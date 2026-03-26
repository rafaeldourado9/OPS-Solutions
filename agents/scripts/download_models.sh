#!/bin/bash
set -e

echo "🔄 Baixando modelos do Ollama..."

# Aguardar Ollama estar pronto
echo "⏳ Aguardando Ollama iniciar..."
until curl -s http://localhost:11434/api/tags > /dev/null 2>&1; do
    sleep 2
done

echo "✅ Ollama está pronto!"

# Baixar modelos
echo "📥 Baixando llama3.1:8b..."
ollama pull llama3.1:8b

echo "📥 Baixando llava:7b (visão)..."
ollama pull llava:7b

echo "📥 Baixando whisper:base (áudio)..."
ollama pull whisper:base

echo "📥 Baixando nomic-embed-text (embeddings)..."
ollama pull nomic-embed-text

echo "✅ Todos os modelos baixados com sucesso!"
