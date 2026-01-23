
import os
import sys

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

env_path = Path(__file__).parent.parent.parent / ".env"

if getattr(sys, 'frozen', False):
    # Running in a PyInstaller bundle
    # In OneDir mode, datas are often in _internal (sys._MEIPASS)
    # Check sys._MEIPASS first, then executable directory as fallback
    if hasattr(sys, '_MEIPASS'):
        env_path = Path(sys._MEIPASS) / ".env"
    
    # Fallback: check executable directory if not found in _MEIPASS
    if not env_path.exists():
        env_path = Path(sys.executable).parent / ".env"

if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

GOOGLE_DRIVE_API = "https://www.googleapis.com/drive/v3"

GOOGLE_UPLOAD_API = "https://www.googleapis.com/upload/drive/v3"

GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

SCOPES = [

    "https://www.googleapis.com/auth/drive.file",

    "https://www.googleapis.com/auth/userinfo.email",

    "https://www.googleapis.com/auth/userinfo.profile",

]

OAUTH_CALLBACK_PORT = 58392

REDIRECT_URI = f"http://localhost:{OAUTH_CALLBACK_PORT}/callback"

@dataclass

class GoogleDriveCredentials:

    access_token: str

    refresh_token: str

    expires_at: float

    email: Optional[str] = None

    name: Optional[str] = None

    picture: Optional[str] = None

class OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):

    auth_code: Optional[str] = None

    error: Optional[str] = None

    def log_message(self, format, *args):

        pass

    def do_GET(self):

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

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>VaultKeeper - Error</title>
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
                    background: #ef4444;
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
                h1 {  margin: 0 0 10px; color: #ef4444; }
                p {  color: #9ca3af; margin: 0; }
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

    _on_sync_start_callbacks = []

    _on_sync_end_callbacks = []

    def __init__(self):

        self.client_id = os.getenv("GDRIVE_CLIENT_ID")

        self.client_secret = os.getenv("GDRIVE_CLIENT_SECRET")

        self.project_id = os.getenv("GDRIVE_PROJECT_ID")

        self.credentials: Optional[GoogleDriveCredentials] = None

        self._credentials_file = self._get_credentials_path()

        self._load_credentials()

        self._code_verifier: Optional[str] = None

        self._code_challenge: Optional[str] = None

        self._is_syncing = False

    @classmethod

    def on_sync_start(cls, callback):

        cls._on_sync_start_callbacks.append(callback)

    @classmethod

    def on_sync_end(cls, callback):

        cls._on_sync_end_callbacks.append(callback)

    @classmethod

    def _notify_sync_start(cls):

        for callback in cls._on_sync_start_callbacks:

            try:

                callback()

            except Exception as e:

                print(f"Error in sync start callback: {e}")

    @classmethod

    def _notify_sync_end(cls, success: bool = True, error: str = None):

        for callback in cls._on_sync_end_callbacks:

            try:

                callback(success, error)

            except Exception as e:

                print(f"Error in sync end callback: {e}")

    @property

    def is_syncing(self) -> bool:

        return self._is_syncing

    def _get_credentials_path(self) -> Path:

        app_data = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming"))

        vk_dir = app_data / "VaultKeeper"

        vk_dir.mkdir(parents=True, exist_ok=True)

        return vk_dir / "gdrive_credentials.json"

    def is_configured(self) -> bool:

        return bool(self.client_id and self.client_secret)

    def is_connected(self) -> bool:

        return self.credentials is not None and self.credentials.access_token is not None

    def get_user_info(self) -> Optional[dict]:

        if not self.credentials:

            return None

        return {

            "email": self.credentials.email,

            "name": self.credentials.name,

            "picture": self.credentials.picture,

        }

    def get_storage_info(self) -> Optional[dict]:

        if not self.is_connected():

            return None

        try:

            if not self._ensure_valid_token():

                return None

            headers = {"Authorization": f"Bearer {self.credentials.access_token}"}

            response = requests.get(

                f"{GOOGLE_DRIVE_API}/about",

                headers=headers,

                params={"fields": "storageQuota"}

            )

            if response.ok:

                data = response.json()

                quota = data.get("storageQuota", {})

                used = int(quota.get("usage", 0))

                total = int(quota.get("limit", 0))

                if total > 0:

                    percent = (used / total) * 100

                else:

                    percent = 0

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

        code_verifier = secrets.token_urlsafe(64)[:128]

        code_challenge = hashlib.sha256(code_verifier.encode()).digest()

        code_challenge = base64.urlsafe_b64encode(code_challenge).decode().rstrip("=")

        return code_verifier, code_challenge

    def _load_credentials(self) -> None:

        try:

            if self._credentials_file.exists():

                with open(self._credentials_file, "r") as f:

                    data = json.load(f)

                    self.credentials = GoogleDriveCredentials(**data)

        except Exception as e:

            print(f"Failed to load Google Drive credentials: {e}")

            self.credentials = None

    def _save_credentials(self) -> None:

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

        self.credentials = None

        try:

            if self._credentials_file.exists():

                self._credentials_file.unlink()

        except Exception as e:

            print(f"Failed to delete credentials file: {e}")

    def get_auth_url(self) -> str:

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

        if not self.is_configured():

            if on_error:

                on_error("Google Drive API credentials not configured")

            return

        OAuthCallbackHandler.auth_code = None

        OAuthCallbackHandler.error = None

        server = socketserver.TCPServer(("localhost", OAUTH_CALLBACK_PORT), OAuthCallbackHandler)

        server.timeout = 120

        def run_server():

            try:

                server.handle_request()

            finally:

                server.server_close()

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

        server_thread = threading.Thread(target=run_server, daemon=True)

        server_thread.start()

        auth_url = self.get_auth_url()

        webbrowser.open(auth_url)

    def _exchange_code(self, code: str) -> None:

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

            if "refresh_token" in tokens:

                self.credentials.refresh_token = tokens["refresh_token"]

            self._save_credentials()

            return True

        except Exception as e:

            print(f"Failed to refresh token: {e}")

            return False

    def _ensure_valid_token(self) -> bool:

        if not self.credentials:

            return False

        import time

        if time.time() >= self.credentials.expires_at - 60:

            return self.refresh_token()

        return True

    def disconnect(self) -> None:

        self._clear_credentials()

    def _get_headers(self) -> dict:

        if not self._ensure_valid_token():

            raise Exception("Not authenticated with Google Drive")

        return {"Authorization": f"Bearer {self.credentials.access_token}"}

    def _get_or_create_vault_folder(self) -> Optional[str]:

        headers = self._get_headers()

        query = "name='VaultKeeper' and mimeType='application/vnd.google-apps.folder' and trashed=false"

        params = {"q": query, "spaces": "drive"}

        response = requests.get(f"{GOOGLE_DRIVE_API}/files", headers=headers, params=params)

        response.raise_for_status()

        files = response.json().get("files", [])

        if files:

            return files[0]["id"]

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

        if vault_path is None:

            vault_path = Path.home() / '.vaultkeeper' / 'vault.db'

        if not vault_path.exists():

            raise FileNotFoundError(f"Vault file not found: {vault_path}")

        if not self._ensure_valid_token():

            raise Exception("Failed to refresh access token")

        print(f"[GDrive] Starting upload of {vault_path}")

        self._is_syncing = True

        GoogleDriveManager._notify_sync_start()

        try:

            folder_id = self._get_or_create_vault_folder()

            if not folder_id:

                raise Exception("Failed to create VaultKeeper folder")

            print(f"[GDrive] Using folder ID: {folder_id}")

            headers = self._get_headers()

            query = f"name='{vault_path.name}' and '{folder_id}' in parents and trashed=false"

            params = {"q": query}

            response = requests.get(f"{GOOGLE_DRIVE_API}/files", headers=headers, params=params)

            response.raise_for_status()

            files = response.json().get("files", [])

            with open(vault_path, "rb") as f:

                file_content = f.read()

            if files:

                file_id = files[0]["id"]

                response = requests.patch(

                    f"{GOOGLE_UPLOAD_API}/files/{file_id}?uploadType=media",

                    headers={**headers, "Content-Type": "application/octet-stream"},

                    data=file_content,

                )

            else:

                metadata = {

                    "name": vault_path.name,

                    "parents": [folder_id],

                }

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

            self._is_syncing = False

            GoogleDriveManager._notify_sync_end(success=True)

            return True

        except Exception as e:

            self._is_syncing = False

            GoogleDriveManager._notify_sync_end(success=False, error=str(e))

            raise

    def download_vault(self, vault_path: Path, progress_callback: Optional[Callable[[int], None]] = None) -> bool:

        folder_id = self._get_or_create_vault_folder()

        if not folder_id:

            raise Exception("VaultKeeper folder not found")

        headers = self._get_headers()

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

        if vault_path.exists():

            backup_path = vault_path.with_suffix(".backup")

            vault_path.rename(backup_path)

        with open(vault_path, "wb") as f:

            f.write(response.content)

        return True

    def merge_vaults(self, vault_path: Path = None, master_password: str = None, 
                     progress_callback: Optional[Callable[[int, str], None]] = None) -> dict:
        """
        Merge local vault with cloud vault intelligently.
        
        - Credentials that exist only locally are kept
        - Credentials that exist only in cloud are added locally
        - Credentials that exist in both are merged (most recent wins)
        - After merge, uploads the combined vault to cloud
        
        Returns a dict with merge statistics.
        """
        import tempfile
        import sqlite3
        import shutil
        from datetime import datetime
        
        if vault_path is None:
            vault_path = Path.home() / '.vaultkeeper' / 'vault.db'
        
        stats = {
            "local_only": 0,
            "cloud_only": 0,
            "updated_from_cloud": 0,
            "updated_from_local": 0,
            "unchanged": 0,
            "total_after_merge": 0
        }
        
        def report_progress(percent: int, message: str):
            if progress_callback:
                progress_callback(percent, message)
            print(f"[Merge] {percent}% - {message}")
        
        report_progress(5, "Starting merge...")
        
        # Step 1: Download cloud vault to temp file
        temp_dir = Path(tempfile.mkdtemp())
        cloud_vault_path = temp_dir / "cloud_vault.db"
        
        try:
            report_progress(10, "Downloading vault from cloud...")
            
            # Check if cloud vault exists
            folder_id = self._get_or_create_vault_folder()
            if not folder_id:
                raise Exception("Could not access VaultKeeper folder in Google Drive")
            
            headers = self._get_headers()
            query = f"name='vault.db' and '{folder_id}' in parents and trashed=false"
            params = {"q": query}
            
            response = requests.get(f"{GOOGLE_DRIVE_API}/files", headers=headers, params=params)
            response.raise_for_status()
            files = response.json().get("files", [])
            
            cloud_exists = len(files) > 0
            local_exists = vault_path.exists()
            
            if not cloud_exists and not local_exists:
                raise Exception("No vault found locally or in cloud")
            
            if not cloud_exists:
                # Only local vault exists - just upload it
                report_progress(50, "No cloud vault found. Uploading local vault...")
                self.upload_vault(vault_path)
                stats["local_only"] = -1  # Signal that we only uploaded
                report_progress(100, "Upload complete!")
                return stats
            
            if not local_exists:
                # Only cloud vault exists - just download it
                report_progress(50, "No local vault found. Downloading cloud vault...")
                self.download_vault(vault_path)
                stats["cloud_only"] = -1  # Signal that we only downloaded
                report_progress(100, "Download complete!")
                return stats
            
            # Both exist - need to merge
            report_progress(20, "Downloading cloud vault for merge...")
            
            file_id = files[0]["id"]
            response = requests.get(
                f"{GOOGLE_DRIVE_API}/files/{file_id}?alt=media",
                headers=headers
            )
            response.raise_for_status()
            
            with open(cloud_vault_path, "wb") as f:
                f.write(response.content)
            
            report_progress(30, "Reading credentials from both vaults...")
            
            # Step 2: Read credentials from both vaults
            def read_credentials_raw(db_path: Path) -> list:
                """Read raw encrypted credentials from database."""
                with sqlite3.connect(db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM vault ORDER BY id')
                    return [dict(row) for row in cursor.fetchall()]
            
            def read_folders_raw(db_path: Path) -> list:
                """Read folders from database."""
                with sqlite3.connect(db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    try:
                        cursor.execute('SELECT * FROM folders ORDER BY id')
                        return [dict(row) for row in cursor.fetchall()]
                    except sqlite3.OperationalError:
                        return []
            
            def read_secure_notes_raw(db_path: Path) -> list:
                """Read raw encrypted secure notes from database."""
                with sqlite3.connect(db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    try:
                        cursor.execute('SELECT * FROM secure_notes ORDER BY id')
                        return [dict(row) for row in cursor.fetchall()]
                    except sqlite3.OperationalError:
                        return []
            
            def read_credit_cards_raw(db_path: Path) -> list:
                """Read raw encrypted credit cards from database."""
                with sqlite3.connect(db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    try:
                        cursor.execute('SELECT * FROM credit_cards ORDER BY id')
                        return [dict(row) for row in cursor.fetchall()]
                    except sqlite3.OperationalError:
                        return []
            
            local_creds = read_credentials_raw(vault_path)
            cloud_creds = read_credentials_raw(cloud_vault_path)
            local_folders = read_folders_raw(vault_path)
            cloud_folders = read_folders_raw(cloud_vault_path)
            
            # NOTE: Secure notes and credit cards are NOT synced automatically due to encryption issues.
            # Use Settings > Data Management to manually export/import notes and cards between devices.
            
            report_progress(40, f"Found {len(local_creds)} local and {len(cloud_creds)} cloud credentials...")
            
            # Step 3: Create merge key (domain + username + encrypted password as unique identifier)
            # We'll use domain + username as the key since password is encrypted differently
            def get_merge_key(cred: dict) -> str:
                return f"{cred.get('domain', '')}|{cred.get('username', '')}"
            
            # Index credentials by merge key
            local_by_key = {get_merge_key(c): c for c in local_creds}
            cloud_by_key = {get_merge_key(c): c for c in cloud_creds}
            
            # Step 4: Merge credentials
            merged_creds = []
            
            # Process all unique keys
            all_keys = set(local_by_key.keys()) | set(cloud_by_key.keys())
            
            for key in all_keys:
                local_cred = local_by_key.get(key)
                cloud_cred = cloud_by_key.get(key)
                
                if local_cred and not cloud_cred:
                    # Only in local
                    merged_creds.append(local_cred)
                    stats["local_only"] += 1
                elif cloud_cred and not local_cred:
                    # Only in cloud
                    merged_creds.append(cloud_cred)
                    stats["cloud_only"] += 1
                else:
                    # In both - compare updated_at timestamps
                    local_time = local_cred.get('updated_at') or local_cred.get('created_at') or ''
                    cloud_time = cloud_cred.get('updated_at') or cloud_cred.get('created_at') or ''
                    
                    if local_time >= cloud_time:
                        merged_creds.append(local_cred)
                        if local_time > cloud_time:
                            stats["updated_from_local"] += 1
                        else:
                            stats["unchanged"] += 1
                    else:
                        merged_creds.append(cloud_cred)
                        stats["updated_from_cloud"] += 1
            
            stats["total_after_merge"] = len(merged_creds)
            
            report_progress(60, f"Merged to {len(merged_creds)} credentials. Updating local vault...")
            
            # Step 5: Backup local vault
            backup_path = vault_path.with_suffix('.pre_merge.backup')
            shutil.copy2(vault_path, backup_path)
            
            # Step 6: Clear local vault and insert merged credentials
            with sqlite3.connect(vault_path) as conn:
                cursor = conn.cursor()
                
                # Clear existing credentials
                cursor.execute('DELETE FROM vault')
                
                # Insert merged credentials
                for cred in merged_creds:
                    cursor.execute('''
                        INSERT INTO vault (domain, username, password, notes, totp_secret, 
                                          backup_codes, is_favorite, folder_id, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        cred.get('domain'),
                        cred.get('username'),
                        cred.get('password'),
                        cred.get('notes'),
                        cred.get('totp_secret'),
                        cred.get('backup_codes'),
                        cred.get('is_favorite', 0),
                        cred.get('folder_id'),
                        cred.get('created_at'),
                        cred.get('updated_at')
                    ))
                
                # Merge folders too
                existing_folder_names = set()
                cursor.execute('SELECT name FROM folders')
                for row in cursor.fetchall():
                    existing_folder_names.add(row[0])
                
                for folder in cloud_folders:
                    if folder.get('name') not in existing_folder_names:
                        cursor.execute('''
                            INSERT INTO folders (name, icon, created_at)
                            VALUES (?, ?, ?)
                        ''', (
                            folder.get('name'),
                            folder.get('icon', 'folder'),
                            folder.get('created_at')
                        ))
                
                conn.commit()
            
            report_progress(80, "Uploading merged vault to cloud...")
            
            # Step 7: Upload merged vault to cloud
            self.upload_vault(vault_path)
            
            report_progress(100, "Merge complete!")
            
            return stats
            
        finally:
            # Cleanup temp directory
            try:
                shutil.rmtree(temp_dir)
            except:
                pass

_gdrive_manager: Optional[GoogleDriveManager] = None

def get_gdrive_manager() -> GoogleDriveManager:

    global _gdrive_manager

    if _gdrive_manager is None:

        _gdrive_manager = GoogleDriveManager()

    return _gdrive_manager
