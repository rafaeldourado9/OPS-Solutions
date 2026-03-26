@echo off
cd /d "%~dp0"
echo Criando commits atomicos...

git add agents/adapters/
git commit -m "feat(agents): add adapters layer"

git add agents/api/
git commit -m "feat(agents): add API layer"

git add agents/gateway/
git commit -m "feat(agents): add gateway service"

git add agents/sales/
git commit -m "feat(agents): add sales module"

git add agents/scripts/
git commit -m "chore(agents): add utility scripts"

git add agents/tests/
git commit -m "test(agents): add test suite"

git add agents/agents/
git commit -m "feat(agents): add all agent implementations"

git add agents/restart_waha.py agents/setup_webhook.py agents/test_waha.py agents/rebuild.bat
git commit -m "chore(agents): add utility scripts"

git add agents/sample_audio.ogg
git commit -m "chore(agents): add sample audio file"

git add agents/server.log 2>nul
git commit -m "chore(agents): add server log" 2>nul

git add commit_all.bat
git commit -m "chore: add commit automation script"

echo.
echo Commits criados!
echo.
git log --oneline -20
echo.
echo Status final:
git status --short
pause
