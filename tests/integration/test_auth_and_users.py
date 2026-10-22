from urllib.parse import parse_qs, urlparse

from httpx import AsyncClient

from tests.conftest import FakeMailerService


async def test_health_check(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_register_login_and_me_flow(client: AsyncClient) -> None:
    register_res = await client.post(
        "/auth/register",
        json={
            "email": "player1@example.com",
            "username": "player_one",
            "password": "Password123",
            "bio": "RPG lover",
        },
    )
    assert register_res.status_code == 201
    register_data = register_res.json()
    assert "access_token" in register_data
    assert "refresh_token" in register_data
    assert register_data["user"]["username"] == "player_one"

    duplicate_res = await client.post(
        "/auth/register",
        json={
            "email": "player1@example.com",
            "username": "another_name",
            "password": "Password123",
        },
    )
    assert duplicate_res.status_code == 409

    login_res = await client.post(
        "/auth/login",
        json={
            "email": "player1@example.com",
            "password": "Password123",
        },
    )
    assert login_res.status_code == 200
    access_token = login_res.json()["access_token"]

    me_res = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "player1@example.com"


async def test_forgot_and_reset_password_flow(
    client: AsyncClient,
    fake_mailer: FakeMailerService,
) -> None:
    await client.post(
        "/auth/register",
        json={
            "email": "resetme@example.com",
            "username": "reset_user",
            "password": "OldPassword123",
        },
    )

    forgot_res = await client.post(
        "/users/forgot-password",
        json={"email": "resetme@example.com"},
    )
    assert forgot_res.status_code == 200
    assert len(fake_mailer.sent_emails) == 1

    reset_url = fake_mailer.sent_emails[0]["reset_url"]
    parsed_url = urlparse(reset_url)
    token = parse_qs(parsed_url.query)["token"][0]

    reset_res = await client.post(
        "/users/reset-password",
        json={
            "token": token,
            "new_password": "NewPassword456",
        },
    )
    assert reset_res.status_code == 200

    old_login_res = await client.post(
        "/auth/login",
        json={
            "email": "resetme@example.com",
            "password": "OldPassword123",
        },
    )
    assert old_login_res.status_code == 401

    new_login_res = await client.post(
        "/auth/login",
        json={
            "email": "resetme@example.com",
            "password": "NewPassword456",
        },
    )
    assert new_login_res.status_code == 200
