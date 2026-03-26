"""
Script para reconectar sessão WAHA
"""
import asyncio
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

WAHA_URL = os.getenv("WAHA_URL", "http://localhost:3000")
WAHA_API_KEY = os.getenv("WAHA_API_KEY", "adminops")
WAHA_SESSION = os.getenv("WAHA_SESSION", "default")


async def restart_waha_session():
    """Reinicia a sessão WAHA"""
    
    headers = {
        "X-Api-Key": WAHA_API_KEY,
        "Content-Type": "application/json"
    }
    
    print("=" * 60)
    print("REINICIANDO SESSÃO WAHA")
    print("=" * 60)
    print(f"Sessão: {WAHA_SESSION}")
    print()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # 1. Verificar status atual
        print("[1] Verificando status atual...")
        try:
            resp = await client.get(
                f"{WAHA_URL}/api/sessions/{WAHA_SESSION}",
                headers=headers
            )
            if resp.status_code == 200:
                session = resp.json()
                print(f"    Status atual: {session.get('status')}")
                print()
        except Exception as e:
            print(f"    ❌ Erro: {e}")
            return
        
        # 2. Parar a sessão
        print("[2] Parando sessão...")
        try:
            resp = await client.post(
                f"{WAHA_URL}/api/sessions/{WAHA_SESSION}/stop",
                headers=headers
            )
            print(f"    Status: {resp.status_code}")
            if resp.status_code in [200, 201]:
                print("    ✅ Sessão parada")
            await asyncio.sleep(2)
        except Exception as e:
            print(f"    ⚠️  Erro ao parar (pode já estar parada): {e}")
        print()
        
        # 3. Iniciar a sessão
        print("[3] Iniciando sessão...")
        try:
            resp = await client.post(
                f"{WAHA_URL}/api/sessions/{WAHA_SESSION}/start",
                headers=headers
            )
            print(f"    Status: {resp.status_code}")
            if resp.status_code in [200, 201]:
                print("    ✅ Sessão iniciada")
                print()
                print("    🔄 Aguardando QR Code...")
                await asyncio.sleep(3)
            else:
                print(f"    Resposta: {resp.text}")
        except Exception as e:
            print(f"    ❌ Erro: {e}")
            return
        print()
        
        # 4. Obter QR Code
        print("[4] Obtendo QR Code...")
        try:
            resp = await client.get(
                f"{WAHA_URL}/api/sessions/{WAHA_SESSION}/auth/qr",
                headers=headers
            )
            print(f"    Status: {resp.status_code}")
            if resp.status_code == 200:
                qr_data = resp.json()
                print()
                print("=" * 60)
                print("📱 ESCANEIE O QR CODE NO WHATSAPP:")
                print("=" * 60)
                print()
                print(f"Acesse: http://localhost:3000/api/sessions/{WAHA_SESSION}/auth/qr")
                print()
                print("Ou abra o dashboard:")
                print(f"http://localhost:3000/dashboard")
                print()
                print("Usuário: admin")
                print("Senha: adminops")
                print()
                print("=" * 60)
            else:
                print(f"    ⚠️  QR Code não disponível ainda")
                print(f"    Resposta: {resp.text}")
        except Exception as e:
            print(f"    ⚠️  Erro ao obter QR: {e}")
        print()
        
        # 5. Monitorar status
        print("[5] Monitorando conexão (aguardando 60s)...")
        for i in range(12):  # 12 x 5s = 60s
            await asyncio.sleep(5)
            try:
                resp = await client.get(
                    f"{WAHA_URL}/api/sessions/{WAHA_SESSION}",
                    headers=headers
                )
                if resp.status_code == 200:
                    session = resp.json()
                    status = session.get('status')
                    print(f"    [{i+1}/12] Status: {status}")
                    
                    if status == "WORKING":
                        print()
                        print("    ✅ CONECTADO COM SUCESSO!")
                        print()
                        if session.get('me'):
                            print(f"    📱 Número: {session['me'].get('id')}")
                        return
                    elif status == "FAILED":
                        print()
                        print("    ❌ Falha na conexão")
                        print("    Tente novamente ou verifique os logs do WAHA")
                        return
            except Exception as e:
                print(f"    ⚠️  Erro ao verificar status: {e}")
        
        print()
        print("    ⏱️  Timeout - verifique manualmente o status")
    
    print()
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(restart_waha_session())
