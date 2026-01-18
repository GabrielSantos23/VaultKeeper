# Environment Variables Security

VaultKeeper uses environment variables to protect sensitive OAuth credentials from being exposed in source code.

## 🔐 How It Works

Instead of hardcoding credentials:

```python
# ❌ BAD - Exposed in git
client_secret = "GOCSPX-..."
```

We use environment variables:

```python
# ✅ GOOD - Protected
client_secret = os.getenv("GDRIVE_CLIENT_SECRET", "fallback")
```

## 📁 Files

### `.env` (Secret - Never commit!)

Contains actual credentials. Protected by `.gitignore`.

### `.env.example` (Template - Can commit)

Template showing required variables without sensitive values.

## 🚀 Setup for Developers

1. Copy the example:

   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your credentials:

   ```bash
   nano .env
   ```

3. Verify `.env` is gitignored:
   ```bash
   git status  # Should NOT show .env
   ```

## 🔒 Current Variables

- `GDRIVE_CLIENT_ID`: OAuth client ID
- `GDRIVE_PROJECT_ID`: Google Cloud project ID
- `GDRIVE_CLIENT_SECRET`: OAuth client secret

## 📦 Distribution

For **production releases**, you have two options:

### Option 1: Include Credentials (Easiest)

The code has fallback values for end users:

```python
client_id = os.getenv("GDRIVE_CLIENT_ID", "default-value")
```

Users don't need `.env` - it just works!

### Option 2: Require User Configuration

Remove fallbacks and require users to create `.env`:

```python
client_id = os.getenv("GDRIVE_CLIENT_ID")
if not client_id:
    raise ValueError("Please configure GDRIVE_CLIENT_ID")
```

**Current**: We use Option 1 for better UX.

## ⚠️ Security Best Practices

1. **Never commit `.env`** - Always in `.gitignore`
2. **Rotate credentials** if accidentally exposed
3. **Use different credentials** for dev/prod
4. **Restrict OAuth scopes** to minimum needed
5. **Monitor usage** in Google Cloud Console

## 🔄 Rotating Credentials

If credentials are exposed:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Delete compromised OAuth client
3. Create new OAuth client
4. Update `.env` with new values
5. Restart app

## 🎯 Best Practices for This Project

- ✅ `.env` is gitignored
- ✅ Default values for users
- ✅ `python-dotenv` loads automatically
- ✅ No credentials in source code
- ✅ Template provided (`.env.example`)
