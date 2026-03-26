@echo off
echo 🔧 Rebuilding com Python 3.11 para suporte TTS...
echo.

echo 📦 Parando containers...
docker-compose down

echo.
echo 🏗️ Rebuilding imagem (pode demorar alguns minutos)...
docker-compose build --no-cache

echo.
echo ✅ Build completo!
echo.
echo Para subir os serviços:
echo docker-compose up -d
echo.
echo Para rodar o agente:
echo AGENT_ID=bbzinha uvicorn api.main:app --reload
