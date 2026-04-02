import structlog

from core.domain.customer import Customer
from core.domain.events import InboundAgentEvent
from core.domain.lead import Lead
from core.ports.outbound.customer_repository import CustomerRepositoryPort
from core.ports.outbound.lead_repository import LeadRepositoryPort
from core.ports.outbound.tenant_repository import TenantRepositoryPort

logger = structlog.get_logger()


class SyncCustomerFromAgentEventUseCase:
    """Auto-create a customer (and lead) when a new_contact event arrives from agents."""

    def __init__(
        self,
        customer_repo: CustomerRepositoryPort,
        tenant_repo: TenantRepositoryPort,
        lead_repo: LeadRepositoryPort | None = None,
    ) -> None:
        self._customer_repo = customer_repo
        self._tenant_repo = tenant_repo
        self._lead_repo = lead_repo

    async def execute(self, event: InboundAgentEvent) -> Customer | None:
        if event.event_type != "new_contact":
            return None

        tenant = await self._tenant_repo.get_by_agent_id(event.agent_id)
        if not tenant:
            tenant = await self._tenant_repo.get_by_owned_agent_id(event.agent_id)
        if not tenant:
            logger.warning("tenant_not_found_for_agent", agent_id=event.agent_id)
            return None

        # Extract phone from chat_id (e.g., "5511999999999@c.us" -> "5511999999999")
        phone = event.chat_id.split("@")[0] if "@" in event.chat_id else event.chat_id

        existing = await self._customer_repo.get_by_phone(tenant.id, phone)
        if existing:
            logger.debug("customer_already_exists", phone=phone)
            return existing

        name = event.data.get("name") or event.data.get("pushName") or event.data.get("push_name") or phone
        customer = Customer.create(
            tenant_id=tenant.id,
            name=name,
            phone=phone,
            source="whatsapp_auto",
            chat_id=event.chat_id,
        )
        await self._customer_repo.save(customer)

        logger.info(
            "customer_auto_created",
            customer_id=str(customer.id),
            phone=phone,
            agent_id=event.agent_id,
        )

        # Auto-create a lead for this new contact
        if self._lead_repo:
            lead = Lead.create(
                tenant_id=tenant.id,
                title=name,
                customer_id=customer.id,
                source="whatsapp_auto",
            )
            await self._lead_repo.save(lead)
            logger.info("lead_auto_created", lead_id=str(lead.id), customer_id=str(customer.id))

        return customer
