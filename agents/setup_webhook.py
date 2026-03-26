#!/usr/bin/env python3
"""Script para configurar webhook no WAHA."""
import httpx
import os

WAHA_URL = os.getenv("WAHA_URL", "http://localhost:3000")
WAHA_API_KEY = os.getenv("WAHA_API_KEY", "adminops")
WEBHOOK_URL = "http://host.docker.internal:8000/webhook"

def setup_webhook():
    headers = {"X-Api-Key": WAHA_API_KEY}
    
    # Parar sessão
    print("Parando sessão default...")
    resp = httpx.post(f"{WAHA_URL}/api/sessions/default/stop", headers=headers, timeout=10)
    print(f"Stop: {resp.status_code}")
    
    # Aguardar
    import time
    time.sleep(3)
    
    # Iniciar com webhook
    print("Iniciando sessão com webhook...")
    payload = {
        "name": "default",
        "config": {
            "webhooks": [
                {
                    "url": WEBHOOK_URL,
                    "events": ["message"]
                }
            ],
            "noweb": {
                "store": {
                    "enabled": True,
                    "fullSync": True
                }
            }
        }
    }
    resp = httpx.post(
        f"{WAHA_URL}/api/sessions/default/start",
        json=payload,
        headers=headers,
        timeout=10
    )
    print(f"Start: {resp.status_code} - {resp.text}")
    
    # Verificar
    time.sleep(5)
    resp = httpx.get(f"{WAHA_URL}/api/sessions/default", headers=headers)
    print(f"\nStatus final: {resp.json()}")

if __name__ == "__main__":
    setup_webhook()
