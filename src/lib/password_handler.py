import asyncio

import bcrypt


def _hash_password(plain_password: str):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain_password.encode(), salt).decode()


def _check_password(plain_password: str, hashed_password: str):
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


async def hash_password(plain_password: str) -> str:
    return await asyncio.to_thread(_hash_password, plain_password)


async def check_password(plain_password: str, hashed_password: str) -> bool:
    return await asyncio.to_thread(_check_password, plain_password, hashed_password)
