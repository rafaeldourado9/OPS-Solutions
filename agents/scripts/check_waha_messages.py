"""Verifica mensagens enviadas diretamente no WAHA (não depende do banco)."""

import asyncio
import httpx
import os
from datetime import datetime

async def check_waha_sent_messages():
    """Verifica no WAHA quais mensagens foram enviadas."""
    
    waha_url = os.environ.get("WAHA_URL", "http://localhost:3000")
    waha_api_key = os.environ.get("WAHA_API_KEY", "")
    session = os.environ.get("WAHA_SESSION", "adult_content_session")
    
    headers = {}
    if waha_api_key:
        headers["X-Api-Key"] = waha_api_key
    
    print(f"\n{'='*80}")
    print(f"🔍 VERIFICANDO MENSAGENS ENVIADAS NO WAHA")
    print(f"{'='*80}\n")
    print(f"URL: {waha_url}")
    print(f"Sessão: {session}\n")
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Buscar mensagens enviadas (fromMe=true)
            response = await client.get(
                f"{waha_url}/api/messages",
                params={
                    "session": session,
                    "limit": 100,
                },
                headers=headers
            )
            
            if response.status_code != 200:
                print(f"❌ Erro ao buscar mensagens: {response.status_code}")
                print(f"Resposta: {response.text}")
                return
            
            messages = response.json()
            
            if not messages:
                print("✅ Nenhuma mensagem encontrada no WAHA.")
                return
            
            # Filtrar apenas mensagens ENVIADAS pelo bot (fromMe=true)
            sent_messages = [msg for msg in messages if msg.get("fromMe", False)]
            
            if not sent_messages:
                print(f"✅ SEGURO: Das {len(messages)} mensagens no WAHA, NENHUMA foi enviada pelo bot.")
                print(f"   Todas são mensagens RECEBIDAS de usuários.\n")
                return
            
            print(f"⚠️  Encontradas {len(sent_messages)} mensagens ENVIADAS pelo bot:\n")
            
            # Agrupar por destinatário
            recipients = {}
            for msg in sent_messages:
                chat_id = msg.get("chatId", "unknown")
                if chat_id not in recipients:
                    recipients[chat_id] = []
                recipients[chat_id].append(msg)
            
            print(f"📊 Total de destinatários: {len(recipients)}\n")
            
            for chat_id, msgs in recipients.items():
                print(f"📱 Para: {chat_id}")
                print(f"   Mensagens enviadas: {len(msgs)}")
                
                # Mostrar últimas 3 mensagens
                for msg in msgs[:3]:
                    timestamp = msg.get("timestamp", 0)
                    dt = datetime.fromtimestamp(timestamp) if timestamp else "?"
                    body = msg.get("body", "")
                    preview = body[:60] + "..." if len(body) > 60 else body
                    print(f"   [{dt}] {preview}")
                
                print()
            
            # Alerta de segurança
            if len(recipients) > 5:
                print(f"🚨 ALERTA: Bot enviou mensagens para {len(recipients)} pessoas diferentes!")
                print(f"   Isso pode indicar envio em massa.\n")
            else:
                print(f"✅ Apenas {len(recipients)} destinatário(s). Parece normal.\n")
    
    except httpx.ConnectError:
        print(f"❌ Não foi possível conectar ao WAHA em {waha_url}")
        print(f"   Certifique-se de que o WAHA está rodando.\n")
    except Exception as e:
        print(f"❌ Erro: {e}\n")
    
    print(f"{'='*80}\n")

if __name__ == "__main__":
    asyncio.run(check_waha_sent_messages())
