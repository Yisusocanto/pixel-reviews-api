import hashlib
import logging
import re
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from src.core.settings import settings
from src.lib.password_handler import check_password, hash_password
from src.modules.password_reset_tokens.models import PasswordResetTokenCreate
from src.modules.password_reset_tokens.service import PasswordResetTokenService
from src.modules.reviews.service import ReviewService
from src.modules.users.models import User, UserCreate, UserUpdate
from src.modules.users.repository import UserRepository
from src.modules.users.schemas import UserPagination
from src.modules.wishlists.schemas import WishlistPagination
from src.modules.wishlists.service import WishlistService
from src.services.mailer.client import MailerService
from src.services.storage.client import StorageError, StorageService

logger = logging.getLogger("user_service")

PHOTO_EXTENSIONS = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
MAX_PROFILE_PHOTO_BYTES = 3 * 1024 * 1024
IMMUTABLE_CACHE_CONTROL = "public, max-age=31536000, immutable"


class UserService:
    def __init__(
        self,
        repo: UserRepository,
        review_service: ReviewService,
        wishlist_service: WishlistService,
        password_reset_token_service: PasswordResetTokenService,
        storage: StorageService,
        mailer: MailerService,
    ) -> None:
        self.repo = repo
        self.review_service = review_service
        self.wishlist_service = wishlist_service
        self.password_reset_token_service = password_reset_token_service
        self.storage = storage
        self.mailer = mailer

    async def create(self, data: UserCreate) -> User:
        existing_username = await self.repo.get_by_username(data.username)
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with that username already exists.",
            )

        existing_email = await self.repo.get_by_email(data.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with that email already exists.",
            )

        hashed_password = await hash_password(data.password)
        new_user = User(
            email=data.email,
            username=data.username,
            bio=data.bio,
            hashed_password=hashed_password,
        )

        return await self.repo.create(new_user)

    async def create_from_google(self, email: str, google_id: str, name: str | None = None) -> User:
        base_username = ""
        if name:
            base_username = re.sub(r"[^a-zA-Z0-9_]", "_", name.strip().lower())
        if not base_username:
            email_prefix = email.split("@")[0]
            base_username = re.sub(r"[^a-zA-Z0-9_]", "_", email_prefix.lower())

        base_username = base_username[:20].strip("_") or "user"
        username = base_username

        while await self.repo.get_by_username(username):
            suffix = secrets.token_hex(2)
            username = f"{base_username[:15]}_{suffix}"

        new_user = User(
            email=email,
            username=username,
            google_id=google_id,
            hashed_password=None,
        )

        return await self.repo.create(new_user)

    async def update(self, data: UserUpdate, user_id: uuid.UUID) -> User:
        user = await self.repo.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if data.username:
            already_in_use = await self.repo.get_by_username(data.username)
            if already_in_use:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Username already in use. choose another",
                )

        updated_user = await self.repo.update(user, data)
        return updated_user

    async def update_password(self, user: User, old_password: str, new_password: str) -> User:
        if not await check_password(old_password, user.hashed_password or ""):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Old password incorrect"
            )

        if len(new_password) < 4 or len(new_password) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Too short or too long password (4 - 50 characters)",
            )

        new_hashed_password = await hash_password(new_password)
        updated_user = await self.repo.update_password(user, new_hashed_password)
        return updated_user

    async def get_all(self, page: int, limit: int) -> UserPagination:
        offset = (page - 1) * limit

        users = await self.repo.get_all(offset=offset, limit=limit)
        total = await self.repo.count_all()
        total_pages = (total - 1 + limit) // limit if total > 0 else 0

        return UserPagination(items=users, page=page, total=total, total_pages=total_pages)

    async def get_user(self, username: str) -> User:
        user = await self.repo.get_by_username(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )
        return user

    async def get_user_reviews(
        self, page: int, limit: int, username: str, current_user_id: uuid.UUID | None = None
    ):
        user = await self.get_user(username)
        return await self.review_service.get_all(
            page, limit, user_id=user.id, current_user_id=current_user_id
        )

    async def user_wishlist(self, page: int, limit: int, username: str) -> WishlistPagination:
        user = await self.get_user(username)
        wishlist = await self.wishlist_service.get_all(page, limit, user.id)
        return wishlist

    async def update_profile_photo(
        self, user: User, content: bytes, content_type: str | None
    ) -> User:
        extension = PHOTO_EXTENSIONS.get(content_type or "")
        if extension is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File type not supported.",
            )

        if not content or len(content) > MAX_PROFILE_PHOTO_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty or exceeds the size limit.",
            )

        old_key = user.profile_photo_key
        new_key = f"profile/{uuid.uuid4()}{extension}"

        try:
            await self.storage.upload(
                new_key, content, content_type, cache_control=IMMUTABLE_CACHE_CONTROL
            )
        except StorageError:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to upload profile photo.",
            )

        try:
            updated_user = await self.repo.set_profile_photo_key(user, new_key)
        except SQLAlchemyError:
            logger.exception("[USERS] DB update failed for user %s, removing %s", user.id, new_key)
            await self._delete_photo_quietly(new_key)
            raise

        if old_key:
            await self._delete_photo_quietly(old_key)

        logger.info("[USERS] User %s changed profile photo to %s", user.id, new_key)
        return updated_user

    async def forgot_password(self, email: str, bg_tasks: BackgroundTasks):
        response = {"message": "Check your inbox to reset your password."}

        user = await self.repo.get_by_email(email)
        if not user:
            return response

        await self.password_reset_token_service.delete_all(user.id)

        token = secrets.token_urlsafe(16)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        expires_at = datetime.now(UTC) + timedelta(minutes=15)

        base_url = settings.FRONTEND_URL + "/reset-password"
        query_params = urlencode({"token": token})
        reset_url = base_url + "?" + query_params

        await self.password_reset_token_service.create(
            PasswordResetTokenCreate(user_id=user.id, token_hash=token_hash, expires_at=expires_at)
        )

        bg_tasks.add_task(
            self.mailer.send_forgot_password_email,
            email=user.email,
            username=user.username,
            reset_url=reset_url,
        )

        return response

    async def reset_password(self, token: str, new_password: str):
        exception = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="The link is invalid or has expired"
        )

        hashed_token = hashlib.sha256(token.encode()).hexdigest()

        db_token = await self.password_reset_token_service.get_one(hashed_token)
        if not db_token:
            raise exception

        if datetime.now(UTC) > db_token.expires_at:
            raise exception

        user = await self.repo.get_user(db_token.user_id)
        if not user:
            raise exception

        hashed_new_password = await hash_password(new_password)
        await self.repo.update_password(user=user, new_password=hashed_new_password)
        await self.password_reset_token_service.delete_all(user.id)

        return {"message": "Password successfully reset"}

    async def _delete_photo_quietly(self, key: str) -> None:
        try:
            await self.storage.delete(key)
        except StorageError:
            logger.warning("[USERS] Orphan file left in storage: %s", key)
