import ssl
import socket
import datetime
import logging
from typing import List, NamedTuple, Union, Optional
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/ssl_checker.log'),
        logging.StreamHandler()
    ]
)

def format_time_remaining(days_remaining: int) -> str:
    """Format the remaining time in a human-readable format."""
    if days_remaining < 0:
        return "EXPIRED"

    years = days_remaining // 365
    remaining_days = days_remaining % 365
    months = remaining_days // 30
    days = remaining_days % 30

    parts = []
    if years > 0:
        parts.append(f"{years} year{'s' if years != 1 else ''}")
    if months > 0:
        parts.append(f"{months} month{'s' if months != 1 else ''}")
    if days > 0 or not parts:  # Include days if it's the only component
        parts.append(f"{days} day{'s' if days != 1 else ''}")

    return ", ".join(parts)

def get_certificate_expiry(domain: str) -> Union[datetime.datetime, Exception]:
    """Get SSL certificate expiration date for a domain."""
    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, 443)) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                not_after = cert['notAfter'].replace("GMT", "+0000")
                exp_date = datetime.datetime.strptime(not_after, '%b %d %H:%M:%S %Y %z')
                return exp_date
    except Exception as e:
        return e

@dataclass(frozen=True)
class CheckDomainResult:
    domain: str
    expiry_date: Optional[datetime.datetime]
    time_remaining: Optional[str] = None
    error: Optional[str] = None

def get_certificate_expiry_str(domain: str) -> CheckDomainResult:
    expiry_result = get_certificate_expiry(domain)
    if isinstance(expiry_result, Exception):
        return CheckDomainResult(domain, None, None, str(expiry_result))
    now = datetime.datetime.now(datetime.timezone.utc)
    days_remaining = (expiry_result - now).days
    time_remaining = format_time_remaining(days_remaining)
    return CheckDomainResult(domain, expiry_result, time_remaining, None)

def check_domains(domains: List[str]) -> List[CheckDomainResult]:
    return [get_certificate_expiry_str(domain) for domain in domains]

def main():
    domains = [
        "ikriv.com", 
        "hodka.net", 
        "hodka.ikriv.com",
        "dev.ikriv.com",
        "korov.net"]

    print(check_domains(domains))

if __name__ == "__main__":
    main()