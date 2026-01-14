# 🔐 Gerenciador de Senhas Desktop + Extensão (Native Messaging)

Este documento descreve **passo a passo** como criar um **gerenciador de senhas desktop em Python** integrado a uma **extensão de navegador** usando **Native Messaging** (mesma abordagem usada por Bitwarden e 1Password).

---

## 🧠 Visão Geral da Arquitetura

```
┌────────────────┐      Native Messaging      ┌────────────────────┐
│ Browser        │  ◀──────────────────────▶ │ App Desktop Python  │
│ Extension      │                            │ (Password Manager) │
└────────────────┘                            └────────────────────┘
```

### Princípios importantes

- A **extensão nunca acessa o banco de dados**
- A **extensão nunca armazena senhas**
- Toda criptografia acontece **no app desktop**
- Comunicação direta e local (sem HTTP)

---

## 🧩 Tecnologias Utilizadas

### App Desktop

- Python 3.11+
- PySide6 (UI)
- SQLite (banco local)
- cryptography (AES-256-GCM)
- argon2-cffi (hash da master password)

### Extensão

- Manifest V3
- JavaScript ou TypeScript
- Native Messaging API

---

## 🗂️ Estrutura do Projeto

```
password-manager/
 ├── app/
 │   ├── core/
 │   │   ├── crypto.py        # Criptografia
 │   │   ├── auth.py          # Master password
 │   │   └── vault.py         # Regras de negócio
 │   ├── db/
 │   │   └── vault.db         # SQLite local
 │   ├── native/
 │   │   └── host.py          # Native Messaging host
 │   ├── ui/
 │   │   └── main_window.py   # Interface gráfica
 │   └── main.py
 └── extension/
     ├── manifest.json
     ├── background.js
     ├── content.js
```

---

## 🔐 Segurança (Obrigatório)

### Master Password

- Nunca salvar em texto
- Hash usando **Argon2**
- Usada apenas para derivar a chave

### Criptografia

- Algoritmo: **AES-256-GCM**
- Cada senha criptografada individualmente
- Chave derivada da master password

---

## 🗄️ Banco de Dados Local (SQLite)

### Schema

```sql
CREATE TABLE vault (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  domain TEXT NOT NULL,
  username TEXT NOT NULL,
  password BLOB NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

📌 Apenas a senha é criptografada (ou todos os campos, se quiser mais segurança).

---

## 🖥️ App Desktop – Passos de Implementação

### 1️⃣ Criar sistema de master password

- Primeira execução → criar master password
- Salvar apenas o **hash Argon2**

### 2️⃣ Implementar criptografia

- Derivar chave com a master password
- Funções `encrypt()` e `decrypt()`

### 3️⃣ Criar o banco SQLite

- Criar tabelas
- CRUD de credenciais

### 4️⃣ Interface gráfica

Telas mínimas:

- Login (master password)
- Lista de credenciais
- Adicionar / editar / remover
- Lock automático

---

## 🔗 Native Messaging – Conceito

Native Messaging permite que:

- A extensão execute um **programa local**
- Comunicação via **stdin / stdout** (JSON)

📌 Não usa HTTP, não expõe portas.

---

## 🧩 Native Host (Python)

### Protocolo

- Mensagens JSON
- Prefixo de 4 bytes indicando tamanho

### Exemplo de mensagem recebida

```json
{
  "action": "get_credentials",
  "domain": "github.com"
}
```

### Exemplo de resposta

```json
{
  "username": "user@email.com",
  "password": "DECRYPTED_PASSWORD"
}
```

---

## 🧠 Ações suportadas pelo Native Host

- `get_credentials`
- `save_credentials`
- `lock`
- `unlock`

---

## 🌐 Extensão – Implementação

### manifest.json

- Permissões:

  - `nativeMessaging`
  - `activeTab`
  - `scripting`

### background.js

- Conecta ao native host
- Envia ações
- Recebe respostas

### content.js

- Detecta formulários de login
- Preenche usuário e senha

---

## 🔄 Fluxo de Autofill

1. Usuário abre um site
2. content.js detecta o domínio
3. background.js envia pedido ao native host
4. App desktop retorna credenciais
5. Extensão preenche o formulário

---

## 📦 Registro do Native Host (SO)

### Linux

```json
~/.mozilla/native-messaging-hosts/password_manager.json
```

### Windows

- Registro do Windows
- Caminho para o executável Python

📌 O navegador precisa saber **onde está o host**.

---

## 🔒 Proteções Essenciais

- App precisa estar desbloqueado
- Timeout de inatividade
- Limpar senha da memória
- Bloquear clipboard após X segundos

---

## 🚀 Features Avançadas (Opcional)

- Gerador de senhas
- Backup criptografado
- Importação CSV
- Detecção de senhas vazadas
- Biometria (Windows Hello)

---

## 📈 Roadmap Sugerido

1. Criptografia + master password
2. Banco SQLite
3. UI básica
4. Native Messaging host
5. Extensão mínima
6. Autofill
7. Hardening de segurança

---

## ✅ Resultado Final

- App desktop seguro
- Extensão integrada
- Sem servidores
- Arquitetura profissional
- Projeto forte de portfólio

---

📌 Próximo passo sugerido:

- Implementar **crypto.py** corretamente
- Criar **native host funcional**

Se quiser, posso gerar **código base completo** para cada parte.
