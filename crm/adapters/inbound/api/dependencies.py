from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.outbound.persistence.repositories.pg_dashboard_repository import PgDashboardRepository
from core.ports.outbound.dashboard_repository import DashboardRepositoryPort
from core.use_cases.dashboard.get_conversation_metrics import GetConversationMetricsUseCase
from core.use_cases.dashboard.get_inventory_alerts import GetInventoryAlertsUseCase
from core.use_cases.dashboard.get_kpis import GetKPIsUseCase
from core.use_cases.dashboard.get_revenue_chart import GetRevenueChartUseCase
from core.use_cases.dashboard.get_sales_funnel import GetSalesFunnelUseCase

from adapters.outbound.persistence.database import get_session
from adapters.outbound.persistence.repositories.pg_contract_repository import PgContractRepository
from adapters.outbound.persistence.repositories.pg_conversation_repository import PgConversationRepository
from adapters.outbound.persistence.repositories.pg_customer_repository import PgCustomerRepository
from adapters.outbound.persistence.repositories.pg_lead_repository import PgLeadRepository
from adapters.outbound.persistence.repositories.pg_message_repository import PgMessageRepository
from adapters.outbound.persistence.repositories.pg_premise_repository import PgPremiseRepository
from adapters.outbound.persistence.repositories.pg_product_repository import PgProductRepository, PgStockMovementRepository
from adapters.outbound.persistence.repositories.pg_quote_repository import PgQuoteRepository
from adapters.outbound.persistence.repositories.pg_quote_template_repository import PgQuoteTemplateRepository
from adapters.outbound.persistence.repositories.pg_tenant_repository import PgTenantRepository
from adapters.outbound.persistence.repositories.pg_user_repository import PgUserRepository
from core.ports.outbound.agent_config_port import AgentConfigPort
from core.ports.outbound.contract_repository import ContractRepositoryPort
from core.ports.outbound.conversation_repository import ConversationRepositoryPort
from core.ports.outbound.customer_repository import CustomerRepositoryPort
from core.ports.outbound.lead_repository import LeadRepositoryPort
from core.ports.outbound.message_repository import MessageRepositoryPort
from core.ports.outbound.notification_port import NotificationPort
from core.ports.outbound.premise_repository import PremiseRepositoryPort
from core.ports.outbound.product_repository import ProductRepositoryPort
from core.ports.outbound.stock_movement_repository import StockMovementRepositoryPort
from core.ports.outbound.quote_repository import QuoteRepositoryPort
from core.ports.outbound.quote_template_repository import QuoteTemplateRepositoryPort
from core.ports.outbound.rag_document_port import RagDocumentPort
from core.ports.outbound.storage_port import StoragePort
from core.ports.outbound.tenant_repository import TenantRepositoryPort
from core.ports.outbound.user_repository import UserRepositoryPort
from core.use_cases.auth.login import LoginUseCase
from core.use_cases.auth.refresh_token import RefreshTokenUseCase
from core.use_cases.auth.register_tenant import RegisterTenantUseCase
from core.use_cases.conversations.end_takeover import EndTakeoverUseCase
from core.use_cases.conversations.get_conversation_messages import GetConversationMessagesUseCase
from core.use_cases.conversations.handle_gateway_proxy import HandleGatewayProxyUseCase
from core.use_cases.conversations.list_conversations import ListConversationsUseCase
from core.use_cases.conversations.receive_agent_event import ReceiveAgentEventUseCase
from core.use_cases.conversations.send_operator_message import SendOperatorMessageUseCase
from core.use_cases.conversations.start_takeover import StartTakeoverUseCase
from core.use_cases.conversations.store_agent_event_message import StoreAgentEventMessageUseCase
from core.use_cases.customers.create_customer import CreateCustomerUseCase
from core.use_cases.customers.list_customers import ListCustomersUseCase
from core.use_cases.customers.sync_from_agent_event import SyncCustomerFromAgentEventUseCase
from core.use_cases.customers.update_customer import UpdateCustomerUseCase
from core.use_cases.leads.create_lead import CreateLeadUseCase
from core.use_cases.leads.get_lead import GetLeadUseCase
from core.use_cases.leads.list_leads import ListLeadsUseCase
from core.use_cases.leads.move_lead_stage import MoveLeadStageUseCase
from core.use_cases.leads.update_lead import UpdateLeadUseCase
from core.use_cases.agents.delete_rag_document import DeleteRagDocumentUseCase
from core.use_cases.agents.get_agent_config import GetAgentConfigUseCase
from core.use_cases.agents.list_rag_documents import ListRagDocumentsUseCase
from core.use_cases.agents.update_agent_config import UpdateAgentConfigUseCase
from core.use_cases.agents.upload_rag_document import UploadRagDocumentUseCase
from core.use_cases.contracts.create_contract import CreateContractUseCase
from core.use_cases.contracts.list_contracts import ListContractsUseCase
from core.use_cases.contracts.update_contract_status import UpdateContractStatusUseCase
from core.use_cases.inventory.add_stock_movement import AddStockMovementUseCase
from core.use_cases.inventory.create_product import CreateProductUseCase
from core.use_cases.inventory.list_products import ListProductsUseCase
from core.use_cases.inventory.list_stock_movements import ListStockMovementsUseCase
from core.use_cases.inventory.generate_stock_report import GenerateStockReportUseCase
from core.use_cases.inventory.update_product import UpdateProductUseCase
from core.use_cases.premises.create_premise import CreatePremiseUseCase
from core.use_cases.premises.delete_premise import DeletePremiseUseCase
from core.use_cases.premises.list_premises import ListPremisesUseCase
from core.use_cases.premises.update_premise import UpdatePremiseUseCase
from core.use_cases.quotes.create_quote import CreateQuoteUseCase
from core.use_cases.quotes.delete_quote_template import DeleteQuoteTemplateUseCase
from core.use_cases.quotes.generate_quote_document import GenerateQuoteDocumentUseCase
from core.use_cases.quotes.get_quote import GetQuoteUseCase
from core.use_cases.quotes.list_quote_templates import ListQuoteTemplatesUseCase
from core.use_cases.quotes.list_quotes import ListQuotesUseCase
from core.use_cases.quotes.recalculate_quote import RecalculateQuoteUseCase
from core.use_cases.quotes.update_quote_status import UpdateQuoteStatusUseCase
from core.use_cases.quotes.analyze_template_fields import AnalyzeTemplateFieldsUseCase
from core.use_cases.quotes.upload_quote_template import UploadQuoteTemplateUseCase
from core.use_cases.quotes.generate_quotes_report import GenerateQuotesReportUseCase
from core.use_cases.quotes.generate_single_quote_pdf import GenerateSingleQuotePdfUseCase
from core.use_cases.contracts.upload_contract_template import UploadContractTemplateUseCase
from core.use_cases.contracts.list_contract_templates import ListContractTemplatesUseCase
from core.use_cases.contracts.delete_contract_template import DeleteContractTemplateUseCase
from core.use_cases.contracts.generate_contract import GenerateContractUseCase
from adapters.outbound.persistence.repositories.pg_contract_template_repository import PgContractTemplateRepository
from core.ports.outbound.contract_template_repository import ContractTemplateRepositoryPort


# --- Repositories ---

async def get_tenant_repo(
    session: AsyncSession = Depends(get_session),
) -> TenantRepositoryPort:
    return PgTenantRepository(session)


async def get_user_repo(
    session: AsyncSession = Depends(get_session),
) -> UserRepositoryPort:
    return PgUserRepository(session)


async def get_customer_repo(
    session: AsyncSession = Depends(get_session),
) -> CustomerRepositoryPort:
    return PgCustomerRepository(session)


async def get_conversation_repo(
    session: AsyncSession = Depends(get_session),
) -> ConversationRepositoryPort:
    return PgConversationRepository(session)


async def get_message_repo(
    session: AsyncSession = Depends(get_session),
) -> MessageRepositoryPort:
    return PgMessageRepository(session)


async def get_lead_repo(
    session: AsyncSession = Depends(get_session),
) -> LeadRepositoryPort:
    return PgLeadRepository(session)


def get_notification(request: Request) -> NotificationPort:
    return request.app.state.ws_manager


# --- Auth Use Cases ---

def _get_email_adapter():
    from adapters.outbound.email.smtp_adapter import SmtpEmailAdapter
    from infrastructure.config import settings
    if not settings.smtp_user:
        return None
    return SmtpEmailAdapter()


async def get_register_tenant_uc(
    tenant_repo: TenantRepositoryPort = Depends(get_tenant_repo),
    user_repo: UserRepositoryPort = Depends(get_user_repo),
) -> RegisterTenantUseCase:
    return RegisterTenantUseCase(tenant_repo, user_repo, _get_email_adapter())


async def get_login_uc(
    tenant_repo: TenantRepositoryPort = Depends(get_tenant_repo),
    user_repo: UserRepositoryPort = Depends(get_user_repo),
) -> LoginUseCase:
    return LoginUseCase(tenant_repo, user_repo)


async def get_refresh_token_uc(
    user_repo: UserRepositoryPort = Depends(get_user_repo),
) -> RefreshTokenUseCase:
    return RefreshTokenUseCase(user_repo)


# --- Customer Use Cases ---

async def get_create_customer_uc(
    customer_repo: CustomerRepositoryPort = Depends(get_customer_repo),
) -> CreateCustomerUseCase:
    return CreateCustomerUseCase(customer_repo)


async def get_update_customer_uc(
    customer_repo: CustomerRepositoryPort = Depends(get_customer_repo),
) -> UpdateCustomerUseCase:
    return UpdateCustomerUseCase(customer_repo)


async def get_list_customers_uc(
    customer_repo: CustomerRepositoryPort = Depends(get_customer_repo),
) -> ListCustomersUseCase:
    return ListCustomersUseCase(customer_repo)


# --- Lead Use Cases ---

async def get_create_lead_uc(
    lead_repo: LeadRepositoryPort = Depends(get_lead_repo),
) -> CreateLeadUseCase:
    return CreateLeadUseCase(lead_repo)


async def get_update_lead_uc(
    lead_repo: LeadRepositoryPort = Depends(get_lead_repo),
) -> UpdateLeadUseCase:
    return UpdateLeadUseCase(lead_repo)


async def get_list_leads_uc(
    lead_repo: LeadRepositoryPort = Depends(get_lead_repo),
) -> ListLeadsUseCase:
    return ListLeadsUseCase(lead_repo)


async def get_lead_uc(
    lead_repo: LeadRepositoryPort = Depends(get_lead_repo),
) -> GetLeadUseCase:
    return GetLeadUseCase(lead_repo)


async def get_move_lead_stage_uc(
    lead_repo: LeadRepositoryPort = Depends(get_lead_repo),
) -> MoveLeadStageUseCase:
    return MoveLeadStageUseCase(lead_repo, _get_broker())


# --- Conversation Use Cases ---

async def get_list_conversations_uc(
    conversation_repo: ConversationRepositoryPort = Depends(get_conversation_repo),
) -> ListConversationsUseCase:
    return ListConversationsUseCase(conversation_repo)


async def get_conversation_messages_uc(
    conversation_repo: ConversationRepositoryPort = Depends(get_conversation_repo),
    message_repo: MessageRepositoryPort = Depends(get_message_repo),
) -> GetConversationMessagesUseCase:
    return GetConversationMessagesUseCase(conversation_repo, message_repo)


# --- Takeover Use Cases ---

async def get_start_takeover_uc(
    conversation_repo: ConversationRepositoryPort = Depends(get_conversation_repo),
    notification: NotificationPort = Depends(get_notification),
) -> StartTakeoverUseCase:
    return StartTakeoverUseCase(conversation_repo, _get_cache(), notification)


async def get_end_takeover_uc(
    conversation_repo: ConversationRepositoryPort = Depends(get_conversation_repo),
    notification: NotificationPort = Depends(get_notification),
) -> EndTakeoverUseCase:
    return EndTakeoverUseCase(conversation_repo, _get_cache(), notification)


async def get_send_operator_message_uc(
    conversation_repo: ConversationRepositoryPort = Depends(get_conversation_repo),
    message_repo: MessageRepositoryPort = Depends(get_message_repo),
    notification: NotificationPort = Depends(get_notification),
) -> SendOperatorMessageUseCase:
    return SendOperatorMessageUseCase(
        conversation_repo, message_repo, _get_whatsapp_gateway(), notification,
    )


# --- Webhook / Proxy Use Cases ---

def _get_broker():
    from adapters.outbound.messaging.rabbitmq_adapter import RabbitMQAdapter
    return RabbitMQAdapter()


def _get_agent_gateway():
    from adapters.outbound.agents.agent_api_gateway import AgentAPIGateway
    return AgentAPIGateway()


def _get_cache():
    from adapters.outbound.cache.redis_adapter import RedisCacheAdapter
    return RedisCacheAdapter()


def _get_whatsapp_gateway():
    from adapters.outbound.agents.whatsapp_direct_gateway import WhatsAppDirectGateway
    return WhatsAppDirectGateway()


async def get_receive_agent_event_uc(
    customer_repo: CustomerRepositoryPort = Depends(get_customer_repo),
    tenant_repo: TenantRepositoryPort = Depends(get_tenant_repo),
    conversation_repo: ConversationRepositoryPort = Depends(get_conversation_repo),
    message_repo: MessageRepositoryPort = Depends(get_message_repo),
    notification: NotificationPort = Depends(get_notification),
) -> ReceiveAgentEventUseCase:
    sync_uc = SyncCustomerFromAgentEventUseCase(customer_repo, tenant_repo)
    store_message_uc = StoreAgentEventMessageUseCase(
        conversation_repo, message_repo, customer_repo, tenant_repo, notification,
    )
    return ReceiveAgentEventUseCase(sync_uc, store_message_uc)


# --- Premise Use Cases ---

async def get_premise_repo(
    session: AsyncSession = Depends(get_session),
) -> PremiseRepositoryPort:
    return PgPremiseRepository(session)


async def get_quote_repo(
    session: AsyncSession = Depends(get_session),
) -> QuoteRepositoryPort:
    return PgQuoteRepository(session)


async def get_create_premise_uc(
    premise_repo: PremiseRepositoryPort = Depends(get_premise_repo),
) -> CreatePremiseUseCase:
    return CreatePremiseUseCase(premise_repo)


async def get_update_premise_uc(
    premise_repo: PremiseRepositoryPort = Depends(get_premise_repo),
) -> UpdatePremiseUseCase:
    return UpdatePremiseUseCase(premise_repo)


async def get_list_premises_uc(
    premise_repo: PremiseRepositoryPort = Depends(get_premise_repo),
) -> ListPremisesUseCase:
    return ListPremisesUseCase(premise_repo)


async def get_delete_premise_uc(
    premise_repo: PremiseRepositoryPort = Depends(get_premise_repo),
) -> DeletePremiseUseCase:
    return DeletePremiseUseCase(premise_repo)


# --- Quote Use Cases ---

async def get_create_quote_uc(
    quote_repo: QuoteRepositoryPort = Depends(get_quote_repo),
    premise_repo: PremiseRepositoryPort = Depends(get_premise_repo),
) -> CreateQuoteUseCase:
    return CreateQuoteUseCase(quote_repo, premise_repo)


async def get_get_quote_uc(
    quote_repo: QuoteRepositoryPort = Depends(get_quote_repo),
) -> GetQuoteUseCase:
    return GetQuoteUseCase(quote_repo)


async def get_list_quotes_uc(
    quote_repo: QuoteRepositoryPort = Depends(get_quote_repo),
) -> ListQuotesUseCase:
    return ListQuotesUseCase(quote_repo)


async def get_update_quote_status_uc(
    quote_repo: QuoteRepositoryPort = Depends(get_quote_repo),
) -> UpdateQuoteStatusUseCase:
    return UpdateQuoteStatusUseCase(quote_repo, _get_broker())


async def get_recalculate_quote_uc(
    quote_repo: QuoteRepositoryPort = Depends(get_quote_repo),
    premise_repo: PremiseRepositoryPort = Depends(get_premise_repo),
) -> RecalculateQuoteUseCase:
    return RecalculateQuoteUseCase(quote_repo, premise_repo)


# --- Quote Template Use Cases ---

async def get_quote_template_repo(
    session: AsyncSession = Depends(get_session),
) -> QuoteTemplateRepositoryPort:
    return PgQuoteTemplateRepository(session)


def _get_storage() -> StoragePort:
    from adapters.outbound.storage.minio_adapter import MinioStorageAdapter
    return MinioStorageAdapter()


def _get_docx_engine():
    from adapters.outbound.documents.docx_template_engine import DocxTemplateEngine
    return DocxTemplateEngine()


def _get_pdf_exporter():
    from adapters.outbound.documents.pdf_exporter import LibreOfficePdfExporter
    return LibreOfficePdfExporter()


def _get_llm_analyzer():
    from adapters.outbound.llm.gemini_analyzer_adapter import GeminiAnalyzerAdapter
    return GeminiAnalyzerAdapter()


async def get_analyze_template_fields_uc() -> AnalyzeTemplateFieldsUseCase:
    return AnalyzeTemplateFieldsUseCase(_get_docx_engine(), _get_llm_analyzer())


async def get_upload_quote_template_uc(
    template_repo: QuoteTemplateRepositoryPort = Depends(get_quote_template_repo),
) -> UploadQuoteTemplateUseCase:
    return UploadQuoteTemplateUseCase(template_repo, _get_storage(), _get_docx_engine())


async def get_list_quote_templates_uc(
    template_repo: QuoteTemplateRepositoryPort = Depends(get_quote_template_repo),
) -> ListQuoteTemplatesUseCase:
    return ListQuoteTemplatesUseCase(template_repo)


async def get_delete_quote_template_uc(
    template_repo: QuoteTemplateRepositoryPort = Depends(get_quote_template_repo),
) -> DeleteQuoteTemplateUseCase:
    return DeleteQuoteTemplateUseCase(template_repo, _get_storage())


async def get_generate_quote_document_uc(
    quote_repo: QuoteRepositoryPort = Depends(get_quote_repo),
    template_repo: QuoteTemplateRepositoryPort = Depends(get_quote_template_repo),
    customer_repo: CustomerRepositoryPort = Depends(get_customer_repo),
    tenant_repo: TenantRepositoryPort = Depends(get_tenant_repo),
) -> GenerateQuoteDocumentUseCase:
    return GenerateQuoteDocumentUseCase(
        quote_repo=quote_repo,
        template_repo=template_repo,
        storage=_get_storage(),
        docx_engine=_get_docx_engine(),
        pdf_exporter=_get_pdf_exporter(),
        customer_repo=customer_repo,
        tenant_repo=tenant_repo,
    )


async def get_generate_quotes_report_uc(
    tenant_repo: TenantRepositoryPort = Depends(get_tenant_repo),
    quote_repo: QuoteRepositoryPort = Depends(get_quote_repo),
) -> GenerateQuotesReportUseCase:
    return GenerateQuotesReportUseCase(tenant_repo, quote_repo)


async def get_generate_single_quote_pdf_uc(
    tenant_repo: TenantRepositoryPort = Depends(get_tenant_repo),
    quote_repo: QuoteRepositoryPort = Depends(get_quote_repo),
) -> GenerateSingleQuotePdfUseCase:
    return GenerateSingleQuotePdfUseCase(tenant_repo, quote_repo)


# --- Contract Use Cases ---

async def get_contract_repo(
    session: AsyncSession = Depends(get_session),
) -> ContractRepositoryPort:
    return PgContractRepository(session)


async def get_create_contract_uc(
    contract_repo: ContractRepositoryPort = Depends(get_contract_repo),
    quote_repo: QuoteRepositoryPort = Depends(get_quote_repo),
) -> CreateContractUseCase:
    return CreateContractUseCase(contract_repo, quote_repo)


async def get_list_contracts_uc(
    contract_repo: ContractRepositoryPort = Depends(get_contract_repo),
) -> ListContractsUseCase:
    return ListContractsUseCase(contract_repo)


async def get_update_contract_status_uc(
    contract_repo: ContractRepositoryPort = Depends(get_contract_repo),
) -> UpdateContractStatusUseCase:
    return UpdateContractStatusUseCase(contract_repo)


# --- Inventory Use Cases ---

async def get_product_repo(
    session: AsyncSession = Depends(get_session),
) -> ProductRepositoryPort:
    return PgProductRepository(session)


async def get_stock_movement_repo(
    session: AsyncSession = Depends(get_session),
) -> StockMovementRepositoryPort:
    return PgStockMovementRepository(session)


async def get_create_product_uc(
    product_repo: ProductRepositoryPort = Depends(get_product_repo),
) -> CreateProductUseCase:
    return CreateProductUseCase(product_repo)


async def get_update_product_uc(
    product_repo: ProductRepositoryPort = Depends(get_product_repo),
) -> UpdateProductUseCase:
    return UpdateProductUseCase(product_repo)


async def get_list_products_uc(
    product_repo: ProductRepositoryPort = Depends(get_product_repo),
) -> ListProductsUseCase:
    return ListProductsUseCase(product_repo)


async def get_add_stock_movement_uc(
    product_repo: ProductRepositoryPort = Depends(get_product_repo),
    movement_repo: StockMovementRepositoryPort = Depends(get_stock_movement_repo),
) -> AddStockMovementUseCase:
    return AddStockMovementUseCase(product_repo, movement_repo)


async def get_list_stock_movements_uc(
    product_repo: ProductRepositoryPort = Depends(get_product_repo),
    movement_repo: StockMovementRepositoryPort = Depends(get_stock_movement_repo),
) -> ListStockMovementsUseCase:
    return ListStockMovementsUseCase(product_repo, movement_repo)


async def get_generate_stock_report_uc(
    tenant_repo: TenantRepositoryPort = Depends(get_tenant_repo),
    product_repo: ProductRepositoryPort = Depends(get_product_repo),
    movement_repo: StockMovementRepositoryPort = Depends(get_stock_movement_repo),
) -> GenerateStockReportUseCase:
    return GenerateStockReportUseCase(tenant_repo, product_repo, movement_repo)


# --- Agent Config + RAG Use Cases ---

def _get_agent_config_port() -> AgentConfigPort:
    from adapters.outbound.agents.filesystem_agent_config import FilesystemAgentConfigAdapter
    return FilesystemAgentConfigAdapter()


def _get_rag_port() -> RagDocumentPort:
    from adapters.outbound.agents.qdrant_rag_adapter import QdrantRagAdapter
    return QdrantRagAdapter()


async def get_get_agent_config_uc(
    tenant_repo: TenantRepositoryPort = Depends(get_tenant_repo),
) -> GetAgentConfigUseCase:
    return GetAgentConfigUseCase(tenant_repo, _get_agent_config_port())


async def get_update_agent_config_uc(
    tenant_repo: TenantRepositoryPort = Depends(get_tenant_repo),
) -> UpdateAgentConfigUseCase:
    return UpdateAgentConfigUseCase(tenant_repo, _get_agent_config_port())


async def get_list_rag_documents_uc(
    tenant_repo: TenantRepositoryPort = Depends(get_tenant_repo),
) -> ListRagDocumentsUseCase:
    return ListRagDocumentsUseCase(tenant_repo, _get_agent_config_port(), _get_rag_port())


async def get_upload_rag_document_uc(
    tenant_repo: TenantRepositoryPort = Depends(get_tenant_repo),
) -> UploadRagDocumentUseCase:
    return UploadRagDocumentUseCase(tenant_repo, _get_agent_config_port(), _get_rag_port())


async def get_delete_rag_document_uc(
    tenant_repo: TenantRepositoryPort = Depends(get_tenant_repo),
) -> DeleteRagDocumentUseCase:
    return DeleteRagDocumentUseCase(tenant_repo, _get_agent_config_port(), _get_rag_port())


# --- Dashboard Use Cases ---

async def get_dashboard_repo(
    session: AsyncSession = Depends(get_session),
) -> DashboardRepositoryPort:
    return PgDashboardRepository(session)


async def get_kpis_uc(
    repo: DashboardRepositoryPort = Depends(get_dashboard_repo),
) -> GetKPIsUseCase:
    return GetKPIsUseCase(repo)


async def get_sales_funnel_uc(
    repo: DashboardRepositoryPort = Depends(get_dashboard_repo),
) -> GetSalesFunnelUseCase:
    return GetSalesFunnelUseCase(repo)


async def get_revenue_chart_uc(
    repo: DashboardRepositoryPort = Depends(get_dashboard_repo),
) -> GetRevenueChartUseCase:
    return GetRevenueChartUseCase(repo)


async def get_conversation_metrics_uc(
    repo: DashboardRepositoryPort = Depends(get_dashboard_repo),
) -> GetConversationMetricsUseCase:
    return GetConversationMetricsUseCase(repo)


async def get_inventory_alerts_uc(
    repo: DashboardRepositoryPort = Depends(get_dashboard_repo),
) -> GetInventoryAlertsUseCase:
    return GetInventoryAlertsUseCase(repo)


# --- Contract Template Use Cases ---

async def get_contract_template_repo(
    session: AsyncSession = Depends(get_session),
) -> ContractTemplateRepositoryPort:
    return PgContractTemplateRepository(session)


async def get_upload_contract_template_uc(
    template_repo: ContractTemplateRepositoryPort = Depends(get_contract_template_repo),
) -> UploadContractTemplateUseCase:
    return UploadContractTemplateUseCase(template_repo, _get_storage())


async def get_list_contract_templates_uc(
    template_repo: ContractTemplateRepositoryPort = Depends(get_contract_template_repo),
) -> ListContractTemplatesUseCase:
    return ListContractTemplatesUseCase(template_repo)


async def get_delete_contract_template_uc(
    template_repo: ContractTemplateRepositoryPort = Depends(get_contract_template_repo),
) -> DeleteContractTemplateUseCase:
    return DeleteContractTemplateUseCase(template_repo, _get_storage())


async def get_generate_contract_uc(
    template_repo: ContractTemplateRepositoryPort = Depends(get_contract_template_repo),
) -> GenerateContractUseCase:
    return GenerateContractUseCase(template_repo, _get_storage(), _get_docx_engine(), _get_pdf_exporter())


async def get_whatsapp_number_repo(
    session: AsyncSession = Depends(get_session),
) -> PgWhatsAppNumberRepository:
    from adapters.outbound.persistence.repositories.pg_whatsapp_number_repository import PgWhatsAppNumberRepository
    return PgWhatsAppNumberRepository(session)


async def get_handle_gateway_proxy_uc(
    conversation_repo: ConversationRepositoryPort = Depends(get_conversation_repo),
    message_repo: MessageRepositoryPort = Depends(get_message_repo),
    tenant_repo: TenantRepositoryPort = Depends(get_tenant_repo),
    notification: NotificationPort = Depends(get_notification),
    number_repo: PgWhatsAppNumberRepository = Depends(get_whatsapp_number_repo),
) -> HandleGatewayProxyUseCase:
    return HandleGatewayProxyUseCase(
        agent_gateway=_get_agent_gateway(),
        cache=_get_cache(),
        conversation_repo=conversation_repo,
        message_repo=message_repo,
        tenant_repo=tenant_repo,
        notification=notification,
        number_repo=number_repo,
    )
