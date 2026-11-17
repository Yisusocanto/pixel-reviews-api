import logging

from aio_pika import ExchangeType, connect_robust
from aio_pika.abc import AbstractChannel, AbstractRobustConnection
from aio_pika.pool import Pool

logger = logging.getLogger("broker")


class Broker:
    def __init__(self, amqp_url: str, max_connections: int = 10) -> None:
        self.amqp_url = amqp_url
        self.connections_pool: Pool[AbstractRobustConnection] = Pool(
            self._get_connection, max_size=2
        )
        self.channel_pool: Pool[AbstractChannel] = Pool(self._get_channel, max_size=max_connections)

    async def _get_connection(self) -> AbstractRobustConnection:
        return await connect_robust(
            self.amqp_url,
            heartbeat=10,
            client_properties={"connection_name": "broker-client"},
        )

    async def _get_channel(self) -> AbstractChannel:
        async with self.connections_pool.acquire() as connection:
            return await connection.channel(publisher_confirms=True)

    async def setup_topology(self) -> None:
        async with self.channel_pool.acquire() as channel:
            dlx = await channel.declare_exchange(
                "moderation.dlx", ExchangeType.DIRECT, durable=True
            )
            dlq = await channel.declare_queue("moderation.dlq", durable=True)
            await dlq.bind(dlx, routing_key="moderation.failed")

            main_exchange = await channel.declare_exchange(
                "moderation", ExchangeType.TOPIC, durable=True
            )
            moderation_queue = await channel.declare_queue(
                "moderation.review.check",
                durable=True,
                arguments={
                    "x-dead-letter-exchange": "moderation.dlx",
                    "x-dead-letter-routing-key": "moderation.failed",
                    "x-queue-type": "quorum",
                    "x-delivery-limit": 3,
                },
            )
            await moderation_queue.bind(main_exchange, routing_key="moderation.*.check")
            logger.info("[BROKER] RabbitMQ moderation topology initialized")

    async def close(self) -> None:
        await self.channel_pool.close()
        await self.connections_pool.close()
        logger.info("[BROKER] RabbitMQ connection pools closed")
