from typing import Any, Optional
from uuid import UUID

import pytest

from core.domain.conversation import CRMMessage, Conversation
from core.domain.customer import Customer
from core.domain.lead import Lead, LeadStage
from core.domain.contract import Contract
from core.domain.premise import Premise
from core.domain.product import Product, StockMovement
from core.domain.quote import Quote
from core.domain.quote_template import QuoteTemplate
from core.domain.tenant import Tenant
from core.domain.user import Role, User
from core.ports.outbound.agent_gateway import AgentGatewayPort
from core.ports.outbound.cache_port import CachePort
from core.ports.outbound.whatsapp_gateway import WhatsAppGatewayPort
from core.ports.outbound.conversation_repository import ConversationRepositoryPort
from core.ports.outbound.customer_repository import CustomerRepositoryPort
from core.ports.outbound.lead_repository import LeadRepositoryPort
from core.ports.outbound.message_repository import MessageRepositoryPort
from core.ports.outbound.notification_port import NotificationPort
from core.domain.rag_document import RagDocument
from core.ports.outbound.agent_config_port import AgentConfigPort
from core.ports.outbound.contract_repository import ContractRepositoryPort
from core.ports.outbound.docx_template_engine_port import DocxTemplateEnginePort
from core.ports.outbound.pdf_exporter_port import PdfExporterPort
from core.ports.outbound.premise_repository import PremiseRepositoryPort
from core.ports.outbound.quote_repository import QuoteRepositoryPort
from core.ports.outbound.product_repository import ProductRepositoryPort
from core.ports.outbound.rag_document_port import RagDocumentPort
from core.ports.outbound.quote_template_repository import QuoteTemplateRepositoryPort
from core.ports.outbound.stock_movement_repository import StockMovementRepositoryPort
from core.ports.outbound.storage_port import StoragePort
from core.ports.outbound.tenant_repository import TenantRepositoryPort
from core.ports.outbound.user_repository import UserRepositoryPort
from infrastructure.security import hash_password


# --- In-memory fake repositories for unit tests ---

class FakeTenantRepository(TenantRepositoryPort):
    def __init__(self):
        self._store: dict[UUID, Tenant] = {}

    async def save(self, tenant: Tenant) -> None:
        self._store[tenant.id] = tenant

    async def get_by_id(self, tenant_id: UUID) -> Optional[Tenant]:
        return self._store.get(tenant_id)

    async def get_by_slug(self, slug: str) -> Optional[Tenant]:
        return next((t for t in self._store.values() if t.slug == slug), None)

    async def get_by_agent_id(self, agent_id: str) -> Optional[Tenant]:
        return next((t for t in self._store.values() if t.agent_id == agent_id), None)

    async def get_by_gateway_session(self, gateway_session: str) -> Optional[Tenant]:
        return next((t for t in self._store.values() if t.gateway_session == gateway_session), None)

    async def exists_by_slug(self, slug: str) -> bool:
        return any(t.slug == slug for t in self._store.values())


class FakeUserRepository(UserRepositoryPort):
    def __init__(self):
        self._store: dict[UUID, User] = {}

    async def save(self, user: User) -> None:
        self._store[user.id] = user

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        return self._store.get(user_id)

    async def get_by_email(self, tenant_id: UUID, email: str) -> Optional[User]:
        return next(
            (u for u in self._store.values() if u.tenant_id == tenant_id and u.email == email),
            None,
        )

    async def list_by_tenant(self, tenant_id: UUID) -> list[User]:
        return [u for u in self._store.values() if u.tenant_id == tenant_id]


class FakeCustomerRepository(CustomerRepositoryPort):
    def __init__(self):
        self._store: dict[UUID, Customer] = {}

    async def save(self, customer: Customer) -> None:
        self._store[customer.id] = customer

    async def update(self, customer: Customer) -> None:
        self._store[customer.id] = customer

    async def get_by_id(self, tenant_id: UUID, customer_id: UUID) -> Optional[Customer]:
        c = self._store.get(customer_id)
        return c if c and c.tenant_id == tenant_id else None

    async def get_by_phone(self, tenant_id: UUID, phone: str) -> Optional[Customer]:
        return next(
            (c for c in self._store.values() if c.tenant_id == tenant_id and c.phone == phone),
            None,
        )

    async def get_by_chat_id(self, tenant_id: UUID, chat_id: str) -> Optional[Customer]:
        return next(
            (c for c in self._store.values() if c.tenant_id == tenant_id and c.chat_id == chat_id),
            None,
        )

    async def list_by_tenant(
        self, tenant_id: UUID, offset: int = 0, limit: int = 50, search: Optional[str] = None
    ) -> tuple[list[Customer], int]:
        items = [c for c in self._store.values() if c.tenant_id == tenant_id and c.is_active]
        if search:
            s = search.lower()
            items = [c for c in items if s in c.name.lower() or s in c.phone]
        total = len(items)
        return items[offset : offset + limit], total

    async def delete(self, tenant_id: UUID, customer_id: UUID) -> bool:
        c = self._store.get(customer_id)
        if c and c.tenant_id == tenant_id:
            c.is_active = False
            return True
        return False


class FakeCachePort(CachePort):
    def __init__(self):
        self._store: dict[str, str] = {}

    async def get(self, key: str) -> Optional[str]:
        return self._store.get(key)

    async def set(self, key: str, value: str, ttl_seconds: int = 0) -> None:
        self._store[key] = value

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def exists(self, key: str) -> bool:
        return key in self._store


class FakeConversationRepository(ConversationRepositoryPort):
    def __init__(self):
        self._store: dict[UUID, Conversation] = {}

    async def save(self, conversation: Conversation) -> None:
        self._store[conversation.id] = conversation

    async def update(self, conversation: Conversation) -> None:
        self._store[conversation.id] = conversation

    async def get_by_chat_id(self, tenant_id: UUID, chat_id: str) -> Optional[Conversation]:
        return next(
            (c for c in self._store.values() if c.tenant_id == tenant_id and c.chat_id == chat_id),
            None,
        )

    async def get_by_id(self, tenant_id: UUID, conversation_id: UUID) -> Optional[Conversation]:
        c = self._store.get(conversation_id)
        return c if c and c.tenant_id == tenant_id else None

    async def list_by_tenant(
        self, tenant_id: UUID, status: Optional[str] = None, offset: int = 0, limit: int = 50
    ) -> tuple[list[Conversation], int]:
        items = [c for c in self._store.values() if c.tenant_id == tenant_id]
        if status:
            items = [c for c in items if c.status == status]
        items.sort(key=lambda c: c.last_message_at or c.created_at, reverse=True)
        total = len(items)
        return items[offset : offset + limit], total


class FakeMessageRepository(MessageRepositoryPort):
    def __init__(self):
        self._store: list[CRMMessage] = []

    async def save(self, message: CRMMessage) -> None:
        self._store.append(message)

    async def list_by_conversation(
        self, tenant_id: UUID, conversation_id: UUID, offset: int = 0, limit: int = 100
    ) -> tuple[list[CRMMessage], int]:
        items = [
            m for m in self._store
            if m.tenant_id == tenant_id and m.conversation_id == conversation_id
        ]
        items.sort(key=lambda m: m.created_at)
        total = len(items)
        return items[offset : offset + limit], total


class FakeNotificationPort(NotificationPort):
    def __init__(self):
        self.events: list[tuple[UUID, str, dict]] = []

    async def push_to_tenant(self, tenant_id: UUID, event_type: str, data: dict[str, Any]) -> None:
        self.events.append((tenant_id, event_type, data))


class FakeLeadRepository(LeadRepositoryPort):
    def __init__(self):
        self._store: dict[UUID, Lead] = {}

    async def save(self, lead: Lead) -> None:
        self._store[lead.id] = lead

    async def update(self, lead: Lead) -> None:
        self._store[lead.id] = lead

    async def get_by_id(self, tenant_id: UUID, lead_id: UUID) -> Optional[Lead]:
        lead = self._store.get(lead_id)
        return lead if lead and lead.tenant_id == tenant_id else None

    async def list_by_tenant(
        self,
        tenant_id: UUID,
        stage: Optional[str] = None,
        assigned_to: Optional[UUID] = None,
        search: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Lead], int]:
        items = [l for l in self._store.values() if l.tenant_id == tenant_id]
        if stage:
            items = [l for l in items if (l.stage.value if isinstance(l.stage, LeadStage) else l.stage) == stage]
        if assigned_to:
            items = [l for l in items if l.assigned_to == assigned_to]
        if search:
            s = search.lower()
            items = [l for l in items if s in l.title.lower()]
        items.sort(key=lambda l: l.updated_at, reverse=True)
        total = len(items)
        return items[offset : offset + limit], total

    async def delete(self, tenant_id: UUID, lead_id: UUID) -> bool:
        lead = self._store.get(lead_id)
        if lead and lead.tenant_id == tenant_id:
            del self._store[lead_id]
            return True
        return False


class FakePremiseRepository(PremiseRepositoryPort):
    def __init__(self):
        self._store: dict[UUID, Premise] = {}

    async def save(self, premise: Premise) -> None:
        self._store[premise.id] = premise

    async def update(self, premise: Premise) -> None:
        self._store[premise.id] = premise

    async def get_by_id(self, tenant_id: UUID, premise_id: UUID) -> Optional[Premise]:
        p = self._store.get(premise_id)
        return p if p and p.tenant_id == tenant_id else None

    async def list_by_tenant(
        self, tenant_id: UUID, active_only: bool = True
    ) -> list[Premise]:
        items = [p for p in self._store.values() if p.tenant_id == tenant_id]
        if active_only:
            items = [p for p in items if p.is_active]
        return sorted(items, key=lambda p: p.name)

    async def delete(self, tenant_id: UUID, premise_id: UUID) -> bool:
        p = self._store.get(premise_id)
        if p and p.tenant_id == tenant_id:
            del self._store[premise_id]
            return True
        return False


class FakeQuoteRepository(QuoteRepositoryPort):
    def __init__(self):
        self._store: dict[UUID, Quote] = {}

    async def save(self, quote: Quote) -> None:
        self._store[quote.id] = quote

    async def update(self, quote: Quote) -> None:
        self._store[quote.id] = quote

    async def get_by_id(self, tenant_id: UUID, quote_id: UUID) -> Optional[Quote]:
        q = self._store.get(quote_id)
        return q if q and q.tenant_id == tenant_id else None

    async def list_by_tenant(
        self,
        tenant_id: UUID,
        status: Optional[str] = None,
        customer_id: Optional[UUID] = None,
        lead_id: Optional[UUID] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Quote], int]:
        from core.domain.quote import QuoteStatus
        items = [q for q in self._store.values() if q.tenant_id == tenant_id]
        if status:
            items = [q for q in items if (q.status.value if isinstance(q.status, QuoteStatus) else q.status) == status]
        if customer_id:
            items = [q for q in items if q.customer_id == customer_id]
        if lead_id:
            items = [q for q in items if q.lead_id == lead_id]
        items.sort(key=lambda q: q.updated_at, reverse=True)
        total = len(items)
        return items[offset : offset + limit], total

    async def delete(self, tenant_id: UUID, quote_id: UUID) -> bool:
        q = self._store.get(quote_id)
        if q and q.tenant_id == tenant_id:
            del self._store[quote_id]
            return True
        return False


class FakeAgentConfigPort(AgentConfigPort):
    def __init__(self, initial: dict[str, dict] | None = None):
        self._store: dict[str, dict] = initial or {}

    def exists(self, agent_id: str) -> bool:
        return agent_id in self._store

    def read(self, agent_id: str) -> dict:
        if agent_id not in self._store:
            raise FileNotFoundError(f"business.yml not found for agent '{agent_id}'")
        return dict(self._store[agent_id])

    def write(self, agent_id: str, config: dict) -> None:
        self._store[agent_id] = dict(config)


class FakeRagDocumentPort(RagDocumentPort):
    def __init__(self):
        # collection -> list of (name, chunks)
        self._store: dict[str, list[tuple[str, list[str]]]] = {}

    async def list_documents(self, collection: str) -> list[RagDocument]:
        from collections import Counter
        items = self._store.get(collection, [])
        counts: Counter = Counter(name for name, _ in items)
        return [
            RagDocument(name=name, collection=collection, chunk_count=count)
            for name, count in sorted(counts.items())
        ]

    async def ingest_document(self, collection: str, name: str, text_chunks: list[str]) -> int:
        if collection not in self._store:
            self._store[collection] = []
        self._store[collection].append((name, text_chunks))
        return len(text_chunks)

    async def delete_document(self, collection: str, name: str) -> int:
        items = self._store.get(collection, [])
        original = len(items)
        self._store[collection] = [(n, c) for n, c in items if n != name]
        deleted = original - len(self._store[collection])
        return deleted


class FakeContractRepository(ContractRepositoryPort):
    def __init__(self):
        self._store: dict[UUID, Contract] = {}

    async def save(self, contract: Contract) -> None:
        self._store[contract.id] = contract

    async def update(self, contract: Contract) -> None:
        self._store[contract.id] = contract

    async def get_by_id(self, tenant_id: UUID, contract_id: UUID) -> Optional[Contract]:
        c = self._store.get(contract_id)
        return c if c and c.tenant_id == tenant_id else None

    async def get_by_quote_id(self, tenant_id: UUID, quote_id: UUID) -> Optional[Contract]:
        return next(
            (c for c in self._store.values() if c.tenant_id == tenant_id and c.quote_id == quote_id),
            None,
        )

    async def list_by_tenant(
        self, tenant_id: UUID, status: Optional[str] = None, offset: int = 0, limit: int = 50
    ) -> tuple[list[Contract], int]:
        from core.domain.contract import ContractStatus
        items = [c for c in self._store.values() if c.tenant_id == tenant_id]
        if status:
            items = [c for c in items if (c.status.value if isinstance(c.status, ContractStatus) else c.status) == status]
        items.sort(key=lambda c: c.updated_at, reverse=True)
        total = len(items)
        return items[offset:offset + limit], total


class FakeProductRepository(ProductRepositoryPort):
    def __init__(self):
        self._store: dict[UUID, Product] = {}

    async def save(self, product: Product) -> None:
        self._store[product.id] = product

    async def update(self, product: Product) -> None:
        self._store[product.id] = product

    async def get_by_id(self, tenant_id: UUID, product_id: UUID) -> Optional[Product]:
        p = self._store.get(product_id)
        return p if p and p.tenant_id == tenant_id else None

    async def get_by_sku(self, tenant_id: UUID, sku: str) -> Optional[Product]:
        return next(
            (p for p in self._store.values() if p.tenant_id == tenant_id and p.sku == sku),
            None,
        )

    async def list_by_tenant(
        self, tenant_id: UUID, search: Optional[str] = None,
        active_only: bool = True, low_stock_only: bool = False,
        offset: int = 0, limit: int = 50,
    ) -> tuple[list[Product], int]:
        items = [p for p in self._store.values() if p.tenant_id == tenant_id]
        if active_only:
            items = [p for p in items if p.is_active]
        if search:
            s = search.lower()
            items = [p for p in items if s in p.name.lower() or s in p.sku.lower()]
        if low_stock_only:
            items = [p for p in items if p.is_low_stock]
        items.sort(key=lambda p: p.name)
        total = len(items)
        return items[offset:offset + limit], total


class FakeStockMovementRepository(StockMovementRepositoryPort):
    def __init__(self):
        self._store: list[StockMovement] = []

    async def save(self, movement: StockMovement) -> None:
        self._store.append(movement)

    async def list_by_product(
        self, tenant_id: UUID, product_id: UUID, offset: int = 0, limit: int = 50
    ) -> tuple[list[StockMovement], int]:
        items = [
            m for m in self._store
            if m.tenant_id == tenant_id and m.product_id == product_id
        ]
        items.sort(key=lambda m: m.created_at, reverse=True)
        total = len(items)
        return items[offset:offset + limit], total


class FakeQuoteTemplateRepository(QuoteTemplateRepositoryPort):
    def __init__(self):
        self._store: dict[UUID, QuoteTemplate] = {}

    async def save(self, template: QuoteTemplate) -> None:
        self._store[template.id] = template

    async def get_by_id(self, tenant_id: UUID, template_id: UUID) -> Optional[QuoteTemplate]:
        t = self._store.get(template_id)
        return t if t and t.tenant_id == tenant_id else None

    async def list_by_tenant(self, tenant_id: UUID) -> list[QuoteTemplate]:
        return sorted(
            [t for t in self._store.values() if t.tenant_id == tenant_id],
            key=lambda t: t.name,
        )

    async def delete(self, tenant_id: UUID, template_id: UUID) -> bool:
        t = self._store.get(template_id)
        if t and t.tenant_id == tenant_id:
            del self._store[template_id]
            return True
        return False


class FakeStoragePort(StoragePort):
    def __init__(self):
        self._store: dict[str, bytes] = {}

    async def upload(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> None:
        self._store[key] = data

    async def download(self, key: str) -> bytes:
        if key not in self._store:
            raise FileNotFoundError(f"Key not found: {key}")
        return self._store[key]

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def get_url(self, key: str, expires_in: int = 3600) -> str:
        return f"http://fake-storage/{key}"


class FakeDocxTemplateEngine(DocxTemplateEnginePort):
    """Returns fixed placeholders and does simple string replacement."""

    def extract_placeholders(self, docx_bytes: bytes) -> list[str]:
        # Extract placeholders from raw bytes (text content)
        import re
        text = docx_bytes.decode("utf-8", errors="ignore")
        found = set(re.findall(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}", text))
        return sorted(found)

    def fill_template(self, docx_bytes: bytes, context: dict[str, str]) -> bytes:
        text = docx_bytes.decode("utf-8", errors="ignore")
        for key, value in context.items():
            text = text.replace(f"{{{key}}}", value)
        return text.encode("utf-8")


class FakePdfExporter(PdfExporterPort):
    async def convert(self, docx_bytes: bytes) -> bytes:
        return b"%PDF-1.4 fake-pdf-content"


class FakeWhatsAppGateway(WhatsAppGatewayPort):
    def __init__(self):
        self.sent_messages: list[tuple[str, str, str]] = []
        self.sent_documents: list[tuple] = []

    async def send_message(self, session: str, chat_id: str, text: str) -> None:
        self.sent_messages.append((session, chat_id, text))

    async def send_typing(self, session: str, chat_id: str, active: bool) -> None:
        pass

    async def send_document(
        self, session: str, chat_id: str, doc_data: bytes, filename: str, caption: str = ""
    ) -> None:
        self.sent_documents.append((session, chat_id, filename, caption))

    async def send_seen(self, session: str, chat_id: str) -> None:
        pass


class FakeAgentGateway(AgentGatewayPort):
    def __init__(self):
        self.forwarded_payloads: list[dict] = []

    async def get_health(self) -> dict:
        return {"status": "ok"}

    async def forward_webhook(self, payload: dict) -> None:
        self.forwarded_payloads.append(payload)


@pytest.fixture
def tenant_repo():
    return FakeTenantRepository()


@pytest.fixture
def customer_repo():
    return FakeCustomerRepository()


@pytest.fixture
def cache():
    return FakeCachePort()


@pytest.fixture
def agent_gateway():
    return FakeAgentGateway()


@pytest.fixture
def user_repo():
    return FakeUserRepository()


@pytest.fixture
def sample_tenant() -> Tenant:
    return Tenant.create(
        slug="acme",
        name="Acme Corp",
        agent_id="acme_agent",
    )


@pytest.fixture
def sample_user(sample_tenant) -> User:
    return User.create(
        tenant_id=sample_tenant.id,
        email="admin@acme.com",
        password_hash=hash_password("Senha123!"),
        name="Admin Acme",
        role=Role.ADMIN,
    )


@pytest.fixture
def conversation_repo():
    return FakeConversationRepository()


@pytest.fixture
def message_repo():
    return FakeMessageRepository()


@pytest.fixture
def notification():
    return FakeNotificationPort()


@pytest.fixture
def lead_repo():
    return FakeLeadRepository()


@pytest.fixture
def whatsapp_gateway():
    return FakeWhatsAppGateway()


@pytest.fixture
def premise_repo():
    return FakePremiseRepository()


@pytest.fixture
def quote_repo():
    return FakeQuoteRepository()


@pytest.fixture
def agent_config_port(sample_tenant):
    return FakeAgentConfigPort({
        sample_tenant.agent_id: {
            "agent": {"name": "Test Agent", "company": "Test Co", "language": "pt-BR", "persona": ""},
            "llm": {"provider": "gemini", "model": "gemini-flash", "fallback_provider": "ollama", "fallback_model": "llama3.1:8b", "temperature": 0.3, "max_tokens": 400},
            "memory": {"qdrant_collection": f"{sample_tenant.agent_id}_chats", "qdrant_rag_collection": f"{sample_tenant.agent_id}_rules"},
        }
    })


@pytest.fixture
def rag_port():
    return FakeRagDocumentPort()


@pytest.fixture
def contract_repo():
    return FakeContractRepository()


@pytest.fixture
def product_repo():
    return FakeProductRepository()


@pytest.fixture
def stock_movement_repo():
    return FakeStockMovementRepository()


@pytest.fixture
def quote_template_repo():
    return FakeQuoteTemplateRepository()


@pytest.fixture
def storage():
    return FakeStoragePort()


@pytest.fixture
def docx_engine():
    return FakeDocxTemplateEngine()


@pytest.fixture
def pdf_exporter():
    return FakePdfExporter()
