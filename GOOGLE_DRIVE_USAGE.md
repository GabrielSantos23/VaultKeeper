# Google Drive Sync - User Guide

VaultKeeper agora vem com Google Drive sync **integrado e pronto para usar**! Não precisa configurar nada complicado.

## 🚀 Como Usar (Super Simples)

### 1. Conectar ao Google Drive

1. Abra o VaultKeeper
2. Clique no botão **☁️ Sync** no toolbar
3. Clique em **🔗 Connect Google Drive**
4. Uma página do navegador abrirá
5. Faça login com sua conta Google
6. Clique em **Permitir** quando solicitado
7. Pronto! Seu vault será automaticamente sincronizado

### 2. O Que Acontece Automaticamente

- ✅ Pasta "VaultKeeper" criada no seu Google Drive
- ✅ Vault criptografado enviado para a pasta
- ✅ Toda alteração que você fizer sincroniza automaticamente
- ✅ Indicador visual mostra status (✅ = sincronizado)

### 3. Usando em Múltiplos Dispositivos

1. **PC Principal**: Conecte ao Google Drive (passos acima)
2. **Outro PC/Laptop**:
   - Instale VaultKeeper
   - Conecte ao Google Drive
   - Vault será baixado automaticamente
   - Pronto! Mesmas senhas em todos os dispositivos

## 📊 Indicador de Status

No toolbar, ao lado do botão "Sync", você verá:

| Ícone | Significado                |
| ----- | -------------------------- |
| ⚪    | Google Drive não conectado |
| ✅    | Sincronizado perfeitamente |
| 🔄    | Sincronizando agora...     |
| ⚠️    | Precisa sincronizar        |
| ❌    | Erro na sincronização      |

## 🔐 Segurança

- **Criptografia de ponta a ponta**: Vault é criptografado ANTES de ir para o Drive
- **Google não pode ler**: Apenas você tem a senha mestra
- **Zero-knowledge**: Nem o VaultKeeper, nem o Google sabem suas senhas
- **Acesso limitado**: App só acessa arquivos que ele mesmo criou

## ⚙️ Configurações Avançadas

### Sincronização Manual

Se preferir controle manual:

1. Clique em **☁️ Sync**
2. Use os botões:
   - **📤 Upload to Drive**: Envia vault manualmente
   - **📥 Download from Drive**: Baixa vault manualmente
   - **🔄 Auto-Sync**: Sincroniza inteligentemente

### Desconectar

Para desconectar do Google Drive:

1. Clique em **☁️ Sync**
2. Clique em **🔌 Disconnect**
3. Confirme

Seus arquivos no Drive permanecem intactos. Você pode reconectar a qualquer momento.

## 🆘 Problemas Comuns

### "Não consegui conectar"

- Verifique sua conexão com a internet
- Certifique-se de permitir acesso quando o navegador abrir
- Tente desconectar e conectar novamente

### "Vault não sincronizou"

- Verifique o indicador de status no toolbar
- Clique em **☁️ Sync** → **🔄 Auto-Sync** para forçar
- Veja a barra de status para mensagens de erro

### "Tenho versões diferentes em dois PCs"

- O VaultKeeper detecta automaticamente qual é a mais recente
- Use **🔄 Auto-Sync** - ele escolhe a versão correta
- Se quiser forçar: use Upload ou Download conforme necessário

## 📁 Onde Estão Meus Arquivos?

No seu Google Drive:

```
Google Drive/
└── VaultKeeper/
    └── VaultKeeper.enc
```

Você pode ver a pasta no Google Drive web, mas **NÃO edite o arquivo** diretamente!

## 🔒 Privacidade

- **Credenciais OAuth**: Salvas em `~/.config/vaultkeeper/gdrive_token.pickle`
- **Revogação**: Revogue em [Google Account → Security → Third-party apps](https://myaccount.google.com/permissions)
- **Exclusão**: Delete a pasta VaultKeeper no Drive quando quiser

## 💡 Dicas

1. **Sempre sincronizado**: Deixe conectado ao Drive - sync é automático
2. **Múltiplos PCs**: Funciona perfeitamente, sem conflitos
3. **Backup extra**: Pasta VaultKeeper no Drive serve como backup na nuvem
4. **Offline**: Vault funciona normalmente offline, sincroniza quando conectar

---

**Nota**: Diferente de outros apps que exigem configuração complexa, o VaultKeeper já vem **pronto para usar**. Apenas conecte sua conta Google e pronto! 🎉
