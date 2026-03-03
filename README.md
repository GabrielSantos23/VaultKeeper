<p align="center">
  <img src="logo.png" alt="VaultKeeper Logo" width="120" />
</p>

<h1 align="center">VaultKeeper 2.0</h1>

<p align="center">
  Gerenciador de senhas desktop seguro com integração nativa para extensão de navegador.<br />
  Construído com <strong>Rust + Tauri + React</strong> para máxima performance e segurança.
</p>

<p align="center">
  <a href="https://github.com/GabrielSantos23/VaultKeeper/releases/latest">
    <img src="https://img.shields.io/github/v/release/GabrielSantos23/VaultKeeper?style=for-the-badge&color=f97316&label=Download" alt="Download" />
  </a>
  <img src="https://img.shields.io/badge/Plataformas-Windows%20%7C%20Linux-blue?style=for-the-badge" alt="Plataformas" />
  <img src="https://img.shields.io/github/license/GabrielSantos23/VaultKeeper?style=for-the-badge" alt="Licença" />
</p>

---

## 📸 Screenshots

<!-- Adicione screenshots do app aqui -->
<!-- <p align="center">
  <img src="screenshots/login.png" alt="Tela de Login" width="400" />
  <img src="screenshots/vault.png" alt="Cofre" width="400" />
</p> -->

> 🖼️ _Screenshots em breve_

---

## 🚀 O que há de novo na versão 2.0

- ⚡ **Ultra rápido** — Binário nativo em Rust, sem necessidade de Python
- 🔄 **Atualizações automáticas** — Receba novas versões automaticamente
- 💾 **Migração zero** — Usuários da versão Python mantêm todos os dados
- 🎨 **Interface moderna** — UI premium com modo escuro e animações
- 🔒 **Mesma segurança** — Criptografia idêntica (Argon2id + AES-256-GCM)
- 🌐 **Extensão para navegador** — Chrome, Firefox, Edge, Brave, Vivaldi, Opera, Zen
- 📱 **Multiplataforma** — Windows e Linux
- 🔌 **Conexão persistente** — No Linux, o native host funciona mesmo sem o app aberto

---

## 📦 Instalação

### Baixar binários pré-compilados

| Plataforma | Download                                            |
| ---------- | --------------------------------------------------- |
| Windows    | `VaultKeeper_2.x.x_x64-setup.exe` (Instalador NSIS) |
| Linux      | `VaultKeeper_2.x.x_amd64.AppImage` (Portátil)       |

👉 Baixe na página de [Releases do GitHub](https://github.com/GabrielSantos23/VaultKeeper/releases/latest)

### Compilar a partir do código fonte

```bash
# Clone o repositório
git clone https://github.com/GabrielSantos23/VaultKeeper.git
cd VaultKeeper/vaultkeeper-tauri

# Instale as dependências
bun install

# Rode em modo de desenvolvimento
bun run tauri:dev

# Compile para produção
bun run tauri:build
```

**Pré-requisitos:** [Bun](https://bun.sh/), [Rust](https://rustup.rs/), [Python 3.11+](https://python.org/) (para compilar o native host)

---

## 🔄 Migração da versão Python

**Boa notícia: Não é necessária migração de dados!** 🎉

A versão Tauri é **totalmente compatível** com a versão Python:

- ✅ Mesmo formato de banco de dados (SQLite)
- ✅ Mesma criptografia (Argon2id + AES-256-GCM)
- ✅ Mesmo local de armazenamento (`~/.vaultkeeper/`)
- ✅ Mesma senha mestre

### Como migrar

1. **O instalador detecta** a versão Python automaticamente
2. **Pergunta se deseja desinstalar** a versão antiga
3. **Instala a versão Tauri** no lugar
4. **Faça login com a mesma senha mestre** — seus dados já estarão lá

> No Windows, o instalador NSIS usa hooks personalizados para detectar e remover a versão Python (Inno Setup) automaticamente, incluindo suporte a registros de 32-bit (WOW6432Node).

---

## 🏗️ Arquitetura

```
┌──────────────────┐     Native Messaging      ┌─────────────────────┐
│ Extensão do      │ ◀────────────────────────▶ │ vk_host             │
│ Navegador        │        (stdio)             │ (Python, autônomo)  │
└──────────────────┘                            └─────────┬───────────┘
                                                          │
                                                          ▼
┌──────────────────┐                            ┌─────────────────────┐
│ VaultKeeper App  │──── configura manifestos ──│ SQLite Database     │
│ (Rust + Tauri)   │    e registros ao iniciar  │ (Criptografado)     │
└──────────────────┘                            └─────────────────────┘
```

### Como o `vk_host` funciona

O `vk_host` é um binário Python empacotado (PyInstaller) que serve como ponte entre a extensão do navegador e o banco de dados do VaultKeeper via **Native Messaging Protocol** (stdio).

**No Windows:**

- O instalador coloca o `vk_host.exe` em `AppData\Local\VaultKeeper\bin\`
- Manifestos e chaves de registro são criados automaticamente ao abrir o app
- Funciona imediatamente com qualquer navegador suportado

**No Linux (AppImage):**

- Como o AppImage monta em um diretório temporário, o app **copia o `vk_host`** para `~/.local/share/vaultkeeper/bin/vk_host` — um local fixo e persistente
- Os manifestos dos navegadores apontam para esse caminho fixo
- Resultado: **a extensão funciona mesmo sem o app de desktop aberto**
- A cada abertura do app, o binário é atualizado automaticamente

---

## 🛡️ Segurança

### Criptografia

| Componente            | Tecnologia                      |
| --------------------- | ------------------------------- |
| Hash da Senha Mestre  | Argon2id (recomendado OWASP)    |
| Criptografia do Banco | AES-256-GCM                     |
| Salt                  | Único por credencial (16 bytes) |
| Derivação de Chave    | PBKDF2 com 600.000 iterações    |

### Proteções

- 🔒 Bloqueio automático após inatividade
- 🧹 Limpeza automática da área de transferência
- 🚫 Chave de criptografia nunca salva em disco
- 🔐 Toda criptografia acontece localmente

---

## 📁 Armazenamento

| Plataforma | Local                         |
| ---------- | ----------------------------- |
| Windows    | `%USERPROFILE%\.vaultkeeper\` |
| Linux      | `~/.vaultkeeper/`             |

**Arquivos:**

- `vault.db` — Banco de dados SQLite (criptografado)
- `auth.json` — Configurações de autenticação
- `native_host.log` — Logs de debug do native host

---

## 🔌 Extensão do Navegador

### Navegadores suportados

| Navegador | Windows | Linux               |
| --------- | ------- | ------------------- |
| Chrome    | ✅      | ✅                  |
| Firefox   | ✅      | ✅ (+ Snap/Flatpak) |
| Edge      | ✅      | ✅                  |
| Brave     | ✅      | ✅                  |
| Chromium  | ✅      | ✅ (+ Snap)         |
| Vivaldi   | ✅      | ✅                  |
| Opera     | ✅      | ✅                  |
| Zen       | ✅      | ✅                  |

### Instalação da extensão

1. Abra a página de extensões do seu navegador:
   - Chrome: `chrome://extensions/`
   - Firefox: `about:addons`
   - Edge: `edge://extensions/`

2. Ative o **Modo Desenvolvedor**

3. Clique em **Carregar sem compactação** e selecione a pasta `extension/`

4. A extensão conecta automaticamente ao app desktop

### Reconectar manualmente

Se a extensão não conectar, abra o app Tauri e vá em **Settings > General > Browser Extension**:

- **Reconnect All** — Reinstala os manifestos para todos os navegadores detectados
- **Select Browser** — Instala para um navegador específico
- **Custom Path** — Instalação manual em um diretório personalizado

### Funcionalidades

- 🔍 Detecção automática de formulários de login
- 📝 Preenchimento automático de credenciais
- 🔎 Busca de senhas
- 📋 Copiar senhas para a área de transferência
- ➕ Salvar novas credenciais
- 🔑 Suporte a TOTP (autenticação em dois fatores)
- 💳 Cartões de crédito e notas seguras

---

## 🔄 Atualizações Automáticas

O VaultKeeper verifica automaticamente por novas versões no GitHub ao iniciar:

1. Um toast aparece quando há uma atualização disponível
2. Clique em **"Atualizar Agora"** para baixar
3. O app reinicia automaticamente

As atualizações são assinadas com chave privada para segurança.

---

## 🐛 Solução de Problemas

### App não abre

- Verifique se `~/.vaultkeeper/` tem permissões de escrita
- Windows: tente executar como administrador

### Extensão não conecta

1. Certifique-se de que o app desktop foi aberto pelo menos uma vez (para criar os manifestos)
2. Abra **Settings > Browser Extension > Reconnect All** no app
3. Reinicie o navegador
4. Verifique o console do navegador para erros

### Versão Python não foi removida (Windows)

1. Desinstale manualmente pelo Painel de Controle
2. Ou baixe o instalador da v2.0.2+ que detecta e remove automaticamente

### Atualização falha

1. Verifique sua conexão com a internet
2. Baixe manualmente da página de [Releases](https://github.com/GabrielSantos23/VaultKeeper/releases)

---

## 🛠️ Desenvolvimento

### Estrutura do Projeto

```
VaultKeeper/
├── vaultkeeper-tauri/          # App desktop (Tauri v2)
│   ├── src/                    # Frontend React
│   │   ├── components/         # Componentes React
│   │   ├── stores/             # Estado (Zustand)
│   │   ├── views/              # Páginas
│   │   └── hooks/              # Hooks personalizados
│   ├── src-tauri/              # Backend Rust
│   │   ├── src/
│   │   │   ├── main.rs         # Entry point
│   │   │   ├── native_host.rs  # Configuração do native messaging
│   │   │   └── lib.rs          # Módulos compartilhados
│   │   └── icons/              # Ícones do app
│   └── package.json
├── app/                        # Código Python (native host + vault)
│   ├── native/
│   │   ├── host.py             # Native messaging host
│   │   └── installer.py        # Instalador dos manifestos
│   └── core/
│       ├── vault.py            # Gerenciador de credenciais
│       └── auth.py             # Autenticação
├── extension/                  # Extensão do navegador
└── logo.png                    # Logo do VaultKeeper
```

---

## 📄 Licença

MIT License — veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🙏 Agradecimentos

- Construído com [Tauri](https://tauri.app/)
- UI com [React](https://react.dev/) e [Tailwind CSS](https://tailwindcss.com/)
- Ícones por [HugeIcons](https://hugeicons.com/)

---

<p align="center">
  Feito com ❤️ por <a href="https://github.com/GabrielSantos23">Gabriel Santos</a>
</p>
