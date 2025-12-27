import ssl
import datetime
import asyncio
from typing import AsyncIterator, Sequence
from schema import CertExpirationData, CertExpirationResult


def _format_time_remaining(days_remaining: int) -> str:
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
    if days > 0 or not parts:
        parts.append(f"{days} day{'s' if days != 1 else ''}")

    return ", ".join(parts)


async def _safe_close_writer(writer: asyncio.StreamWriter) -> None:
    try:
        writer.close()
        await writer.wait_closed()
    except Exception:
        pass


async def _get_certificate_expiration_time(domain: str) -> datetime.datetime:
    """Get SSL certificate expiration date for a domain."""
    context = ssl.create_default_context()
    _, writer = await asyncio.open_connection(
        domain, 443, ssl=context, server_hostname=domain
    )

    try:
        ssl_socket = writer.get_extra_info("ssl_object")
        cert = ssl_socket.getpeercert()
        not_after = cert["notAfter"].replace("GMT", "+0000")
        exp_date = datetime.datetime.strptime(not_after, "%b %d %H:%M:%S %Y %z")
        return exp_date
    finally:
        await _safe_close_writer(writer)


async def get_cert_expiration_data(domain: str) -> CertExpirationData:
    """Get SSL certificate expiration information for a single domain."""
    expiry_time = await _get_certificate_expiration_time(domain)
    now = datetime.datetime.now(datetime.timezone.utc)
    days_remaining = (expiry_time - now).days
    is_expired = days_remaining < 0
    time_remaining_str = _format_time_remaining(days_remaining)
    return CertExpirationData(expiry_time, time_remaining_str, is_expired, days_remaining)


async def get_cert_expiration_no_raise(domain: str) -> CertExpirationResult:
    """Get SSL certificate expiration information without raising exceptions."""
    try:
        data = await get_cert_expiration_data(domain)
        return CertExpirationResult(domain=domain, data=data, error=None)
    except Exception as e:
        return CertExpirationResult(domain=domain, data=None, error=str(e))


async def get_cert_expiration_many(
    domains: Sequence[str],
) -> AsyncIterator[CertExpirationResult]:
    """Check SSL certificate expiration for multiple domains asynchronously."""
    tasks = [
        asyncio.create_task(get_cert_expiration_no_raise(domain)) for domain in domains
    ]

    for task in asyncio.as_completed(tasks):
        result = await task
        yield result

