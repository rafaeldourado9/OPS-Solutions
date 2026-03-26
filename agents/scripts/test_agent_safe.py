"""Script para testar o agente de forma SEGURA sem enviar mensagens reais."""

import asyncio
import httpx

async def test_agent_safely():
    """Testa o agente sem enviar mensagens reais."""
    
    print("🔒 MODO DE TESTE SEGURO")
    print("=" * 60)
    print("✅ Nenhuma mensagem será enviada de verdade")
    print("✅ Você verá no console o que SERIA enviado")
    print("=" * 60)
    print()
    
    # Simular webhook do WAHA
    webhook_url = "http://localhost:8000/webhook"
    
    test_message = {
        "event": "message",
        "session": "adult_content_session",
        "payload": {
            "id": "test_123",
            "from": "5511999999999@c.us",  # Número de teste
            "body": "Oi",
            "timestamp": 1234567890,
            "hasMedia": False,
        }
    }
    
    print("📨 Enviando mensagem de teste...")
    print(f"De: {test_message['payload']['from']}")
    print(f"Mensagem: {test_message['payload']['body']}")
    print()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(webhook_url, json=test_message)
            
            if response.status_code == 200:
                print("✅ Webhook recebido com sucesso!")
                print()
                print("⏳ Aguarde 3 segundos (debounce)...")
                await asyncio.sleep(4)
                print()
                print("✅ Teste concluído!")
                print()
                print("👀 Verifique o console do servidor para ver o que SERIA enviado")
            else:
                print(f"❌ Erro: {response.status_code}")
                print(response.text)
    
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        print()
        print("Certifique-se de que o servidor está rodando com:")
        print("USE_FAKE_GATEWAY=true AGENT_ID=adult_content uvicorn api.main:app --reload")


if __name__ == "__main__":
    print()
    print("🚀 Iniciando teste seguro do agente...")
    print()
    asyncio.run(test_agent_safely())
