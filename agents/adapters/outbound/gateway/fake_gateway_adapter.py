"""
FakeGatewayAdapter — Mock gateway para testes (não envia mensagens reais)
"""
import logging
from core.ports.gateway_port import GatewayPort

logger = logging.getLogger(__name__)


class FakeGatewayAdapter(GatewayPort):
    """Gateway fake que apenas loga as mensagens sem enviar"""
    
    async def send_message(self, chat_id: str, text: str) -> None:
        logger.info(f"[FAKE] Enviaria texto para {chat_id}: {text[:50]}...")
    
    async def send_audio(self, chat_id: str, audio_bytes: bytes) -> None:
        logger.info(f"[FAKE] Enviaria áudio para {chat_id} ({len(audio_bytes)} bytes)")
    
    async def send_image(self, chat_id: str, image_data: bytes, filename: str = "image.jpg", caption: str = "") -> None:
        logger.info(f"[FAKE] Enviaria imagem para {chat_id}: {filename} ({len(image_data)} bytes)")

    async def send_video(self, chat_id: str, video_data: bytes, filename: str = "video.mp4", caption: str = "") -> None:
        logger.info(f"[FAKE] Enviaria vídeo para {chat_id}: {filename} ({len(video_data)} bytes)")

    async def send_document(self, chat_id: str, doc_data: bytes, filename: str = "document", caption: str = "") -> None:
        logger.info(f"[FAKE] Enviaria documento para {chat_id}: {filename} ({len(doc_data)} bytes)")

    async def send_voice(self, chat_id: str, audio_data: bytes) -> None:
        logger.info(f"[FAKE] Enviaria voice para {chat_id} ({len(audio_data)} bytes)")

    async def send_recording(self, chat_id: str, active: bool) -> None:
        logger.debug(f"[FAKE] Recording {active} para {chat_id}")

    async def send_seen(self, chat_id: str) -> None:
        logger.debug(f"[FAKE] Seen para {chat_id}")

    async def send_typing(self, chat_id: str, active: bool) -> None:
        logger.debug(f"[FAKE] Typing {active} para {chat_id}")
