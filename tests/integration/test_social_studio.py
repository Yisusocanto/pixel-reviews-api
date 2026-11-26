import uuid

from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from src.modules.games.models import Game
from src.modules.users.models import User, UserRole


async def _register(client: AsyncClient, email: str, username: str) -> tuple[str, str]:
    res = await client.post(
        "/auth/register",
        json={"email": email, "username": username, "password": "Password123"},
    )
    assert res.status_code == 201
    payload = res.json()
    return payload["access_token"], payload["user"]["id"]


async def test_social_studio_admin_candidates_generate_and_tts(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user_token, _ = await _register(client, "player_soc@example.com", "player_soc")
    admin_token, admin_id = await _register(client, "admin_soc@example.com", "admin_soc")

    admin_user = await db_session.get(User, uuid.UUID(admin_id))
    assert admin_user is not None
    admin_user.role = UserRole.ADMIN
    db_session.add(admin_user)

    game = Game(
        title="Cyberpunk 2077",
        slug="cyberpunk-2077",
        igdb_id=1877,
        image_url="https://images.igdb.com/igdb/image/upload/t_thumb/co4hk8.webp",
        background_image="https://images.igdb.com/igdb/image/upload/t_720p/sc8abc.webp",
        screenshots=["https://images.igdb.com/igdb/image/upload/t_720p/sc8abc.webp"],
        critic_score=86,
        description="Open-world action RPG in Night City.",
    )
    db_session.add(game)
    await db_session.commit()
    await db_session.refresh(game)

    review_res = await client.post(
        "/reviews",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "gameId": str(game.id),
            "score": 5,
            "title": "Redemption arc completed",
            "content": "Night City feels alive after 2.0 and Phantom Liberty.",
        },
    )
    assert review_res.status_code == 200

    forbidden = await client.get(
        "/admin/social/candidates",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert forbidden.status_code == 403

    candidates_res = await client.get(
        "/admin/social/candidates?angle=critic_vs_players",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert candidates_res.status_code == 200
    candidates_body = candidates_res.json()
    assert len(candidates_body["items"]) == 1
    assert candidates_body["items"][0]["gameSlug"] == "cyberpunk-2077"
    assert candidates_body["items"][0]["coverUrl"].endswith(".jpg")

    pack_res = await client.post(
        "/admin/social/generate",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "angle": "critic_vs_players",
            "language": "es",
            "gameSlug": "cyberpunk-2077",
        },
    )
    assert pack_res.status_code == 200
    pack = pack_res.json()
    assert pack["hookHeadline"]
    assert len(pack["slides"]) == 2
    assert pack["slides"][0]["imageUrl"].endswith(".jpg")
    assert len(pack["videoScenes"]) == 1

    tts_res = await client.post(
        "/admin/social/tts",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "narration": pack["fullNarration"],
            "voiceDirection": pack["voiceDirection"],
            "voiceName": "Orus",
        },
    )
    assert tts_res.status_code == 200
    tts_body = tts_res.json()
    assert tts_body["audioDataUrl"].startswith("data:audio/wav;base64,")
    assert tts_body["durationSeconds"] == 1.0
