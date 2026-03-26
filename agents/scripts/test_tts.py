"""
Script de teste para validar TTS com gemidos
"""
import asyncio
from adapters.outbound.media.tts_adapter import TTSAdapter


async def test_tts():
    print("🎤 Testando TTS com gemidos...")
    
    tts = TTSAdapter()
    
    text = "Oi amor, tudo bem com você? Estava com saudades... 🔥"
    
    print(f"📝 Texto: {text}")
    print("⏳ Gerando áudio...")
    
    audio_bytes = await tts.synthesize(text, add_moans=True)
    
    print(f"✅ Áudio gerado: {len(audio_bytes)} bytes")
    
    # Salva para testar
    with open("test_output.ogg", "wb") as f:
        f.write(audio_bytes)
    
    print("💾 Salvo em test_output.ogg")
    print("🎧 Teste o áudio!")


if __name__ == "__main__":
    asyncio.run(test_tts())
