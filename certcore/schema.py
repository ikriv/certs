from abc import ABC
from dataclasses import dataclass
from typing import Awaitable, Optional, Callable
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

# Interface for handling certificate expiration results
class CertExpirationHandler(ABC):
    def __enter__(self) -> None:
        pass

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        pass

    async def handleExpirationResul(self, _result: CertExpirationResult) -> None:
        pass

