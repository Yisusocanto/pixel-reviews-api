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
    db_session: AsyncSession, slug: str = "celeste", igdb_id: int = 2001
) -> Game:
    game = Game(
        title="Celeste",
        slug=slug,
        igdb_id=igdb_id,
        image_url="https://example.com/celeste.jpg",
        description="Platformer",
    )
    db_session.add(game)
    await db_session.commit()
    await db_session.refresh(game)
    return game


async def test_comment_moderation_verdicts_visibility_appeal_and_admin_flow(
    client: AsyncClient,
    db_session: AsyncSession,
    fake_moderation_producer: FakeModerationProducer,
) -> None:
    review_author_token, _ = await _register_user(client, "rev_author@example.com", "review_author")
    commenter_token, _ = await _register_user(client, "commenter@example.com", "commenter_user")
    other_token, _ = await _register_user(client, "other_c@example.com", "other_viewer")
    admin_token, admin_id = await _register_user(client, "admin_c@example.com", "admin_comment")

    admin_user = await db_session.get(User, uuid.UUID(admin_id))
    assert admin_user is not None
    admin_user.role = UserRole.ADMIN
    db_session.add(admin_user)
    await db_session.commit()

    game = await _create_game(db_session)

    review_res = await client.post(
        "/reviews",
        headers={"Authorization": f"Bearer {review_author_token}"},
        json={
            "gameId": str(game.id),
            "score": 5,
            "title": "Gran juego",
            "content": "Una obra maestra del genero",
        },
    )
    assert review_res.status_code == 200
    review_id = review_res.json()["id"]

    comment_res = await client.post(
        "/comments",
        headers={"Authorization": f"Bearer {commenter_token}"},
        json={
            "reviewId": review_id,
            "content": "Comentario sospechoso para moderacion",
        },
    )
    assert comment_res.status_code == 200
    comment_id = comment_res.json()["id"]
    assert comment_res.json()["moderation"]["status"] == "pending"

    comment_events = [
        (rk, payload)
        for rk, payload in fake_moderation_producer.published
        if rk == "moderation.comment.check"
    ]
    assert len(comment_events) == 1
    assert str(comment_events[0][1].id) == comment_id
    assert comment_events[0][1].version == 1

    bad_key_res = await client.post(
        "/internal/moderation/verdicts",
        headers={"X-Service-Key": "wrong_key"},
        json={
            "id": comment_id,
            "type": "comment",
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
            "id": comment_id,
            "type": "comment",
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
            "id": comment_id,
            "type": "comment",
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
            "id": comment_id,
            "type": "comment",
            "version": 99,
            "judge": "rules",
            "verdict": "approve",
            "scores": {},
        },
    )
    assert stale_res.status_code == 200
    assert stale_res.json()["result"] == "stale"

    # Public and other users cannot see rejected comment, and commentsCount excludes it
    public_comments = await client.get(f"/reviews/{review_id}/comments")
    assert public_comments.status_code == 200
    assert public_comments.json()["total"] == 0

    other_comments = await client.get(
        f"/reviews/{review_id}/comments",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert other_comments.status_code == 200
    assert other_comments.json()["total"] == 0

    review_detail = await client.get(f"/reviews/{review_id}")
    assert review_detail.status_code == 200
    assert review_detail.json()["commentsCount"] == 0

    # Comment author still sees their rejected comment with moderation metadata
    author_comments = await client.get(
        f"/reviews/{review_id}/comments",
        headers={"Authorization": f"Bearer {commenter_token}"},
    )
    assert author_comments.status_code == 200
    assert author_comments.json()["total"] == 1
    author_comment = author_comments.json()["items"][0]
    assert author_comment["id"] == comment_id
    assert author_comment["moderation"]["status"] == "rejected"
    assert author_comment["moderation"]["reason"] == "hate_or_harassment"
    assert author_comment["moderation"]["canAppeal"] is True

    # Non-author cannot appeal
    other_appeal = await client.post(
        f"/comments/{comment_id}/appeal",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert other_appeal.status_code == 403

    # Author appeals
    appeal_res = await client.post(
        f"/comments/{comment_id}/appeal",
        headers={"Authorization": f"Bearer {commenter_token}"},
    )
    assert appeal_res.status_code == 200
    assert appeal_res.json()["moderation"]["status"] == "needs_review"
    assert appeal_res.json()["moderation"]["canAppeal"] is False

    # Second appeal rejected
    second_appeal = await client.post(
        f"/comments/{comment_id}/appeal",
        headers={"Authorization": f"Bearer {commenter_token}"},
    )
    assert second_appeal.status_code == 400

    # Admin queue access control
    non_admin_queue = await client.get(
        "/admin/moderation/comments",
        headers={"Authorization": f"Bearer {commenter_token}"},
    )
    assert non_admin_queue.status_code == 403

    admin_queue = await client.get(
        "/admin/moderation/comments?status=needs_review",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_queue.status_code == 200
    queue_data = admin_queue.json()
    assert queue_data["total"] == 1
    item = queue_data["items"][0]
    assert item["id"] == comment_id
    assert item["isAppeal"] is True
    assert item["latestModeration"]["judge"] == "user_appeal"
    assert item["review"]["id"] == review_id
    assert item["review"]["game"]["slug"] == "celeste"

    # Optimistic concurrency check
    conflict_res = await client.post(
        f"/admin/moderation/comments/{comment_id}/decision",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "decision": "approve",
            "version": 999,
            "note": "Wrong version",
        },
    )
    assert conflict_res.status_code == 409

    # Admin rejects
    reject_decision = await client.post(
        f"/admin/moderation/comments/{comment_id}/decision",
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

    # Author cannot appeal again after admin decision
    author_after_reject = await client.get(
        f"/reviews/{review_id}/comments",
        headers={"Authorization": f"Bearer {commenter_token}"},
    )
    assert author_after_reject.status_code == 200
    assert author_after_reject.json()["items"][0]["moderation"]["canAppeal"] is False

    # Admin approves
    approve_decision = await client.post(
        f"/admin/moderation/comments/{comment_id}/decision",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "decision": "approve",
            "version": 1,
            "note": "Reconsidered and approved",
        },
    )
    assert approve_decision.status_code == 200
    assert approve_decision.json()["moderationStatus"] == "approved"

    # Now public sees the comment and review commentsCount is 1
    public_after_approve = await client.get(f"/reviews/{review_id}/comments")
    assert public_after_approve.status_code == 200
    assert public_after_approve.json()["total"] == 1

    review_detail_after = await client.get(f"/reviews/{review_id}")
    assert review_detail_after.status_code == 200
    assert review_detail_after.json()["commentsCount"] == 1

    # Audit trail
    history_res = await client.get(
        f"/admin/moderation/comments/{comment_id}/history",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert history_res.status_code == 200
    history = history_res.json()
    assert len(history) == 4
    assert [h["judge"] for h in history] == ["admin", "admin", "user_appeal", "rules"]

    # Editing comment increments version and re-enqueues moderation
    edit_res = await client.patch(
        f"/comments/{comment_id}",
        headers={"Authorization": f"Bearer {commenter_token}"},
        json={"content": "Contenido editado y limpio"},
    )
    assert edit_res.status_code == 200
    comment_events_after = [
        (rk, payload)
        for rk, payload in fake_moderation_producer.published
        if rk == "moderation.comment.check"
    ]
    assert len(comment_events_after) == 2
    assert comment_events_after[1][1].version == 2
