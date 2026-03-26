"""Script para verificar mensagens enviadas pelo agente."""

import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

async def check_sent_messages():
    """Verifica todas as mensagens enviadas pelo agente."""
    
    db_url = os.environ.get("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/whatsapp_agent")
    
    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Buscar mensagens do assistente (enviadas pelo agente)
        query = text("""
            SELECT 
                chat_id,
                role,
                content,
                created_at,
                agent_id
            FROM messages 
            WHERE role = 'assistant'
            ORDER BY created_at DESC
            LIMIT 50
        """)
        
        result = await session.execute(query)
        messages = result.fetchall()
        
        if not messages:
            print("✅ NENHUMA mensagem foi enviada pelo agente!")
            print("O agente NÃO enviou spam.")
            return
        
        print(f"⚠️ Encontradas {len(messages)} mensagens enviadas:\n")
        
        # Agrupar por chat_id
        chats = {}
        for msg in messages:
            chat_id = msg[0]
            if chat_id not in chats:
                chats[chat_id] = []
            chats[chat_id].append(msg)
        
        print(f"📊 Total de conversas: {len(chats)}\n")
        
        for chat_id, msgs in chats.items():
            print(f"Chat: {chat_id}")
            print(f"  Mensagens enviadas: {len(msgs)}")
            print(f"  Última mensagem: {msgs[0][3]}")
            print(f"  Prévia: {msgs[0][2][:100]}...")
            print()
        
        # Verificar se há envio em massa (muitos chats diferentes)
        if len(chats) > 10:
            print(f"🚨 ALERTA: {len(chats)} conversas diferentes!")
            print("Pode ter havido envio em massa.")
        else:
            print(f"✅ Apenas {len(chats)} conversa(s). Parece normal.")

if __name__ == "__main__":
    asyncio.run(check_sent_messages())
