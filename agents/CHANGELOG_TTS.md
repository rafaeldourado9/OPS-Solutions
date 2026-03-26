# 🔥 Resumo das Alterações - Agente Adulto com TTS

## ✅ Problema Resolvido

**Erro original:** `TTS==0.22.0` não compatível com Python 3.12

**Solução:** Downgrade para Python 3.11 no Dockerfile

## 📦 Arquivos Criados/Modificados

### 1. Core - Porta TTS
- ✅ `core/ports/tts_port.py` - Interface abstrata para TTS

### 2. Adapter TTS
- ✅ `adapters/outbound/media/tts_adapter.py` - Implementação com Coqui TTS + gemidos

### 3. Adapter Gateway Fake
- ✅ `adapters/outbound/gateway/fake_gateway_adapter.py` - Para testes sem enviar mensagens

### 4. Configurações
- ✅ `agents/bbzinha/business.yml` - Config do agente adulto
- ✅ `agents/adult_content/business.yml` - Atualizado com mais safadeza
- ✅ `infrastructure/config_loader.py` - Adicionado campo `enable_tts`

### 5. Dependency Injection
- ✅ `api/dependencies.py` - Integração do TTS no container

### 6. Use Case
- ✅ `core/use_cases/process_message.py` - Já tinha suporte a TTS, mantido

### 7. Scripts
- ✅ `scripts/test_tts.py` - Teste local do TTS
- ✅ `scripts/setup_adult_agent.sh` - Setup automatizado
- ✅ `rebuild.bat` - Rebuild com Python 3.11

### 8. Documentação
- ✅ `agents/bbzinha/README.md` - Guia completo de uso

### 9. Dependências
- ✅ `Dockerfile` - Python 3.12 → 3.11
- ✅ `requirements.txt` - Removido torch/torchaudio duplicados

## 🎤 Funcionalidades do TTS

### Como Funciona
1. Texto → Voz (Coqui TTS modelo português)
2. Detecta pausas entre frases
3. Insere gemidos sintéticos (200-400Hz)
4. Converte para OGG/Opus
5. Envia via WAHA como áudio

### Personalização de Gemidos

```python
# Em adapters/outbound/media/tts_adapter.py

def _generate_moan(self) -> AudioSegment:
    duration_ms = 800  # ← Ajuste aqui
    
    # Frequências (Hz) - tom feminino sensual
    moan1 = Sine(200).to_audio_segment(duration=duration_ms // 2)
    moan2 = Sine(400).to_audio_segment(duration=duration_ms // 4)
    moan3 = Sine(300).to_audio_segment(duration=duration_ms // 4)
    
    moan = moan1 + moan2 + moan3
    moan = moan.fade_in(100).fade_out(200) - 20  # ← Volume
    
    return moan
```

**Ajustes possíveis:**
- `duration_ms`: 500-1500ms (duração do gemido)
- Frequências: 150-500Hz (mais grave/agudo)
- Volume: -10 a -30 dB (mais alto/baixo)

## 🚀 Como Usar

### 1. Rebuild (OBRIGATÓRIO)
```bash
# Windows
rebuild.bat

# Linux/Mac
docker-compose build --no-cache
```

### 2. Instalar dependências Python
```bash
pip install -r requirements.txt
```

### 3. Baixar modelos
```bash
bash scripts/setup_adult_agent.sh
```

### 4. Testar TTS localmente
```bash
python scripts/test_tts.py
# Gera test_output.ogg
```

### 5. Rodar agente
```bash
# Modo normal (envia mensagens)
AGENT_ID=bbzinha uvicorn api.main:app --reload

# Modo teste (só loga, não envia)
USE_FAKE_GATEWAY=true AGENT_ID=bbzinha uvicorn api.main:app --reload
```

## 🔧 Configuração

### Habilitar/Desabilitar Áudio

Em `agents/bbzinha/business.yml`:

```yaml
messaging:
  enable_tts: true  # true = áudio, false = texto
```

### Ajustar Safadeza

```yaml
llm:
  temperature: 0.98  # 0.0-1.0 (maior = mais criativo/aleatório)
```

### Persona

Edite a seção `persona:` no YAML para:
- Mudar linguagem/tom
- Ajustar limites
- Adicionar/remover comportamentos

## 📊 Diferenças entre Configs

### adult_content vs bbzinha

| Aspecto | adult_content | bbzinha |
|---------|---------------|---------|
| Nome | Safira | bbzinha |
| Tom | Sensual | Extremamente vulgar |
| Palavrões | Moderado | Pesado |
| Temperatura | 0.9 | 0.98 |
| Grounding | Desabilitado | Desabilitado |
| TTS | Habilitado | Habilitado |

## 🐛 Troubleshooting

### Erro: TTS não encontrado
**Solução:** Rebuild com `rebuild.bat`

### Áudio não envia
1. Verifique `enable_tts: true`
2. Veja logs: `tts.loading` e `tts.loaded`
3. Teste: `python scripts/test_tts.py`

### Gemidos muito altos
Ajuste volume em `tts_adapter.py`:
```python
moan = moan - 30  # Mais baixo
```

## 💡 Próximos Passos

1. **Testar localmente** com `test_tts.py`
2. **Rodar em modo fake** para validar fluxo
3. **Conectar WAHA** e testar com WhatsApp real
4. **Ajustar gemidos** conforme feedback
5. **Monetizar** 💰

## 📝 Notas Importantes

- ⚠️ **Conteúdo adulto:** Use com responsabilidade
- 🔒 **Segurança:** Não exponha sem autenticação
- 💰 **Monetização:** Implemente pagamentos antes de lançar
- 📊 **Monitoramento:** Acompanhe uso e custos
- ⚖️ **Legal:** Respeite leis locais

---

**Tudo pronto! Agora é só buildar e testar. 🔥💦**
