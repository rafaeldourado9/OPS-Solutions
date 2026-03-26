"""
Script de teste e diagnóstico do WAHA
"""
import asyncio
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

WAHA_URL = os.getenv("WAHA_URL", "http://localhost:3000")
WAHA_API_KEY = os.getenv("WAHA_API_KEY", "adminops")
WAHA_SESSION = os.getenv("WAHA_SESSION", "default")


async def test_waha():
    """Testa conexão com WAHA"""
    
    headers = {
        "X-Api-Key": WAHA_API_KEY,
        "Content-Type": "application/json"
    }
    
    print("=" * 60)
    print("TESTE DE CONEXÃO WAHA")
    print("=" * 60)
    print(f"URL: {WAHA_URL}")
    print(f"API Key: {WAHA_API_KEY}")
    print(f"Session: {WAHA_SESSION}")
    print()
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # 1. Testar health (sem auth)
        print("[1] Testando /api/health (sem autenticação)...")
        try:
            resp = await client.get(f"{WAHA_URL}/api/health")
            print(f"    Status: {resp.status_code}")
            if resp.status_code == 401:
                print("    ⚠️  WAHA exige autenticação para health check")
        except Exception as e:
            print(f"    ❌ Erro: {e}")
        print()
        
        # 2. Testar health (com auth)
        print("[2] Testando /api/health (com autenticação)...")
        try:
            resp = await client.get(f"{WAHA_URL}/api/health", headers=headers)
            print(f"    Status: {resp.status_code}")
            if resp.status_code == 200:
                print("    ✅ WAHA está respondendo corretamente")
        except Exception as e:
            print(f"    ❌ Erro: {e}")
        print()
        
        # 3. Listar sessões
        print("[3] Listando sessões...")
        try:
            resp = await client.get(f"{WAHA_URL}/api/sessions", headers=headers)
            print(f"    Status: {resp.status_code}")
            if resp.status_code == 200:
                sessions = resp.json()
                print(f"    Sessões encontradas: {len(sessions)}")
                for s in sessions:
                    print(f"      - {s.get('name')}: {s.get('status')}")
            else:
                print(f"    Resposta: {resp.text}")
        except Exception as e:
            print(f"    ❌ Erro: {e}")
        print()
        
        # 4. Verificar sessão específica
        print(f"[4] Verificando sessão '{WAHA_SESSION}'...")
        try:
            resp = await client.get(
                f"{WAHA_URL}/api/sessions/{WAHA_SESSION}",
                headers=headers
            )
            print(f"    Status: {resp.status_code}")
            if resp.status_code == 200:
                session = resp.json()
                print(f"    ✅ Sessão encontrada")
                print(f"       Status: {session.get('status')}")
                print(f"       Engine: {session.get('engine')}")
                if session.get('me'):
                    print(f"       Número: {session['me'].get('id')}")
            else:
                print(f"    ⚠️  Sessão não encontrada ou erro")
                print(f"    Resposta: {resp.text}")
        except Exception as e:
            print(f"    ❌ Erro: {e}")
        print()
        
        # 5. Testar envio de mensagem (para você mesmo)
        print("[5] Testando envio de mensagem...")
        try:
            # Primeiro pega o número da sessão
            resp = await client.get(
                f"{WAHA_URL}/api/sessions/{WAHA_SESSION}",
                headers=headers
            )
            if resp.status_code == 200:
                session = resp.json()
                if session.get('me'):
                    my_number = session['me']['id'].split('@')[0]
                    
                    # Tenta enviar mensagem para si mesmo
                    payload = {
                        "chatId": f"{my_number}@c.us",
                        "text": "🤖 Teste de conexão WAHA - Framework WhatsApp Agent",
                        "session": WAHA_SESSION
                    }
                    
                    resp = await client.post(
                        f"{WAHA_URL}/api/sendText",
                        json=payload,
                        headers=headers
                    )
                    print(f"    Status: {resp.status_code}")
                    if resp.status_code == 201:
                        print("    ✅ Mensagem enviada com sucesso!")
                    else:
                        print(f"    ⚠️  Falha ao enviar: {resp.text}")
                else:
                    print("    ⚠️  Sessão não tem número associado (não conectada?)")
            else:
                print("    ⚠️  Não foi possível obter informações da sessão")
        except Exception as e:
            print(f"    ❌ Erro: {e}")
        print()
    
    print("=" * 60)
    print("DIAGNÓSTICO COMPLETO")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_waha())
