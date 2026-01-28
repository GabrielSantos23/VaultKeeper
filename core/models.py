from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any

@dataclass
class Folder:
    id: Optional[int]
    name: str
    vault_type: str = "personal"
    icon: str = "folder"
    created_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class Credential:
    id: Optional[int]
    domain: str
    username: str
    password: str
    notes: Optional[str] = None
    totp_secret: Optional[str] = None
    backup_codes: Optional[str] = None
    is_favorite: bool = False
    folder_id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    leaked_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class SecureNote:
    id: Optional[int]
    title: str
    content: str
    is_favorite: bool = False
    folder_id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class CreditCard:
    id: Optional[int]
    title: str
    cardholder_name: str
    card_number: str
    expiry_date: str
    cvv: str
    notes: Optional[str] = None
    is_favorite: bool = False
    folder_id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
