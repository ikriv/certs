from abc import ABC
from dataclasses import dataclass
from typing import Optional
import datetime

@dataclass(frozen=True)
class CertExpirationData:
    expiry_date: datetime.datetime
    time_remaining_str: str
    is_expired: bool
    days_remaining: int

@dataclass(frozen=True)
class CertExpirationResult:
    domain: str
    data: Optional[CertExpirationData]
    error: Optional[str]

