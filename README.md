# 🔐 VaultKeeper - Password Manager

Um gerenciador de senhas desktop seguro com integração de extensão de navegador usando Native Messaging.

## 🧠 Visão Geral

```
┌────────────────┐      Native Messaging      ┌────────────────────┐
│ Browser        │ ◀──────────────────────▶  │ App Desktop Python │
│ Extension      │                            │ (Password Manager) │
└────────────────┘                            └────────────────────┘
```

### Princípios de Segurança

- A **extensão nunca acessa o banco de dados**
- A **extensão nunca armazena senhas**
- Toda criptografia acontece **no app desktop**
- Comunicação direta e local (sem HTTP)
- Criptografia **AES-256-GCM**
- Hash de senha mestra com **Argon2id**

## 📁 Estrutura do Projeto

```
VaultKeeper-v2/
├── app/
│   ├── core/
│   │   ├── crypto.py        # Criptografia AES-256-GCM
│   │   ├── auth.py          # Master password (Argon2)
│   │   └── vault.py         # Regras de negócio
│   ├── db/                  # SQLite (gerado automaticamente)
│   ├── native/
│   │   └── host.py          # Native Messaging host
│   ├── ui/
│   │   └── main_window.py   # Interface gráfica PySide6
│   └── main.py              # Entry point
├── extension/
│   ├── manifest.json        # Manifest V3
│   ├── background.js        # Service Worker
│   ├── content.js           # Detecção de formulários
│   ├── popup.html/css/js    # Interface do popup
│   └── icons/
├── native_host/
│   ├── com.vaultkeeper.host.json
│   └── install_linux.sh
└── requirements.txt
```

## 🚀 Instalação

### 1. Dependências Python

#### Linux / macOS (Bash/Zsh)

```bash
# Criar ambiente virtual (recomendado)
python3 -m venv .venv
source .venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

#### Linux (Fish Shell)

```fish
# Criar ambiente virtual (recomendado)
python3 -m venv .venv
source .venv/bin/activate.fish

# Instalar dependências
pip install -r requirements.txt
```

#### Windows

```powershell
# Criar ambiente virtual (recomendado)
# Se o comando 'python' não funcionar, tente 'py'
python -m venv .venv
.\.venv\Scripts\Activate

# Instalar dependências
pip install -r requirements.txt
```

### 2. Executar o App Desktop

#### Linux / macOS (Bash/Zsh)

```bash
# Ative o ambiente virtual primeiro (se não estiver ativo)
source .venv/bin/activate

# Execute o app
python3 app/main.py
```

#### Linux (Fish Shell)

```fish
# Ative o ambiente virtual primeiro (se não estiver ativo)
source .venv/bin/activate.fish

# Execute o app
python3 app/main.py
```

#### Windows

```powershell
# Ative o ambiente virtual primeiro (se não estiver ativo)
.\.venv\Scripts\Activate

# Execute o app
python app\main.py
```

Na primeira execução, você criará sua **senha mestra**.

### 3. Instalar a Extensão no Chrome

1. Abra `chrome://extensions/`
2. Ative o **Modo do desenvolvedor**
3. Clique em **Carregar sem compactação**
4. Selecione a pasta `extension/`

> **Nota**: O Native Messaging Host é instalado automaticamente quando o app desktop é executado. Não é necessária configuração manual.

### 4. Usar

1. Execute o app desktop (veja comandos acima para seu shell)
2. Na primeira execução, o Native Host será configurado automaticamente
3. Clique no ícone da extensão VaultKeeper no navegador
4. A extensão deve mostrar que está conectada!

### Instalação Manual do Native Host (opcional)

Se precisar reinstalar manualmente o Native Host:

```bash
# Bash/Zsh
source .venv/bin/activate && python -m app.native.installer install

# Fish Shell
source .venv/bin/activate.fish && python -m app.native.installer install
```

Para verificar o status:

```bash
# Bash/Zsh
source .venv/bin/activate && python -m app.native.installer check

# Fish Shell
source .venv/bin/activate.fish && python -m app.native.installer check
```

## 🔐 Funcionalidades

### App Desktop

- ✅ Login com senha mestra
- ✅ Adicionar/editar/excluir credenciais
- ✅ Gerador de senhas seguras
- ✅ Busca de credenciais
- ✅ Auto-lock por inatividade
- ✅ Cópia para clipboard com limpeza automática

### Extensão

- ✅ Detecção automática de formulários de login
- ✅ Preenchimento automático (autofill)
- ✅ Busca de credenciais
- ✅ Cópia de senhas
- ✅ Adicionar novas credenciais

## 🛡️ Segurança

### Master Password

- Hash com **Argon2id** (OWASP recommended)
- 600.000 iterações PBKDF2 para derivação de chave
- Proteção contra brute-force (lockout após 5 tentativas)

### Criptografia

- **AES-256-GCM** para todas as senhas
- Salt único por credencial (16 bytes)
- Nonce aleatório (12 bytes)

### Proteções

- Timeout de inatividade (5 minutos)
- Limpeza de clipboard após 10 segundos
- Chave nunca é salva em disco
- Banco de dados com senhas criptografadas

## 📝 API do Native Host

### Ações Suportadas

| Ação                  | Descrição                                |
| --------------------- | ---------------------------------------- |
| `ping`                | Verificar conexão                        |
| `status`              | Status do cofre (bloqueado/desbloqueado) |
| `unlock`              | Desbloquear com senha mestra             |
| `lock`                | Bloquear o cofre                         |
| `get_credentials`     | Obter credenciais por domínio            |
| `save_credentials`    | Salvar nova credencial                   |
| `delete_credentials`  | Excluir credencial                       |
| `get_all_credentials` | Listar todas as credenciais              |
| `search`              | Buscar credenciais                       |

### Exemplo de Mensagem

```json
{
  "action": "get_credentials",
  "domain": "github.com"
}
```

### Exemplo de Resposta

```json
{
  "success": true,
  "credentials": [
    {
      "id": 1,
      "domain": "github.com",
      "username": "user@email.com",
      "password": "DECRYPTED_PASSWORD"
    }
  ]
}
```

## 🔧 Desenvolvimento

### Logs do Native Host

```bash
tail -f ~/.vaultkeeper/native_host.log
```

### Banco de Dados

```bash
# Localização
~/.vaultkeeper/vault.db

# Visualizar (senhas criptografadas)
sqlite3 ~/.vaultkeeper/vault.db "SELECT id, domain, username FROM vault;"
```

## 📈 Roadmap

- [ ] Biometria (fingerprint)
- [x] Backup criptografado para cloud
- [ ] Importação de CSV
- [ ] Detecção de senhas vazadas (HIBP)
- [x] Suporte a TOTP (2FA)
- [x] Geração de senhas personalizável
- [x] Extensão para Firefox

## 📄 Licença

MIT License
