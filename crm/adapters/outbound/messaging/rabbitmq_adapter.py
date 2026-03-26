import json
import asyncio
import structlog
from typing import Optional

import aio_pika
from aio_pika import ExchangeType, Message, DeliveryMode
from aio_pika.abc import AbstractRobustConnection, AbstractChannel, AbstractExchange

from core.ports.outbound.message_broker_port import CRMEvent, MessageBrokerPort
from infrastructure.config import settings

logger = structlog.get_logger()

EXCHANGE_NAME = "crm.events"


class RabbitMQAdapter(MessageBrokerPort):
    """
    Topic exchange adapter for CRM domain events.

    Routing key  = event_type  (e.g. "crm.lead.stage_changed")
    Exchange     = crm.events  (topic, durable)
    Persistence  = delivery_mode=PERSISTENT (survives broker restart)

    Uses aio-pika RobustConnection — reconnects automatically on failure.
    Connection is lazy: opened on first publish.
    """

    def __init__(self, url: Optional[str] = None) -> None:
        self._url = url or settings.rabbitmq_url
        self._connection: Optional[AbstractRobustConnection] = None
        self._channel: Optional[AbstractChannel] = None
        self._exchange: Optional[AbstractExchange] = None
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def publish(self, event: CRMEvent) -> None:
        try:
            exchange = await self._get_exchange()
            body = json.dumps({
                "event_type": event.event_type,
                "tenant_id": event.tenant_id,
                "occurred_at": event.occurred_at,
                "payload": event.payload,
            }).encode()

            message = Message(
                body=body,
                content_type="application/json",
                delivery_mode=DeliveryMode.PERSISTENT,
                headers={"tenant_id": event.tenant_id},
            )

            await exchange.publish(message, routing_key=event.routing_key())
            logger.debug(
                "event_published",
                event_type=event.event_type,
                tenant_id=event.tenant_id,
            )
        except Exception as exc:
            # Broker unavailable — log and continue (non-blocking)
            logger.warning(
                "event_publish_failed",
                event_type=event.event_type,
                error=str(exc),
            )

    async def close(self) -> None:
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
        self._connection = None
        self._channel = None
        self._exchange = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _get_exchange(self) -> AbstractExchange:
        async with self._lock:
            if self._exchange is None or (
                self._channel is not None and self._channel.is_closed
            ):
                await self._connect()
        return self._exchange  # type: ignore[return-value]

    async def _connect(self) -> None:
        self._connection = await aio_pika.connect_robust(self._url)
        self._channel = await self._connection.channel()
        self._exchange = await self._channel.declare_exchange(
            EXCHANGE_NAME,
            ExchangeType.TOPIC,
            durable=True,
        )
        logger.info("rabbitmq_connected", exchange=EXCHANGE_NAME)
