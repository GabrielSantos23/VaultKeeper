
import os
import json
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

PORT = 12121  # Porta personalizada para o VaultKeeper

class VaultRequestHandler(BaseHTTPRequestHandler):
    vault_path: Path = None

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def do_GET(self):
        # Endpoint de descoberta
        if self.path == '/status':
            if not self.vault_path or not self.vault_path.exists():
                return self._send_json({'status': 'error', 'message': 'Vault not initialized'}, 500)
            
            stats = self.vault_path.stat()
            self._send_json({
                'app': 'VaultKeeper',
                'status': 'ready',
                'modified_at': stats.st_mtime,
                'size': stats.st_size
            })
            return

        # Download do Banco de Dados
        if self.path == '/vault.db':
            if not self.vault_path or not self.vault_path.exists():
                self.send_error(404, "Vault file not found")
                return

            try:
                stats = self.vault_path.stat()
                with open(self.vault_path, 'rb') as f:
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/x-sqlite3')
                    self.send_header('Content-Length', str(stats.st_size))
                    self.end_headers()
                    self.wfile.write(f.read())
                logger.info("Sent vault.db to client")
            except Exception as e:
                logger.error(f"Error serving vault: {e}")
                self.send_error(500, f"Internal Error: {e}")
            return

        self.send_error(404)

    def do_POST(self):
        # Upload do Banco de Dados (Mobile -> PC)
        if self.path == '/vault.db':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            if not self.vault_path:
                self.send_error(500, "Vault path not configured")
                return

            try:
                # Backup before overwrite (Safety first)
                backup_path = self.vault_path.with_suffix('.db.bak')
                if self.vault_path.exists():
                    import shutil
                    shutil.copy2(self.vault_path, backup_path)

                with open(self.vault_path, 'wb') as f:
                    f.write(post_data)
                
                logger.info("Received new vault.db from client")
                self._send_json({'status': 'success', 'message': 'Vault updated'})
            except Exception as e:
                logger.error(f"Error saving vault: {e}")
                self._send_json({'status': 'error', 'message': str(e)}, 500)
            return

        self.send_error(404)

    def log_message(self, format, *args):
        # Silenciar logs do HTTP server no console principal
        pass

class LocalSyncServer:
    def __init__(self, vault_path: Path):
        self.server: Optional[HTTPServer] = None
        self.thread: Optional[threading.Thread] = None
        self.vault_path = vault_path
        # Configurar o handler globalmente (limitação do TCPServer simples)
        VaultRequestHandler.vault_path = vault_path

    def start(self):
        if self.server:
            return

        def run():
            try:
                logger.info(f"Starting Local P2P Server on port {PORT}...")
                self.server = HTTPServer(('0.0.0.0', PORT), VaultRequestHandler)
                self.server.serve_forever()
            except Exception as e:
                logger.error(f"Failed to start local server: {e}")

        self.thread = threading.Thread(target=run, daemon=True)
        self.thread.start()

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
