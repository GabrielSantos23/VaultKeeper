# Configuração do Google Drive OAuth

Para habilitar a sincronização com Google Drive, você precisa configurar credenciais OAuth no Google Cloud Console.

## Passo 1: Criar Projeto no Google Cloud

1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um novo projeto ou selecione um existente
3. Nome sugerido: "VaultKeeper"

## Passo 2: Ativar Google Drive API

1. No menu lateral, vá em **APIs & Services** → **Library**
2. Procure por "Google Drive API"
3. Clique em **Enable**

## Passo 3: Criar Credenciais OAuth

1. Vá em **APIs & Services** → **Credentials**
2. Clique em **Create Credentials** → **OAuth client ID**
3. Se solicitado, configure a tela de consentimento:

   - User Type: **External**
   - App name: **VaultKeeper**
   - User support email: seu email
   - Developer contact: seu email
   - Scopes: **não adicione nenhum** (usaremos apenas drive.file)
   - Test users: adicione seu email

4. Criar OAuth Client ID:

   - Application type: **Desktop app**
   - Name: **VaultKeeper Desktop**
   - Clique em **Create**

5. **Download** o arquivo JSON das credenciais

## Passo 4: Configurar no VaultKeeper

### Opção A: Arquivo de Credenciais (Recomendado)

1. Salve o arquivo JSON baixado como:

   ```
   ~/.config/vaultkeeper/client_secret.json
   ```

   Ou no Windows:

   ```
   %APPDATA%\VaultKeeper\client_secret.json
   ```

2. O VaultKeeper detectará automaticamente este arquivo

### Opção B: Configurar Manualmente no Código

1. Abra `app/utils/gdrive.py`
2. Encontre a variável `CLIENT_CONFIG`
3. Substitua os valores:
   ```python
   CLIENT_CONFIG = {
       "installed": {
           "client_id": "SEU_CLIENT_ID.apps.googleusercontent.com",
           "client_secret": "SEU_CLIENT_SECRET",
           # ... mantenha o resto igual
       }
   }
   ```

## Passo 5: Primeiro Login

1. Execute o VaultKeeper
2. Clique no botão **☁️ Sync**
3. Clique em **Connect Google Drive**
4. Uma página do navegador abrirá
5. Faça login com sua conta Google
6. Autorize o acesso do VaultKeeper
7. Pronto! O token será salvo automaticamente

## Segurança

- **Token armazenado localmente**: `~/.config/vaultkeeper/gdrive_token.pickle`
- **Escopo limitado**: Apenas acesso a arquivos criados pelo app (`drive.file`)
- **Renovação automática**: Token é renovado automaticamente quando expira
- **Revogação**: Para revogar acesso, vá em [Google Account Security](https://myaccount.google.com/permissions)

## Troubleshooting

### "Google Drive not configured"

- Verifique se o arquivo `client_secret.json` existe
- Ou configure manualmente no código conforme Opção B

### "Authentication failed"

- Certifique-se que a Google Drive API está ativada
- Verifique se você adicionou seu email como test user
- Tente revogar e autenticar novamente

### "Vault not found in Google Drive"

- Faça o primeiro upload clicando em "Upload to Google Drive"
- O app criará o arquivo automaticamente

## Exemplo de Uso

```python
from pathlib import Path
from app.utils.gdrive import GoogleDriveSync
from app.core.config import Config

# Inicializar
token_path = Config.get_config_dir() / 'gdrive_token.pickle'
gdrive = GoogleDriveSync(token_path)

# Autenticar
success, message = gdrive.authenticate()
if success:
    print("Autenticado!")

    # Upload
    vault_path = Path("~/VaultKeeper.enc").expanduser()
    success, msg = gdrive.upload_vault(vault_path)
    print(msg)

    # Download
    success, msg = gdrive.download_vault(vault_path)
    print(msg)

    # Auto-sync (inteligente)
    success, msg = gdrive.auto_sync(vault_path)
    print(msg)
```

## Próximos Passos

Após configurar, você poderá:

- ✅ Upload manual do vault
- ✅ Download manual do vault
- ✅ Sync automático (detecta qual versão é mais recente)
- ✅ Status de sincronização
- ✅ Trabalhar em múltiplos dispositivos

**Nota**: O Google Drive é OPCIONAL. O VaultKeeper funciona perfeitamente sem ele, usando apenas armazenamento local.
