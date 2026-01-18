"""
VaultKeeper - Google Drive Integration
Handles OAuth authentication and file sync with Google Drive
"""

import os
import json
import webbrowser
import hashlib
import base64
import secrets
import http.server
import socketserver
import threading
import urllib.parse
from pathlib import Path
from typing import Optional, Tuple, Callable
from dataclasses import dataclass

import requests
from dotenv import load_dotenv

# Load environment variables from .env file
# Search for .env in current directory and parent directories
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()  # Fallback to default behavior

# Google OAuth configuration
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_DRIVE_API = "https://www.googleapis.com/drive/v3"
GOOGLE_UPLOAD_API = "https://www.googleapis.com/upload/drive/v3"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

# Scopes for Google Drive access
SCOPES = [
    "https://www.googleapis.com/auth/drive.file",  # Only files created by this app
    "https://www.googleapis.com/auth/userinfo.email",  # User email for identification
    "https://www.googleapis.com/auth/userinfo.profile",  # User profile info
]

# Local callback port for OAuth
OAUTH_CALLBACK_PORT = 58392
REDIRECT_URI = f"http://localhost:{OAUTH_CALLBACK_PORT}/callback"


@dataclass
class GoogleDriveCredentials:
    """Stores Google Drive OAuth credentials."""
    access_token: str
    refresh_token: str
    expires_at: float
    email: Optional[str] = None
    name: Optional[str] = None
    picture: Optional[str] = None


class OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    """HTTP handler for OAuth callback."""
    
    auth_code: Optional[str] = None
    error: Optional[str] = None
    
    def log_message(self, format, *args):
        """Suppress logging."""
        pass
    
    def do_GET(self):
        """Handle OAuth callback GET request."""
        parsed = urllib.parse.urlparse(self.path)
        
        if parsed.path == "/callback":
            params = urllib.parse.parse_qs(parsed.query)
            
            if "code" in params:
                OAuthCallbackHandler.auth_code = params["code"][0]
                self._send_success_response()
            elif "error" in params:
                OAuthCallbackHandler.error = params.get("error_description", ["Authentication failed"])[0]
                self._send_error_response(OAuthCallbackHandler.error)
            else:
                OAuthCallbackHandler.error = "No authorization code received"
                self._send_error_response(OAuthCallbackHandler.error)
        else:
            self.send_error(404)
    
    def _send_success_response(self):
        """Send success response HTML."""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>VaultKeeper - Connected</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: #1a1d21;
                    color: #fff;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }
                .container {
                    text-align: center;
                    padding: 40px;
                    background: #242830;
                    border-radius: 16px;
                    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
                }
                .icon {
                    width: 64px;
                    height: 64px;
                    background: #4ade80;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0 auto 20px;
                }
                .icon svg {
                    width: 32px;
                    height: 32px;
                }
                h1 { margin: 0 0 10px; color: #4ade80; }
                p { color: #9ca3af; margin: 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                </div>
                <h1>Connected!</h1>
                <p>You can close this window and return to VaultKeeper.</p>
            </div>
        </body>
        </html>
        """
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def _send_error_response(self, error: str):
        """Send error response HTML."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>VaultKeeper - Error</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: #1a1d21;
                    color: #fff;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }}
                .container {{
                    text-align: center;
                    padding: 40px;
                    background: #242830;
                    border-radius: 16px;
                    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
                }}
                .icon {{
                    width: 64px;
                    height: 64px;
                    background: #ef4444;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0 auto 20px;
                }}
                .icon svg {{
                    width: 32px;
                    height: 32px;
                }}
                h1 {{ margin: 0 0 10px; color: #ef4444; }}
                p {{ color: #9ca3af; margin: 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </div>
                <h1>Connection Failed</h1>
                <p>{error}</p>
            </div>
        </body>
        </html>
        """
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))


class GoogleDriveManager:
    """Manages Google Drive OAuth and file operations."""
    
    # Class-level callbacks for sync status (to avoid circular imports)
    _on_sync_start_callbacks = []
    _on_sync_end_callbacks = []
    
    def __init__(self):
        self.client_id = os.getenv("GDRIVE_CLIENT_ID")
        self.client_secret = os.getenv("GDRIVE_CLIENT_SECRET")
        self.project_id = os.getenv("GDRIVE_PROJECT_ID")
        self.credentials: Optional[GoogleDriveCredentials] = None
        self._credentials_file = self._get_credentials_path()
        self._load_credentials()
        
        # PKCE challenge for secure OAuth
        self._code_verifier: Optional[str] = None
        self._code_challenge: Optional[str] = None
        
        # Sync state
        self._is_syncing = False
    
    @classmethod
    def on_sync_start(cls, callback):
        """Register a callback for when sync starts."""
        cls._on_sync_start_callbacks.append(callback)
    
    @classmethod
    def on_sync_end(cls, callback):
        """Register a callback for when sync ends."""
        cls._on_sync_end_callbacks.append(callback)
    
    @classmethod
    def _notify_sync_start(cls):
        """Notify all callbacks that sync has started."""
        for callback in cls._on_sync_start_callbacks:
            try:
                callback()
            except Exception as e:
                print(f"Error in sync start callback: {e}")
    
    @classmethod
    def _notify_sync_end(cls, success: bool = True, error: str = None):
        """Notify all callbacks that sync has ended."""
        for callback in cls._on_sync_end_callbacks:
            try:
                callback(success, error)
            except Exception as e:
                print(f"Error in sync end callback: {e}")
    
    @property
    def is_syncing(self) -> bool:
        """Check if a sync is currently in progress."""
        return self._is_syncing
    
    def _get_credentials_path(self) -> Path:
        """Get the path to store OAuth credentials."""
        app_data = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming"))
        vk_dir = app_data / "VaultKeeper"
        vk_dir.mkdir(parents=True, exist_ok=True)
        return vk_dir / "gdrive_credentials.json"
    
    def is_configured(self) -> bool:
        """Check if Google Drive is properly configured with API credentials."""
        return bool(self.client_id and self.client_secret)
    
    def is_connected(self) -> bool:
        """Check if user is connected to Google Drive."""
        return self.credentials is not None and self.credentials.access_token is not None
    
    def get_user_info(self) -> Optional[dict]:
        """Get connected user info."""
        if not self.credentials:
            return None
        return {
            "email": self.credentials.email,
            "name": self.credentials.name,
            "picture": self.credentials.picture,
        }
    
    def get_storage_info(self) -> Optional[dict]:
        """Get Google Drive storage quota information.
        
        Returns:
            dict with 'used', 'total', and 'percent' keys, or None if not connected
        """
        if not self.is_connected():
            return None
        
        try:
            if not self._ensure_valid_token():
                return None
            
            headers = {"Authorization": f"Bearer {self.credentials.access_token}"}
            
            # Request storage quota from Drive API
            response = requests.get(
                f"{GOOGLE_DRIVE_API}/about",
                headers=headers,
                params={"fields": "storageQuota"}
            )
            
            if response.ok:
                data = response.json()
                quota = data.get("storageQuota", {})
                
                # Get values (in bytes as strings)
                used = int(quota.get("usage", 0))
                total = int(quota.get("limit", 0))  # 0 means unlimited
                
                # Calculate percentage
                if total > 0:
                    percent = (used / total) * 100
                else:
                    percent = 0  # Unlimited storage
                
                return {
                    "used": used,
                    "total": total,
                    "percent": percent,
                    "unlimited": total == 0
                }
        except Exception as e:
            print(f"Error getting storage info: {e}")
        
        return None
    
    def _generate_pkce_challenge(self) -> Tuple[str, str]:
        """Generate PKCE code verifier and challenge."""
        # Generate random code verifier
        code_verifier = secrets.token_urlsafe(64)[:128]
        
        # Create SHA256 hash and base64url encode it
        code_challenge = hashlib.sha256(code_verifier.encode()).digest()
        code_challenge = base64.urlsafe_b64encode(code_challenge).decode().rstrip("=")
        
        return code_verifier, code_challenge
    
    def _load_credentials(self) -> None:
        """Load saved credentials from file."""
        try:
            if self._credentials_file.exists():
                with open(self._credentials_file, "r") as f:
                    data = json.load(f)
                    self.credentials = GoogleDriveCredentials(**data)
        except Exception as e:
            print(f"Failed to load Google Drive credentials: {e}")
            self.credentials = None
    
    def _save_credentials(self) -> None:
        """Save credentials to file."""
        try:
            if self.credentials:
                with open(self._credentials_file, "w") as f:
                    json.dump({
                        "access_token": self.credentials.access_token,
                        "refresh_token": self.credentials.refresh_token,
                        "expires_at": self.credentials.expires_at,
                        "email": self.credentials.email,
                        "name": self.credentials.name,
                        "picture": self.credentials.picture,
                    }, f)
        except Exception as e:
            print(f"Failed to save Google Drive credentials: {e}")
    
    def _clear_credentials(self) -> None:
        """Clear saved credentials."""
        self.credentials = None
        try:
            if self._credentials_file.exists():
                self._credentials_file.unlink()
        except Exception as e:
            print(f"Failed to delete credentials file: {e}")
    
    def get_auth_url(self) -> str:
        """Generate the OAuth authorization URL."""
        self._code_verifier, self._code_challenge = self._generate_pkce_challenge()
        
        params = {
            "client_id": self.client_id,
            "redirect_uri": REDIRECT_URI,
            "response_type": "code",
            "scope": " ".join(SCOPES),
            "access_type": "offline",
            "prompt": "consent",
            "code_challenge": self._code_challenge,
            "code_challenge_method": "S256",
        }
        
        return f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"
    
    def authenticate(self, on_success: Optional[Callable] = None, on_error: Optional[Callable[[str], None]] = None) -> None:
        """Start OAuth flow and authenticate user."""
        if not self.is_configured():
            if on_error:
                on_error("Google Drive API credentials not configured")
            return
        
        # Reset callback handler state
        OAuthCallbackHandler.auth_code = None
        OAuthCallbackHandler.error = None
        
        # Start local server for callback
        server = socketserver.TCPServer(("localhost", OAUTH_CALLBACK_PORT), OAuthCallbackHandler)
        server.timeout = 120  # 2 minute timeout
        
        def run_server():
            try:
                server.handle_request()
            finally:
                server.server_close()
            
            # Process result
            if OAuthCallbackHandler.auth_code:
                try:
                    self._exchange_code(OAuthCallbackHandler.auth_code)
                    self._fetch_user_info()
                    self._save_credentials()
                    if on_success:
                        on_success()
                except Exception as e:
                    if on_error:
                        on_error(str(e))
            elif OAuthCallbackHandler.error:
                if on_error:
                    on_error(OAuthCallbackHandler.error)
        
        # Start server in background thread
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Open browser for authorization
        auth_url = self.get_auth_url()
        webbrowser.open(auth_url)
    
    def _exchange_code(self, code: str) -> None:
        """Exchange authorization code for tokens."""
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
            "code_verifier": self._code_verifier,
        }
        
        response = requests.post(GOOGLE_TOKEN_URL, data=data)
        response.raise_for_status()
        
        tokens = response.json()
        
        import time
        expires_at = time.time() + tokens.get("expires_in", 3600)
        
        self.credentials = GoogleDriveCredentials(
            access_token=tokens["access_token"],
            refresh_token=tokens.get("refresh_token", ""),
            expires_at=expires_at,
        )
    
    def _fetch_user_info(self) -> None:
        """Fetch user profile information."""
        if not self.credentials:
            return
            
        headers = {"Authorization": f"Bearer {self.credentials.access_token}"}
        response = requests.get(GOOGLE_USERINFO_URL, headers=headers)
        
        if response.ok:
            info = response.json()
            self.credentials.email = info.get("email")
            self.credentials.name = info.get("name")
            self.credentials.picture = info.get("picture")
    
    def refresh_token(self) -> bool:
        """Refresh the access token."""
        if not self.credentials or not self.credentials.refresh_token:
            return False
        
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.credentials.refresh_token,
            "grant_type": "refresh_token",
        }
        
        try:
            response = requests.post(GOOGLE_TOKEN_URL, data=data)
            response.raise_for_status()
            
            tokens = response.json()
            
            import time
            self.credentials.access_token = tokens["access_token"]
            self.credentials.expires_at = time.time() + tokens.get("expires_in", 3600)
            
            # Refresh token is not always returned
            if "refresh_token" in tokens:
                self.credentials.refresh_token = tokens["refresh_token"]
            
            self._save_credentials()
            return True
        except Exception as e:
            print(f"Failed to refresh token: {e}")
            return False
    
    def _ensure_valid_token(self) -> bool:
        """Ensure we have a valid access token."""
        if not self.credentials:
            return False
        
        import time
        if time.time() >= self.credentials.expires_at - 60:  # 1 minute buffer
            return self.refresh_token()
        
        return True
    
    def disconnect(self) -> None:
        """Disconnect from Google Drive."""
        self._clear_credentials()
    
    def _get_headers(self) -> dict:
        """Get headers with authorization."""
        if not self._ensure_valid_token():
            raise Exception("Not authenticated with Google Drive")
        return {"Authorization": f"Bearer {self.credentials.access_token}"}
    
    def _get_or_create_vault_folder(self) -> Optional[str]:
        """Get or create VaultKeeper folder in Google Drive."""
        headers = self._get_headers()
        
        # Search for existing folder
        query = "name='VaultKeeper' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        params = {"q": query, "spaces": "drive"}
        
        response = requests.get(f"{GOOGLE_DRIVE_API}/files", headers=headers, params=params)
        response.raise_for_status()
        
        files = response.json().get("files", [])
        
        if files:
            return files[0]["id"]
        
        # Create folder
        metadata = {
            "name": "VaultKeeper",
            "mimeType": "application/vnd.google-apps.folder",
        }
        
        response = requests.post(
            f"{GOOGLE_DRIVE_API}/files",
            headers={**headers, "Content-Type": "application/json"},
            json=metadata,
        )
        response.raise_for_status()
        
        return response.json()["id"]
    
    def upload_vault(self, vault_path: Path = None, progress_callback: Optional[Callable[[int], None]] = None) -> bool:
        """Upload vault file to Google Drive."""
        if vault_path is None:
            vault_path = Path.home() / '.vaultkeeper' / 'vault.db'
        
        if not vault_path.exists():
            raise FileNotFoundError(f"Vault file not found: {vault_path}")
        
        # Ensure valid token
        if not self._ensure_valid_token():
            raise Exception("Failed to refresh access token")
        
        print(f"[GDrive] Starting upload of {vault_path}")
        
        # Notify sync started
        self._is_syncing = True
        GoogleDriveManager._notify_sync_start()
        
        try:
            folder_id = self._get_or_create_vault_folder()
            if not folder_id:
                raise Exception("Failed to create VaultKeeper folder")
            
            print(f"[GDrive] Using folder ID: {folder_id}")
            
            headers = self._get_headers()
            
            # Check if file exists
            query = f"name='{vault_path.name}' and '{folder_id}' in parents and trashed=false"
            params = {"q": query}
            
            response = requests.get(f"{GOOGLE_DRIVE_API}/files", headers=headers, params=params)
            response.raise_for_status()
            
            files = response.json().get("files", [])
            
            with open(vault_path, "rb") as f:
                file_content = f.read()
            
            if files:
                # Update existing file
                file_id = files[0]["id"]
                response = requests.patch(
                    f"{GOOGLE_UPLOAD_API}/files/{file_id}?uploadType=media",
                    headers={**headers, "Content-Type": "application/octet-stream"},
                    data=file_content,
                )
            else:
                # Create new file
                metadata = {
                    "name": vault_path.name,
                    "parents": [folder_id],
                }
                
                # Multipart upload
                boundary = "===vaultkeeper==="
                body = (
                    f"--{boundary}\r\n"
                    f'Content-Type: application/json; charset=UTF-8\r\n\r\n'
                    f'{json.dumps(metadata)}\r\n'
                    f"--{boundary}\r\n"
                    f"Content-Type: application/octet-stream\r\n\r\n"
                ).encode() + file_content + f"\r\n--{boundary}--".encode()
                
                response = requests.post(
                    f"{GOOGLE_UPLOAD_API}/files?uploadType=multipart",
                    headers={**headers, "Content-Type": f"multipart/related; boundary={boundary}"},
                    data=body,
                )
            
            response.raise_for_status()
            
            # Notify sync completed successfully
            self._is_syncing = False
            GoogleDriveManager._notify_sync_end(success=True)
            return True
            
        except Exception as e:
            # Notify sync failed
            self._is_syncing = False
            GoogleDriveManager._notify_sync_end(success=False, error=str(e))
            raise
    
    def download_vault(self, vault_path: Path, progress_callback: Optional[Callable[[int], None]] = None) -> bool:
        """Download vault file from Google Drive."""
        folder_id = self._get_or_create_vault_folder()
        if not folder_id:
            raise Exception("VaultKeeper folder not found")
        
        headers = self._get_headers()
        
        # Find vault file
        query = f"name='{vault_path.name}' and '{folder_id}' in parents and trashed=false"
        params = {"q": query}
        
        response = requests.get(f"{GOOGLE_DRIVE_API}/files", headers=headers, params=params)
        response.raise_for_status()
        
        files = response.json().get("files", [])
        
        if not files:
            raise FileNotFoundError("Vault file not found in Google Drive")
        
        file_id = files[0]["id"]
        
        response = requests.get(
            f"{GOOGLE_DRIVE_API}/files/{file_id}?alt=media",
            headers=headers,
        )
        response.raise_for_status()
        
        # Backup existing file
        if vault_path.exists():
            backup_path = vault_path.with_suffix(".backup")
            vault_path.rename(backup_path)
        
        with open(vault_path, "wb") as f:
            f.write(response.content)
        
        return True


# Singleton instance
_gdrive_manager: Optional[GoogleDriveManager] = None


def get_gdrive_manager() -> GoogleDriveManager:
    """Get the singleton GoogleDriveManager instance."""
    global _gdrive_manager
    if _gdrive_manager is None:
        _gdrive_manager = GoogleDriveManager()
    return _gdrive_manager
