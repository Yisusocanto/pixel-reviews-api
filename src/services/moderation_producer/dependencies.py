from typing import Annotated

from fastapi import Depends, Request

from src.services.moderation_producer.client import ModerationProducer


def get_producer_service(request: Request) -> ModerationProducer:
    broker = getattr(request.app.state, "broker", None)
    return ModerationProducer(broker=broker, exchange_name="moderation")


ModerationProducerDep = Annotated[ModerationProducer, Depends(get_producer_service)]
