import asyncio
import logging
from datetime import UTC, datetime, timedelta

from sqlmodel import col, or_, select

from src.db.database import async_session_maker
from src.modules.comments.models import Comment
from src.modules.reviews.models import Review
from src.services.broker.client import Broker
from src.services.moderation_producer.client import ModerationProducer
from src.services.moderation_producer.schemas import ModerationPayload, ModerationType

logger = logging.getLogger("sweeper")


async def sweep_stale_reviews(
    broker: Broker,
    stale_minutes: int = 10,
    batch_size: int = 50,
    exchange_name: str = "moderation",
    routing_key: str = "moderation.review.check",
) -> int:
    cutoff = datetime.now(UTC) - timedelta(minutes=stale_minutes)
    producer = ModerationProducer(broker=broker, exchange_name=exchange_name)

    async with async_session_maker() as session:
        stmt = (
            select(Review)
            .where(
                Review.moderated_version < Review.content_version,
                or_(col(Review.title).is_not(None), col(Review.content).is_not(None)),
                or_(
                    col(Review.moderation_enqueued_at).is_(None),
                    Review.moderation_enqueued_at < cutoff,
                ),
            )
            .order_by(col(Review.created_at).asc())
            .limit(batch_size)
            .with_for_update(skip_locked=True)
        )
        result = await session.exec(stmt)
        reviews = result.all()

        if not reviews:
            return 0

        logger.info("[SWEEPER] Found %d stale reviews needing moderation", len(reviews))
        enqueued_count = 0

        for review in reviews:
            payload = ModerationPayload(
                id=review.id,
                version=review.content_version,
                type=ModerationType.REVIEW,
                title=review.title,
                content=review.content,
            )

            success = await producer.publish(routing_key=routing_key, payload=payload)
            if success:
                review.moderation_enqueued_at = datetime.now(UTC)
                session.add(review)
                enqueued_count += 1
                logger.info(
                    "[SWEEPER] Re-enqueued review %s (v%s)", review.id, review.content_version
                )

        await session.commit()
        return enqueued_count


async def sweep_stale_comments(
    broker: Broker,
    stale_minutes: int = 10,
    batch_size: int = 50,
    exchange_name: str = "moderation",
    routing_key: str = "moderation.comment.check",
) -> int:
    cutoff = datetime.now(UTC) - timedelta(minutes=stale_minutes)
    producer = ModerationProducer(broker=broker, exchange_name=exchange_name)

    async with async_session_maker() as session:
        stmt = (
            select(Comment)
            .where(
                Comment.moderated_version < Comment.content_version,
                or_(
                    col(Comment.moderation_enqueued_at).is_(None),
                    Comment.moderation_enqueued_at < cutoff,
                ),
            )
            .order_by(col(Comment.created_at).asc())
            .limit(batch_size)
            .with_for_update(skip_locked=True)
        )
        result = await session.exec(stmt)
        comments = result.all()

        if not comments:
            return 0

        logger.info("[SWEEPER] Found %d stale comments needing moderation", len(comments))
        enqueued_count = 0

        for comment in comments:
            payload = ModerationPayload(
                id=comment.id,
                version=comment.content_version,
                type=ModerationType.COMMENT,
                content=comment.content,
            )

            success = await producer.publish(routing_key=routing_key, payload=payload)
            if success:
                comment.moderation_enqueued_at = datetime.now(UTC)
                session.add(comment)
                enqueued_count += 1
                logger.info(
                    "[SWEEPER] Re-enqueued comment %s (v%s)", comment.id, comment.content_version
                )

        await session.commit()
        return enqueued_count


async def run_sweeper_loop(
    broker: Broker,
    stale_minutes: int = 10,
    interval_seconds: int = 600,
    batch_size: int = 50,
    exchange_name: str = "moderation",
    review_routing_key: str = "moderation.review.check",
    comment_routing_key: str = "moderation.comment.check",
) -> None:
    logger.info(
        "[SWEEPER] Starting sweeper loop (interval=%ds, stale_minutes=%dm, batch_size=%d)",
        interval_seconds,
        stale_minutes,
        batch_size,
    )
    while True:
        try:
            await sweep_stale_reviews(
                broker=broker,
                stale_minutes=stale_minutes,
                batch_size=batch_size,
                exchange_name=exchange_name,
                routing_key=review_routing_key,
            )
            await sweep_stale_comments(
                broker=broker,
                stale_minutes=stale_minutes,
                batch_size=batch_size,
                exchange_name=exchange_name,
                routing_key=comment_routing_key,
            )
        except asyncio.CancelledError:
            logger.info("[SWEEPER] Sweeper task cancelled; shutting down loop cleanly")
            break
        except Exception as exc:  # noqa: BLE001
            logger.error("[SWEEPER] Error in sweeper run: %s", exc)

        await asyncio.sleep(interval_seconds)
