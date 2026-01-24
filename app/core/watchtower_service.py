
import hashlib
import requests
import logging
import datetime
from typing import List, Dict, Tuple, Optional
from app.core.vault import VaultManager, Credential
from app.core.password_strength import analyze_password, PasswordStrength

logger = logging.getLogger(__name__)

class WatchtowerService:
    def __init__(self, vault_manager: VaultManager):
        self.vault_manager = vault_manager
        self._cache_pwned = {} 

    def check_pwned(self, password: str) -> int:
        if not password:
            return 0
            
        sha1_password = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
        prefix, suffix = sha1_password[:5], sha1_password[5:]
        
        if prefix in self._cache_pwned:
            response_text = self._cache_pwned[prefix]
        else:
            try:
                url = f"https://api.pwnedpasswords.com/range/{prefix}"
                response = requests.get(url, timeout=5)
                if response.status_code != 200:
                    logger.error(f"HIBP API returned status {response.status_code}")
                    return 0
                response_text = response.text
                self._cache_pwned[prefix] = response_text
            except Exception as e:
                logger.error(f"Error checking HIBP: {e}")
                return 0

        for line in response_text.splitlines():
            hash_suffix, count = line.split(':')
            if hash_suffix == suffix:
                return int(count)
                
        return 0

    def scan_vault(self, network_scan: bool = False) -> Dict:
        credentials = self.vault_manager.get_all_credentials()
        
        leaked_items = []
        reused_items = []
        weak_items = []
        
        password_map = {}
        
        total_items = len(credentials)
        password_ages_days = []
        totp_count = 0
        now = datetime.datetime.now(datetime.timezone.utc)
        
        for cred in credentials:
            if cred.totp_secret:
                totp_count += 1

            if cred.updated_at:
                try:
                    updated_dt = datetime.datetime.strptime(cred.updated_at, "%Y-%m-%d %H:%M:%S")
                    updated_dt = updated_dt.replace(tzinfo=datetime.timezone.utc)
                    age_delta = now - updated_dt
                    password_ages_days.append(age_delta.days)
                except Exception as e:
                    pass
            
            if not cred.password:
                continue
                
            analysis = analyze_password(cred.password)
            if analysis.strength in [PasswordStrength.WEAK, PasswordStrength.FAIR]:
                weak_items.append(cred)
                
            
            pass_hash = hashlib.sha256(cred.password.encode('utf-8')).hexdigest()
            if pass_hash not in password_map:
                password_map[pass_hash] = []
            password_map[pass_hash].append(cred)
            
        for pass_hash, creds in password_map.items():
            if len(creds) > 1:
                reused_items.extend(creds)
                
        checked_hashes = {}
        for cred in credentials:
            if not cred.password:
                continue
            
            if network_scan:
                pass_hash = hashlib.sha1(cred.password.encode('utf-8')).hexdigest().upper()
                if pass_hash in checked_hashes:
                    count = checked_hashes[pass_hash]
                else:
                    count = self.check_pwned(cred.password)
                    checked_hashes[pass_hash] = count
                
                if count != cred.leaked_count:
                    try:
                        self.vault_manager.update_credential_leak_status(cred.id, count)
                        cred.leaked_count = count
                    except Exception as e:
                        logger.error(f"Failed to persist leak status: {e}")
            else:
                count = cred.leaked_count
                
            if count > 0:
                leaked_items.append((cred, count))
                 
        score = 100
        if total_items > 0:
            n_weak = len(weak_items)
            n_reused = len(reused_items)
            n_leaked = len(leaked_items)
            
            strong_ratio = (total_items - n_weak) / total_items
            unique_ratio = (total_items - n_reused) / total_items
            safe_ratio = (total_items - n_leaked) / total_items
            
            score = int((strong_ratio * 30) + (unique_ratio * 30) + (safe_ratio * 40))
            
        avg_age_days = 0
        if password_ages_days:
            avg_age_days = sum(password_ages_days) // len(password_ages_days)
        
        return {
            'leaked': leaked_items,
            'reused': reused_items,
            'weak': weak_items,
            'score': max(0, score),
            'total_count': total_items,
            '2fa_count': totp_count,
            'avg_age_days': avg_age_days
        }
