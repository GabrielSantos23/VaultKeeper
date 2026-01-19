
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

env_path = Path(__file__).parent.parent.parent / ".env"

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

_gdrive_manager: Optional[GoogleDriveManager] = None

def get_gdrive_manager() -> GoogleDriveManager:

    global _gdrive_manager

    if _gdrive_manager is None:

        _gdrive_manager = GoogleDriveManager()

    return _gdrive_manager
