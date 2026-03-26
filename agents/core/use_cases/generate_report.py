"""Use case for generating requirements report from conversation."""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from core.domain.message import Message
from core.ports.document_port import DocumentPort
from core.ports.gateway_port import GatewayPort
from core.ports.llm_port import LLMPort
from core.ports.memory_port import MemoryPort

logger = logging.getLogger(__name__)


class GenerateReportUseCase:
    """Generate PDF report from conversation history."""

    def __init__(
        self,
        memory: MemoryPort,
        document: DocumentPort,
        gateway: GatewayPort,
        llm: LLMPort,
        agent_phone: str,
    ):
        self.memory = memory
        self.document = document
        self.gateway = gateway
        self.llm = llm
        self.agent_phone = agent_phone

    async def execute(
        self,
        chat_id: str,
        agent_id: str,
    ) -> Optional[str]:
        """
        Generate requirements report from conversation.

        Args:
            chat_id: Chat ID to generate report for
            agent_id: Agent ID

        Returns:
            Path to generated PDF or None if failed
        """
        try:
            logger.info(f"Generating report for chat_id={chat_id}")

            # 1. Get conversation history
            messages = await self.memory.get_recent_messages(chat_id, limit=200)
            
            if not messages:
                logger.warning(f"No messages found for chat_id={chat_id}")
                return None

            # 2. Extract requirements using LLM
            template_data = await self._extract_requirements(messages, chat_id)

            # 3. Generate PDF
            output_dir = Path("/tmp/reports")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(output_dir / f"requisitos_{chat_id}_{timestamp}.pdf")
            
            pdf_path = await self.document.generate_pdf(template_data, output_path)

            # 4. Send PDF to agent's phone
            await self._send_pdf_to_agent(pdf_path, chat_id)

            logger.info(f"Report generated successfully: {pdf_path}")
            return pdf_path

        except Exception as e:
            logger.exception(f"Failed to generate report: {e}")
            return None

    async def _extract_requirements(self, messages: list[Message], chat_id: str) -> dict:
        """Extract structured requirements from conversation using LLM."""
        
        # Build conversation text
        conversation = []
        audio_transcriptions = []
        image_descriptions = []
        
        for msg in messages:
            role = "Cliente" if msg.role == "user" else "Rafael"
            conversation.append(f"{role}: {msg.content}")
            
            # Track media
            if "[Usuário enviou um áudio]" in msg.content:
                audio_transcriptions.append(msg.content)
            elif "[Usuário enviou uma imagem]" in msg.content:
                image_descriptions.append(msg.content)

        conversation_text = "\n".join(conversation)

        # Prompt for LLM to extract requirements
        extraction_prompt = f"""
Analise a seguinte conversa de levantamento de requisitos e extraia as informações estruturadas.

CONVERSA:
{conversation_text}

Extraia e retorne APENAS as informações no formato abaixo. Se alguma informação não foi mencionada, escreva "Não informado".

FORMATO DE RESPOSTA:

NOME_CLIENTE: [nome do cliente ou empresa]
TELEFONE: {chat_id}
DESCRICAO_PROBLEMA: [descrição do problema que o cliente quer resolver]
DOR_PRINCIPAL: [principal dor ou dificuldade mencionada]
IMPACTO_NEGOCIO: [como o problema impacta o negócio]
SITUACAO_ATUAL: [como funciona hoje]
SISTEMAS_EXISTENTES: [sistemas que já usam]
PROBLEMAS_ATUAIS: [problemas com a situação atual]
FUNCIONALIDADES: [funcionalidades que o sistema deve ter]
USUARIOS: [quem vai usar o sistema]
FLUXOS: [principais fluxos de uso]
USUARIOS_SIMULTANEOS: [quantidade de usuários simultâneos]
TRANSACOES_DIA: [volume de transações por dia]
VOLUME_DADOS: [volume de dados]
CRESCIMENTO: [crescimento esperado]
LATENCIA: [latência aceitável]
DISPONIBILIDADE: [disponibilidade necessária]
REQUISITOS_SEGURANCA: [requisitos de segurança]
PRAZO: [prazo do projeto]
ORCAMENTO: [orçamento disponível]
TECNOLOGIAS_OBRIGATORIAS: [tecnologias que devem ser usadas]
COMPLIANCE: [requisitos de compliance]
ARQUITETURA: [arquitetura recomendada pelo Rafael]
TECNOLOGIAS: [tecnologias sugeridas pelo Rafael]
FASES: [fases de implementação sugeridas]
TEMPO_DESENVOLVIMENTO: [tempo estimado]
CUSTO_ESTIMADO: [custo estimado]
EQUIPE: [equipe necessária]
PROXIMOS_PASSOS: [próximos passos combinados]
OBSERVACOES: [observações adicionais importantes]

Seja objetivo e extraia apenas o que foi realmente discutido na conversa.
"""

        # Call LLM to extract
        messages_llm = [{"role": "user", "content": extraction_prompt}]
        
        extracted_text = ""
        async for chunk in self.llm.stream_response(messages_llm, system="Você é um assistente que extrai informações estruturadas de conversas."):
            extracted_text += chunk

        # Parse extracted text into dict
        template_data = self._parse_extracted_data(extracted_text)
        
        # Add metadata
        template_data["DATA"] = datetime.now().strftime("%d/%m/%Y")
        template_data["DATA_GERACAO"] = datetime.now().strftime("%d/%m/%Y às %H:%M")
        template_data["TELEFONE"] = chat_id
        
        # Add attachments
        if audio_transcriptions:
            template_data["TRANSCRICOES_AUDIO"] = "\n\n".join(audio_transcriptions)
        
        if image_descriptions:
            template_data["IMAGENS_DESCRICOES"] = "\n\n".join(image_descriptions)
        
        template_data["HISTORICO_CONVERSA"] = conversation_text[:5000]  # Limit size

        return template_data

    def _parse_extracted_data(self, text: str) -> dict:
        """Parse LLM extracted text into dictionary."""
        data = {}
        
        lines = text.strip().split("\n")
        current_key = None
        current_value = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line is a key
            if ":" in line and line.split(":")[0].isupper():
                # Save previous key-value
                if current_key:
                    data[current_key] = " ".join(current_value).strip()
                
                # Start new key
                parts = line.split(":", 1)
                current_key = parts[0].strip()
                current_value = [parts[1].strip()] if len(parts) > 1 else []
            else:
                # Continue current value
                if current_key:
                    current_value.append(line)
        
        # Save last key-value
        if current_key:
            data[current_key] = " ".join(current_value).strip()
        
        return data

    async def _send_pdf_to_agent(self, pdf_path: str, chat_id: str):
        """Send generated PDF to agent's phone number."""
        try:
            # Read PDF file
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()

            # Send via WAHA
            # Note: WAHA sendFile endpoint
            import httpx
            
            waha_url = os.environ.get("WAHA_URL", "http://localhost:3000")
            waha_api_key = os.environ.get("WAHA_API_KEY", "")
            session = os.environ.get("WAHA_SESSION", "ops_solutions")
            
            headers = {}
            if waha_api_key:
                headers["X-Api-Key"] = waha_api_key
            
            # Format agent phone
            agent_chat_id = self.agent_phone
            if "@" not in agent_chat_id:
                agent_chat_id = f"{agent_chat_id}@c.us"
            
            files = {
                "file": (f"requisitos_{chat_id}.pdf", pdf_bytes, "application/pdf")
            }
            
            data = {
                "chatId": agent_chat_id,
                "session": session,
                "caption": f"📄 Relatório de Requisitos\n\nCliente: {chat_id}\nData: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{waha_url}/api/sendFile",
                    files=files,
                    data=data,
                    headers=headers
                )
                response.raise_for_status()
            
            logger.info(f"PDF sent to agent phone: {self.agent_phone}")

        except Exception as e:
            logger.exception(f"Failed to send PDF to agent: {e}")
            raise
