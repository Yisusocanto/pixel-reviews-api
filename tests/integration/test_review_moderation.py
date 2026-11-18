import uuid

from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.settings import settings
from src.modules.games.models import Game
from src.modules.users.models import User, UserRole
from tests.conftest import FakeModerationProducer


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
    db_session: AsyncSession, slug: str = "hollow-knight", igdb_id: int = 1001
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


async def test_moderation_verdicts_visibility_appeal_and_admin_flow(
    client: AsyncClient,
    db_session: AsyncSession,
    fake_moderation_producer: FakeModerationProducer,
) -> None:
    author_token, _ = await _register_user(client, "author@example.com", "author_user")
    other_token, _ = await _register_user(client, "other@example.com", "other_user")
    admin_token, admin_id = await _register_user(client, "admin@example.com", "admin_user")

    admin_user = await db_session.get(User, uuid.UUID(admin_id))
    assert admin_user is not None
    admin_user.role = UserRole.ADMIN
    db_session.add(admin_user)
    await db_session.commit()

    game = await _create_game(db_session)
    game_id = str(game.id)
    game_slug = game.slug

    create_res = await client.post(
        "/reviews",
        headers={"Authorization": f"Bearer {author_token}"},
        json={
            "gameId": game_id,
            "score": 5,
            "title": "Juego dificil",
            "content": "Texto sospechoso para probar moderacion",
        },
    )
    assert create_res.status_code == 200
    review_id = create_res.json()["id"]
    assert len(fake_moderation_producer.published) == 1

    bad_key_res = await client.post(
        "/internal/moderation/verdicts",
        headers={"X-Service-Key": "wrong_key"},
        json={
            "id": review_id,
            "type": "review",
            "version": 1,
            "judge": "rules",
            "verdict": "reject",
            "reason": "hate_or_harassment",
            "scores": {"hate_or_harassment": 1.0},
        },
    )
    assert bad_key_res.status_code == 403

    verdict_res = await client.post(
        "/internal/moderation/verdicts",
        headers={"X-Service-Key": settings.MODERATION_SERVICE_KEY},
        json={
            "id": review_id,
            "type": "review",
            "version": 1,
            "judge": "rules",
            "verdict": "reject",
            "reason": "hate_or_harassment",
            "scores": {"hate_or_harassment": 1.0},
        },
    )
    assert verdict_res.status_code == 200
    assert verdict_res.json()["result"] == "applied"

    dup_res = await client.post(
        "/internal/moderation/verdicts",
        headers={"X-Service-Key": settings.MODERATION_SERVICE_KEY},
        json={
            "id": review_id,
            "type": "review",
            "version": 1,
            "judge": "rules",
            "verdict": "reject",
            "reason": "hate_or_harassment",
            "scores": {"hate_or_harassment": 1.0},
        },
    )
    assert dup_res.status_code == 200
    assert dup_res.json()["result"] == "duplicate"

    stale_res = await client.post(
        "/internal/moderation/verdicts",
        headers={"X-Service-Key": settings.MODERATION_SERVICE_KEY},
        json={
            "id": review_id,
            "type": "review",
            "version": 99,
            "judge": "rules",
            "verdict": "approve",
            "scores": {},
        },
    )
    assert stale_res.status_code == 200
    assert stale_res.json()["result"] == "stale"

    public_list = await client.get("/reviews")
    assert public_list.status_code == 200
    assert public_list.json()["total"] == 0

    other_detail = await client.get(
        f"/reviews/{review_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert other_detail.status_code == 404

    stats_res = await client.get(f"/games/{game_slug}/stats")
    assert stats_res.status_code == 200
    assert stats_res.json()["totalReviews"] == 1

    author_detail = await client.get(
        f"/reviews/{review_id}",
        headers={"Authorization": f"Bearer {author_token}"},
    )
    assert author_detail.status_code == 200
    mod_info = author_detail.json()["moderation"]
    assert mod_info["status"] == "rejected"
    assert mod_info["reason"] == "hate_or_harassment"
    assert mod_info["canAppeal"] is True

    other_appeal = await client.post(
        f"/reviews/{review_id}/appeal",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert other_appeal.status_code == 403

    appeal_res = await client.post(
        f"/reviews/{review_id}/appeal",
        headers={"Authorization": f"Bearer {author_token}"},
    )
    assert appeal_res.status_code == 200
    appealed_mod = appeal_res.json()["moderation"]
    assert appealed_mod["status"] == "needs_review"
    assert appealed_mod["canAppeal"] is False

    second_appeal = await client.post(
        f"/reviews/{review_id}/appeal",
        headers={"Authorization": f"Bearer {author_token}"},
    )
    assert second_appeal.status_code == 400

    non_admin_queue = await client.get(
        "/admin/moderation/reviews",
        headers={"Authorization": f"Bearer {author_token}"},
    )
    assert non_admin_queue.status_code == 403

    admin_queue = await client.get(
        "/admin/moderation/reviews?status=needs_review",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_queue.status_code == 200
    queue_data = admin_queue.json()
    assert queue_data["total"] == 1
    item = queue_data["items"][0]
    assert item["id"] == review_id
    assert item["isAppeal"] is True
    assert item["latestModeration"]["judge"] == "user_appeal"

    conflict_res = await client.post(
        f"/admin/moderation/reviews/{review_id}/decision",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "decision": "approve",
            "version": 999,
            "note": "Wrong version",
        },
    )
    assert conflict_res.status_code == 409

    reject_decision = await client.post(
        f"/admin/moderation/reviews/{review_id}/decision",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "decision": "reject",
            "version": 1,
            "reason": "hate_or_harassment",
            "note": "Confirmed violation by admin",
        },
    )
    assert reject_decision.status_code == 200
    assert reject_decision.json()["moderationStatus"] == "rejected"

    author_after_admin_reject = await client.get(
        f"/reviews/{review_id}",
        headers={"Authorization": f"Bearer {author_token}"},
    )
    assert author_after_admin_reject.status_code == 200
    assert author_after_admin_reject.json()["moderation"]["status"] == "rejected"
    assert author_after_admin_reject.json()["moderation"]["canAppeal"] is False

    approve_decision = await client.post(
        f"/admin/moderation/reviews/{review_id}/decision",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "decision": "approve",
            "version": 1,
            "note": "Reconsidered and approved",
        },
    )
    assert approve_decision.status_code == 200
    assert approve_decision.json()["moderationStatus"] == "approved"

    history_res = await client.get(
        f"/admin/moderation/reviews/{review_id}/history",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert history_res.status_code == 200
    history = history_res.json()
    assert len(history) == 4
    assert [h["judge"] for h in history] == ["admin", "admin", "user_appeal", "rules"]
