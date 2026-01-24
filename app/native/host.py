
import sys
import json
import struct
import logging
from typing import Optional, Dict, Any
from pathlib import Path

# Redirect stdout to stderr globally and immediately to prevent ANY print() 
# from breaking Native Messaging protocol.
# This must be done before any other imports that might print.
# We save the original stdout to send actual messages to the extension.
STDOUT = sys.stdout
sys.stdout = sys.stderr

if not getattr(sys, 'frozen', False):
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.vault import VaultManager
from app.core.auth import AuthManager
from app.core.totp import TOTPManager, get_totp_code, is_valid_totp_secret

log_path = Path.home() / '.vaultkeeper' / 'native_host.log'
log_path.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=str(log_path),
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NativeMessagingHost:

    def __init__(self):
        self.auth = AuthManager()
        self.vault = VaultManager(auth=self.auth)
        logger.info("NativeMessagingHost initialized")

    def read_message(self) -> Optional[Dict[str, Any]]:
        try:
            # We must read from stdin.buffer for binary length
            length_bytes = sys.stdin.buffer.read(4)
            if len(length_bytes) != 4:
                if len(length_bytes) == 0:
                     # Normal closure
                     return None
                logger.error(f"Failed to read message length: got {len(length_bytes)} bytes")
                return None
            
            message_length = struct.unpack('@I', length_bytes)[0]
            logger.debug(f"Reading message of length {message_length}")
            
            message_bytes = sys.stdin.buffer.read(message_length)
            if len(message_bytes) != message_length:
                logger.error(f"Message truncated: expected {message_length}, got {len(message_bytes)}")
                return None
            
            message = json.loads(message_bytes.decode('utf-8'))
            logger.debug(f"Received message: {message.get('action', 'unknown')}")
            return message
        except Exception as e:
            logger.error(f"Error reading message: {e}")
            return None

    def send_message(self, message: Dict[str, Any]):
        try:
            message_bytes = json.dumps(message).encode('utf-8')
            length_bytes = struct.pack('@I', len(message_bytes))
            
            # Write to the SAVED stdout (the actual output stream to the browser)
            STDOUT.buffer.write(length_bytes)
            STDOUT.buffer.write(message_bytes)
            STDOUT.buffer.flush()
            
            logger.debug(f"Sent message: {message.get('success', message.get('error', 'unknown'))}")
        except Exception as e:
            logger.error(f"Error sending message: {e}")

    def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        action = message.get('action')
        logger.info(f"Handling action: {action}")
        try:
            if action == 'ping':
                return self._handle_ping()
            elif action == 'status':
                return self._handle_status()
            elif action == 'unlock':
                return self._handle_unlock(message)
            elif action == 'lock':
                return self._handle_lock()
            elif action == 'get_credentials':
                return self._handle_get_credentials(message)
            elif action == 'check_credentials':
                return self._handle_check_credentials(message)
            elif action == 'save_credentials':
                return self._handle_save_credentials(message)
            elif action == 'update_credentials':
                return self._handle_save_credentials(message)
            elif action == 'delete_credentials':
                return self._handle_delete_credentials(message)
            elif action == 'get_all_credentials':
                return self._handle_get_all_credentials()
            elif action == 'search':
                return self._handle_search(message)
            elif action == 'get_totp':
                return self._handle_get_totp(message)
            elif action == 'get_all_credit_cards':
                return self._handle_get_all_credit_cards()
            elif action == 'save_credit_card':
                return self._handle_save_credit_card(message)
            elif action == 'delete_credit_card':
                return self._handle_delete_credit_card(message)
            elif action == 'get_all_secure_notes':
                return self._handle_get_all_secure_notes()
            elif action == 'save_secure_note':
                return self._handle_save_secure_note(message)
            elif action == 'delete_secure_note':
                return self._handle_delete_secure_note(message)
            else:
                return {'success': False, 'error': f'Unknown action: {action}'}
        except Exception as e:
            logger.error(f"Error handling action {action}: {e}")
            return {'success': False, 'error': str(e)}

    def _handle_ping(self) -> Dict[str, Any]:
        return {'success': True, 'message': 'pong', 'version': '1.0.0'}

    def _handle_status(self) -> Dict[str, Any]:
        return {
            'success': True,
            'unlocked': self.auth.is_unlocked,
            'first_run': self.auth.is_first_run(),
            'credential_count': self.vault.get_credential_count() if self.auth.is_unlocked else 0
        }

    def _handle_unlock(self, message: Dict[str, Any]) -> Dict[str, Any]:
        password = message.get('password')
        if not password:
            return {'success': False, 'error': 'Password required'}
        try:
            if self.auth.is_first_run():
                self.auth.create_master_password(password)
                self.vault.crypto.derive_key(password)
                return {'success': True, 'message': 'Master password created'}
            self.vault.unlock(password)
            return {'success': True, 'message': 'Vault unlocked'}
        except ValueError as e:
            return {'success': False, 'error': str(e)}

    def _handle_lock(self) -> Dict[str, Any]:
        self.vault.lock()
        return {'success': True, 'message': 'Vault locked'}

    def _handle_get_credentials(self, message: Dict[str, Any]) -> Dict[str, Any]:
        if not self.auth.is_unlocked:
            return {'success': False, 'error': 'Vault is locked', 'locked': True}
        domain = message.get('domain')
        if not domain:
            return {'success': False, 'error': 'Domain required'}
        credentials = self.vault.get_credentials_by_domain(domain)
        if credentials:
            return {
                'success': True,
                'credentials': [cred.to_dict() for cred in credentials]
            }
        else:
            return {'success': True, 'credentials': []}

    def _handle_check_credentials(self, message: Dict[str, Any]) -> Dict[str, Any]:
        domain = message.get('domain')
        if not domain:
            return {'success': False, 'error': 'Domain required'}
        if self.auth.is_unlocked:
            credentials = self.vault.get_credentials_by_domain(domain)
        else:
            credentials = self.vault.get_basic_credentials_by_domain(domain)
        return {
            'success': True,
            'credentials': [cred.to_dict() for cred in credentials],
            'locked': not self.auth.is_unlocked
        }

    def _handle_save_credentials(self, message: Dict[str, Any]) -> Dict[str, Any]:
        if not self.auth.is_unlocked:
            return {'success': False, 'error': 'Vault is locked', 'locked': True}
        domain = message.get('domain')
        username = message.get('username')
        password = message.get('password')
        notes = message.get('notes')
        totp_secret = message.get('totp_secret')
        clear_totp = message.get('clear_totp', False)
        backup_codes = message.get('backup_codes')
        clear_backup = message.get('clear_backup', False)
        credential_id = message.get('id')

        if not all([domain, username, password]):
            return {'success': False, 'error': 'Domain, username, and password are required'}
        if totp_secret and not is_valid_totp_secret(totp_secret):
            return {'success': False, 'error': 'Invalid TOTP secret. Must be a valid base32 string.'}

        try:
            if credential_id:
                self.vault.update_credential(
                    credential_id,
                    domain=domain,
                    username=username,
                    password=password,
                    notes=notes,
                    totp_secret=totp_secret,
                    clear_totp=clear_totp,
                    backup_codes=backup_codes,
                    clear_backup=clear_backup
                )
                return {'success': True, 'message': 'Credential updated', 'id': credential_id}
            else:
                existing_creds = self.vault.get_credentials_by_domain(domain)
                existing = next((c for c in existing_creds if c.username == username), None)
                if existing:
                    logger.info(f"updating existing credential {existing.id} instead of creating new")
                    self.vault.update_credential(
                        existing.id,
                        domain=domain,
                        username=username,
                        password=password,
                        notes=notes,
                        totp_secret=totp_secret,
                        clear_totp=clear_totp,
                        backup_codes=backup_codes,
                        clear_backup=clear_backup
                    )
                    return {'success': True, 'message': 'Credential updated (overwrite)', 'id': existing.id}
                new_id = self.vault.add_credential(domain, username, password, notes, totp_secret, backup_codes)
                return {'success': True, 'message': 'Credential saved', 'id': new_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _handle_delete_credentials(self, message: Dict[str, Any]) -> Dict[str, Any]:
        if not self.auth.is_unlocked:
            return {'success': False, 'error': 'Vault is locked', 'locked': True}
        credential_id = message.get('id')
        if not credential_id:
            return {'success': False, 'error': 'Credential ID required'}
        if self.vault.delete_credential(credential_id):
            return {'success': True, 'message': 'Credential deleted'}
        else:
            return {'success': False, 'error': 'Credential not found'}

    def _handle_get_all_credentials(self) -> Dict[str, Any]:
        if not self.auth.is_unlocked:
            return {'success': False, 'error': 'Vault is locked', 'locked': True}
        credentials = self.vault.get_all_credentials()
        return {
            'success': True,
            'credentials': [cred.to_dict() for cred in credentials]
        }

    def _handle_search(self, message: Dict[str, Any]) -> Dict[str, Any]:
        if not self.auth.is_unlocked:
            return {'success': False, 'error': 'Vault is locked', 'locked': True}
        query = message.get('query', '')
        credentials = self.vault.search_credentials(query)
        return {
            'success': True,
            'credentials': [cred.to_dict() for cred in credentials]
        }

    def _handle_get_totp(self, message: Dict[str, Any]) -> Dict[str, Any]:
        if not self.auth.is_unlocked:
            return {'success': False, 'error': 'Vault is locked', 'locked': True}
        credential_id = message.get('id')
        if not credential_id:
            return {'success': False, 'error': 'Credential ID required'}
        try:
            credential = self.vault.get_credential(credential_id)
            if not credential:
                return {'success': False, 'error': 'Credential not found'}
            if not credential.totp_secret:
                return {'success': False, 'error': 'No TOTP secret configured for this credential'}
            code, remaining = get_totp_code(credential.totp_secret)
            return {
                'success': True,
                'code': code,
                'remaining_seconds': remaining,
                'credential_id': credential_id
            }
        except ValueError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Error generating TOTP: {e}")
            return {'success': False, 'error': 'Failed to generate TOTP code'}

    def _handle_get_all_credit_cards(self) -> Dict[str, Any]:
        if not self.auth.is_unlocked:
            return {'success': False, 'error': 'Vault is locked', 'locked': True}
        cards = self.vault.get_all_credit_cards()
        return {
            'success': True,
            'cards': [card.to_dict() for card in cards]
        }

    def _handle_save_credit_card(self, message: Dict[str, Any]) -> Dict[str, Any]:
        if not self.auth.is_unlocked:
            return {'success': False, 'error': 'Vault is locked', 'locked': True}
        card_id = message.get('id')
        title = message.get('title')
        cardholder_name = message.get('cardholder_name')
        card_number = message.get('card_number')
        expiry_date = message.get('expiry_date')
        cvv = message.get('cvv')
        notes = message.get('notes')

        if not all([title, cardholder_name, card_number, expiry_date, cvv]):
            return {'success': False, 'error': 'All card fields are required'}

        try:
            if card_id:
                self.vault.update_credit_card(
                    card_id, title=title, cardholder_name=cardholder_name,
                    card_number=card_number, expiry_date=expiry_date,
                    cvv=cvv, notes=notes
                )
                return {'success': True, 'message': 'Card updated', 'id': card_id}
            else:
                new_id = self.vault.add_credit_card(
                    title, cardholder_name, card_number, expiry_date, cvv, notes
                )
                return {'success': True, 'message': 'Card saved', 'id': new_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _handle_delete_credit_card(self, message: Dict[str, Any]) -> Dict[str, Any]:
        if not self.auth.is_unlocked:
            return {'success': False, 'error': 'Vault is locked', 'locked': True}
        card_id = message.get('id')
        if not card_id:
            return {'success': False, 'error': 'Card ID required'}
        if self.vault.delete_credit_card(card_id):
            return {'success': True, 'message': 'Card deleted'}
        return {'success': False, 'error': 'Card not found'}

    def _handle_get_all_secure_notes(self) -> Dict[str, Any]:
        if not self.auth.is_unlocked:
            return {'success': False, 'error': 'Vault is locked', 'locked': True}
        notes = self.vault.get_all_secure_notes()
        return {
            'success': True,
            'notes': [note.to_dict() for note in notes]
        }

    def _handle_save_secure_note(self, message: Dict[str, Any]) -> Dict[str, Any]:
        if not self.auth.is_unlocked:
            return {'success': False, 'error': 'Vault is locked', 'locked': True}
        note_id = message.get('id')
        title = message.get('title')
        content = message.get('content')

        if not title or not content:
            return {'success': False, 'error': 'Title and content are required'}

        try:
            if note_id:
                self.vault.update_secure_note(note_id, title=title, content=content)
                return {'success': True, 'message': 'Note updated', 'id': note_id}
            else:
                new_id = self.vault.add_secure_note(title, content)
                return {'success': True, 'message': 'Note saved', 'id': new_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _handle_delete_secure_note(self, message: Dict[str, Any]) -> Dict[str, Any]:
        if not self.auth.is_unlocked:
            return {'success': False, 'error': 'Vault is locked', 'locked': True}
        note_id = message.get('id')
        if not note_id:
            return {'success': False, 'error': 'Note ID required'}
        if self.vault.delete_secure_note(note_id):
            return {'success': True, 'message': 'Note deleted'}
        return {'success': False, 'error': 'Note not found'}

    def run(self):
        logger.info("Starting Native Messaging Host")
        while True:
            message = self.read_message()
            if message is None:
                logger.info("Connection closed")
                break
            response = self.handle_message(message)
            if '_requestId' in message:
                response['_requestId'] = message['_requestId']
            self.send_message(response)
        logger.info("Native Messaging Host stopped")

def main():
    host = NativeMessagingHost()
    host.run()

if __name__ == '__main__':
    main()
