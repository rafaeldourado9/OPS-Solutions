"""Script de auditoria - Mostra TODAS as conversas e para quem o agente enviou."""

import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

async def audit_all_conversations():
    """Audita todas as conversas e mostra para quem o agente enviou mensagens."""
    
    db_url = os.environ.get("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/whatsapp_agent")
    
    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Buscar TODOS os chat_ids únicos
        query_chats = text("""
            SELECT DISTINCT chat_id, agent_id, MIN(created_at) as first_message
            FROM messages 
            GROUP BY chat_id, agent_id
            ORDER BY first_message DESC
        """)
        
        result = await session.execute(query_chats)
        chats = result.fetchall()
        
        if not chats:
            print("✅ Nenhuma conversa encontrada no banco de dados.")
            return
        
        print(f"\n{'='*80}")
        print(f"📊 AUDITORIA COMPLETA - Total de conversas: {len(chats)}")
        print(f"{'='*80}\n")
        
        for idx, (chat_id, agent_id, first_msg) in enumerate(chats, 1):
            print(f"\n{idx}. Chat ID: {chat_id}")
            print(f"   Agente: {agent_id}")
            print(f"   Primeira mensagem: {first_msg}")
            
            # Contar mensagens por role
            query_count = text("""
                SELECT role, COUNT(*) as count
                FROM messages
                WHERE chat_id = :chat_id
                GROUP BY role
            """)
            
            result_count = await session.execute(query_count, {"chat_id": chat_id})
            counts = result_count.fetchall()
            
            for role, count in counts:
                emoji = "👤" if role == "user" else "🤖"
                print(f"   {emoji} {role}: {count} mensagens")
            
            # Mostrar últimas 3 mensagens
            query_recent = text("""
                SELECT role, content, created_at
                FROM messages
                WHERE chat_id = :chat_id
                ORDER BY created_at DESC
                LIMIT 3
            """)
            
            result_recent = await session.execute(query_recent, {"chat_id": chat_id})
            recent = result_recent.fetchall()
            
            if recent:
                print(f"   📝 Últimas mensagens:")
                for role, content, created_at in reversed(recent):
                    emoji = "👤" if role == "user" else "🤖"
                    preview = content[:60] + "..." if len(content) > 60 else content
                    print(f"      {emoji} [{created_at}] {preview}")
        
        print(f"\n{'='*80}")
        
        # Resumo de segurança
        query_assistant = text("""
            SELECT COUNT(DISTINCT chat_id) as unique_chats
            FROM messages
            WHERE role = 'assistant'
        """)
        
        result_assistant = await session.execute(query_assistant)
        unique_chats_with_replies = result_assistant.scalar()
        
        print(f"\n🔍 RESUMO DE SEGURANÇA:")
        print(f"   Total de conversas: {len(chats)}")
        print(f"   Conversas com respostas do agente: {unique_chats_with_replies}")
        
        if unique_chats_with_replies > 5:
            print(f"\n   ⚠️  ALERTA: Agente respondeu para {unique_chats_with_replies} pessoas diferentes!")
            print(f"   Isso pode indicar envio em massa ou vazamento de mensagens.")
        elif unique_chats_with_replies == 0:
            print(f"\n   ✅ SEGURO: Agente NÃO enviou nenhuma mensagem ainda.")
        else:
            print(f"\n   ✅ NORMAL: Apenas {unique_chats_with_replies} conversa(s) ativa(s).")
        
        print(f"{'='*80}\n")

if __name__ == "__main__":
    asyncio.run(audit_all_conversations())
