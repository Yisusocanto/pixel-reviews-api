import logging

from aio_pika import DeliveryMode, Message
from aio_pika.exceptions import AMQPError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.services.broker.client import Broker
from src.services.moderation_producer.schemas import ModerationPayload

logger = logging.getLogger("moderation_producer")


class ModerationProducer:
    def __init__(
        self,
        broker: Broker | None = None,
        exchange_name: str = "moderation",
    ) -> None:
        self.broker = broker
        self.exchange_name = exchange_name

    async def publish(self, routing_key: str, payload: ModerationPayload) -> bool:
        if self.broker is None:
            logger.warning(
                "[MODERATION] Broker is not configured; skipping publish for %s %s (v%s)",
                payload.type,
                payload.id,
                payload.version,
            )
            return False

        try:
            await self._publish_with_retry(routing_key, payload)
            logger.info(
                "[MODERATION] Published %s %s (v%s) to exchange '%s' with key '%s'",
                payload.type,
                payload.id,
                payload.version,
                self.exchange_name,
                routing_key,
            )
            return True
        except (AMQPError, OSError, TimeoutError) as exc:
            logger.error(
                "[MODERATION] Failed to publish %s %s (v%s): %s",
                payload.type,
                payload.id,
                payload.version,
                exc,
            )
            return False

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=5),
        retry=retry_if_exception_type(AMQPError),
        reraise=True,
    )
    async def _publish_with_retry(self, routing_key: str, payload: ModerationPayload):
        assert self.broker is not None
        body_bytes = payload.model_dump_json().encode("utf-8")
        message = Message(
            body=body_bytes,
            content_type="application/json",
            content_encoding="utf-8",
            delivery_mode=DeliveryMode.PERSISTENT,
            message_id=str(payload.id),
            correlation_id=str(payload.id),
            headers={
                "x-event-version": payload.version,
                "x-event-type": payload.__class__.__name__,
            },
        )

        async with self.broker.channel_pool.acquire() as channel:
            exchange = await channel.get_exchange(self.exchange_name)
            return await exchange.publish(
                message, routing_key=routing_key, mandatory=True, timeout=5
            )
