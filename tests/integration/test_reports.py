import uuid

from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from src.modules.comments.models import Comment
from src.modules.games.models import Game
from src.modules.reviews.models import Review
from src.modules.users.models import User, UserRole
from src.schemas.moderation import ModerationStatus


async def _register_user(client: AsyncClient, email: str, username: str) -> tuple[str, str]:
    res = await client.post(
        "/auth/register",
        json={
            "email": email,
            "username": username,
            "password": "Password123",
        },
    )
    assert res.status_code == 201
    data = res.json()
    return data["access_token"], data["user"]["id"]


async def _create_game(
    db_session: AsyncSession, slug: str = "hollow-knight", igdb_id: int = 3001
) -> Game:
    game = Game(
        title="Hollow Knight",
        slug=slug,
        igdb_id=igdb_id,
        image_url="https://example.com/hk.jpg",
        description="Metroidvania",
    )
    db_session.add(game)
    await db_session.commit()
    await db_session.refresh(game)
    return game


async def test_report_review_and_admin_verdict_flow(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    author_token, _ = await _register_user(client, "author_rep@example.com", "author_rep")
    reporter1_token, reporter1_id = await _register_user(
        client, "reporter1@example.com", "reporter_one"
    )
    reporter2_token, _ = await _register_user(client, "reporter2@example.com", "reporter_two")
    admin_token, admin_id = await _register_user(client, "admin_rep@example.com", "admin_rep")

    admin_user = await db_session.get(User, uuid.UUID(admin_id))
    assert admin_user is not None
    admin_user.role = UserRole.ADMIN
    db_session.add(admin_user)
    await db_session.commit()

    game = await _create_game(db_session)

    review_res = await client.post(
        "/reviews",
        headers={"Authorization": f"Bearer {author_token}"},
        json={
            "gameId": str(game.id),
            "score": 4,
            "title": "Spoiler review",
            "content": "Ends up being the final boss",
        },
    )
    assert review_res.status_code == 200
    review_id = review_res.json()["id"]

    self_report = await client.post(
        "/reports",
        headers={"Authorization": f"Bearer {author_token}"},
        json={
            "targetId": review_id,
            "targetType": "review",
            "type": "spoiler",
            "reason": "Self report",
        },
    )
    assert self_report.status_code == 400

    first_report = await client.post(
        "/reports",
        headers={"Authorization": f"Bearer {reporter1_token}"},
        json={
            "targetId": review_id,
            "targetType": "review",
            "type": "spoiler",
            "reason": "Contains ending spoilers",
        },
    )
    assert first_report.status_code == 201
    report_data = first_report.json()
    assert report_data["status"] == "open"
    assert report_data["reporterId"] == reporter1_id
    assert report_data["targetType"] == "review"
    report_id = report_data["id"]

    review_in_db = await db_session.get(Review, uuid.UUID(review_id))
    assert review_in_db is not None
    assert review_in_db.moderation_status == ModerationStatus.NEEDS_REVIEW

    duplicate_report = await client.post(
        "/reports",
        headers={"Authorization": f"Bearer {reporter1_token}"},
        json={
            "targetId": review_id,
            "targetType": "review",
            "type": "spam",
        },
    )
    assert duplicate_report.status_code == 409

    second_report = await client.post(
        "/reports",
        headers={"Authorization": f"Bearer {reporter2_token}"},
        json={
            "targetId": review_id,
            "targetType": "review",
            "type": "spoiler",
            "reason": "Huge spoiler",
        },
    )
    assert second_report.status_code == 201

    forbidden_queue = await client.get(
        "/admin/moderation/reports",
        headers={"Authorization": f"Bearer {reporter1_token}"},
    )
    assert forbidden_queue.status_code == 403

    queue_res = await client.get(
        "/admin/moderation/reports",
        headers={"Authorization": f"Bearer {admin_token}"},
        params={"status": "open", "targetType": "review"},
    )
    assert queue_res.status_code == 200
    queue_data = queue_res.json()
    assert queue_data["total"] == 2
    assert len(queue_data["items"]) == 2
    assert queue_data["items"][0]["openReportsCount"] == 2
    assert queue_data["items"][0]["target"]["id"] == review_id
    assert queue_data["items"][0]["target"]["gameSlug"] == "hollow-knight"

    invalid_verdict = await client.post(
        f"/admin/moderation/reports/{report_id}/verdict",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "open"},
    )
    assert invalid_verdict.status_code == 400

    resolve_res = await client.post(
        f"/admin/moderation/reports/{report_id}/verdict",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "resolved"},
    )
    assert resolve_res.status_code == 200
    assert resolve_res.json()["status"] == "resolved"
    assert resolve_res.json()["target"]["moderationStatus"] == "rejected"

    await db_session.refresh(review_in_db)
    assert review_in_db.moderation_status == ModerationStatus.REJECTED

    open_after = await client.get(
        "/admin/moderation/reports",
        headers={"Authorization": f"Bearer {admin_token}"},
        params={"status": "open"},
    )
    assert open_after.status_code == 200
    assert open_after.json()["total"] == 0

    already_closed = await client.post(
        f"/admin/moderation/reports/{report_id}/verdict",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "dismissed"},
    )
    assert already_closed.status_code == 409


async def test_report_comment_and_dismiss_flow(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    review_author_token, _ = await _register_user(client, "rev_c_rep@example.com", "rev_c_rep")
    commenter_token, _ = await _register_user(client, "comm_rep@example.com", "comm_rep")
    reporter_token, _ = await _register_user(client, "rep_comm@example.com", "rep_comm")
    admin_token, admin_id = await _register_user(client, "admin_comm_r@example.com", "admin_comm_r")

    admin_user = await db_session.get(User, uuid.UUID(admin_id))
    assert admin_user is not None
    admin_user.role = UserRole.ADMIN
    db_session.add(admin_user)
    await db_session.commit()

    game = await _create_game(db_session, slug="hades", igdb_id=3002)

    review_res = await client.post(
        "/reviews",
        headers={"Authorization": f"Bearer {review_author_token}"},
        json={
            "gameId": str(game.id),
            "score": 5,
            "title": "Amazing roguelike",
            "content": "Loved every run",
        },
    )
    assert review_res.status_code == 200
    review_id = review_res.json()["id"]

    comment_res = await client.post(
        "/comments",
        headers={"Authorization": f"Bearer {commenter_token}"},
        json={
            "reviewId": review_id,
            "content": "Totally agree with this review!",
        },
    )
    assert comment_res.status_code == 200
    comment_id = comment_res.json()["id"]

    report_res = await client.post(
        "/reports",
        headers={"Authorization": f"Bearer {reporter_token}"},
        json={
            "targetId": comment_id,
            "targetType": "comment",
            "type": "harassment",
            "reason": "False alarm",
        },
    )
    assert report_res.status_code == 201
    report_id = report_res.json()["id"]

    comment_in_db = await db_session.get(Comment, uuid.UUID(comment_id))
    assert comment_in_db is not None
    assert comment_in_db.moderation_status == ModerationStatus.NEEDS_REVIEW

    dismiss_res = await client.post(
        f"/admin/moderation/reports/{report_id}/verdict",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "dismissed"},
    )
    assert dismiss_res.status_code == 200
    assert dismiss_res.json()["status"] == "dismissed"
    assert dismiss_res.json()["target"]["moderationStatus"] == "approved"
    assert dismiss_res.json()["target"]["reviewId"] == review_id

    await db_session.refresh(comment_in_db)
    assert comment_in_db.moderation_status == ModerationStatus.APPROVED
