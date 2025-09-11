from dataclasses import dataclass
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
    if days > 0 or not parts:  # Include days if it's the only component
        parts.append(f"{days} day{'s' if days != 1 else ''}")

    return ", ".join(parts)

async def _safe_close_writer(writer: asyncio.StreamWriter) -> None:
    try:
        writer.close()
        await writer.wait_closed()
    except Exception as e:
        # We don't really care if closing the writer didn't succeed
        # github.com is known to through APPLICATION_DATA_AFTER_CLOSE_NOTIFY error
        # TODO: log it somewhere
        pass

async def _get_certificate_expiration_time(domain: str) -> datetime.datetime:
    """Get SSL certificate expiration date for a domain."""
    context = ssl.create_default_context()
    
    # Create async connection
    _, writer = await asyncio.open_connection(domain, 443, ssl=context, server_hostname=domain)
    
    try:
        # Get the SSL socket from the writer
        ssl_socket = writer.get_extra_info('ssl_object')
        
        # Get certificate
        cert = ssl_socket.getpeercert()
        not_after = cert['notAfter'].replace("GMT", "+0000")
        exp_date = datetime.datetime.strptime(not_after, '%b %d %H:%M:%S %Y %z')
        return exp_date
    finally:
        await _safe_close_writer(writer)

async def get_cert_expiration_data(domain: str) -> CertExpirationData:
    """
    Get SSL certificate expiration information for a single domain.
    
    This function connects to the specified domain over HTTPS (port 443) and retrieves
    the SSL certificate to determine its expiration date and remaining validity period.
    
    Args:
        domain (str): The domain name to check (e.g., 'google.com', 'example.com').
                     Should not include protocol (https://) or port numbers.
    
    Returns:
        CertExpirationData: A dataclass containing:
            - expiry_date (datetime.datetime): The exact date and time when the 
              certificate expires (in UTC timezone)
            - time_remaining_str (str): Human-readable string describing time remaining
              (e.g., "2 months, 15 days", "EXPIRED", "30 days")
            - is_expired (bool): True if the certificate has already expired
            - days_remaining (int): Number of days remaining until expiration (negative if expired)
    
    Raises:
        ssl.SSLError: If there's an SSL/TLS connection error
        socket.gaierror: If the domain name cannot be resolved
        ConnectionError: If the connection to the domain fails
        Exception: For any other network or certificate-related errors
    
    Note:
        This function performs a live SSL handshake with the target domain.
        The certificate information is retrieved directly from the server,
        not from a certificate transparency log or other cached source.
    """
    expiry_time = await _get_certificate_expiration_time(domain)
    now = datetime.datetime.now(datetime.timezone.utc)
    days_remaining = (expiry_time - now).days
    is_expired = days_remaining < 0
    time_remaining_str = _format_time_remaining(days_remaining)
    return CertExpirationData(expiry_time, time_remaining_str, is_expired, days_remaining)

async def get_cert_expiration_no_raise(domain: str) -> CertExpirationResult:
    """
    Get SSL certificate expiration information for a single domain without raising exceptions.
    
    This is a wrapper around get_cert_expiration_data() that catches all exceptions
    and returns them as part of the CertExpirationResult object instead of raising them.
    This makes it safe to use in concurrent operations where you want to handle
    errors gracefully without stopping the entire process.
    
    Args:
        domain (str): The domain name to check (e.g., 'google.com', 'example.com').
                     Should not include protocol (https://) or port numbers.
    
    Returns:
        CertExpirationResult: A dataclass containing:
            - domain (str): The domain name that was checked
            - data (Optional[CertExpirationData]): Certificate data if successful, None if failed
            - error (Optional[str]): Error message if failed, None if successful
    
    Note:
        This function never raises exceptions. All errors are captured and returned
        as error messages in the CertExpirationResult object. Use this when you
        need to process multiple domains and want to continue even if some fail.
    """
    try:
        data = await get_cert_expiration_data(domain)
        return CertExpirationResult(domain=domain, data=data, error=None)
    except Exception as e:
        return CertExpirationResult(domain=domain, data=None, error=str(e))



async def get_cert_expiration_many(domains: Sequence[str]) -> AsyncIterator[CertExpirationResult]:
    """
    Check SSL certificate expiration for multiple domains asynchronously.
    
    This function fires all domain checks concurrently and yields results as they complete,
    providing significant performance improvements over sequential checking. Each domain
    is processed independently, so failures in one domain don't affect others.
    
    Args:
        domains (Sequence[str]): A sequence of domain names to check.
                                Can be a list, tuple, or any sequence type.
                                Each domain should not include protocol (https://) or port numbers.
    
    Yields:
        CertExpirationResult: For each domain, yields a result containing:
            - domain (str): The domain name that was checked
            - data (Optional[CertExpirationData]): Certificate data if successful, None if failed
            - error (Optional[str]): Error message if failed, None if successful
    
    Exception Handling:
        This function uses get_cert_expiration_no_raise() internally, which means:
        - No exceptions are raised by this function
        - All errors are captured and returned as error messages in CertExpirationResult
        - Network timeouts, SSL errors, DNS resolution failures, etc. are all handled gracefully
        - The function continues processing even if some domains fail
        - Results are yielded in the order they complete, not the input order
    
    Performance:
        - All domain checks start simultaneously (concurrent execution)
        - Results arrive as soon as each domain responds (not waiting for slower ones)
        - Typical performance: 5-10x faster than sequential checking
        - Memory efficient: processes results as they arrive, not storing all at once
    
    Example:
        >>> import asyncio
        >>> 
        >>> async def check_multiple_domains():
        ...     domains = ["google.com", "github.com", "invalid-domain-12345.com", "example.com"]
        ...     
        ...     print("Starting concurrent domain checks...")
        ...     async for result in get_cert_expiration_many(domains):
        ...         if result.error:
        ...             print(f"ERROR {result.domain}: {result.error}")
        ...         else:
        ...             data = result.data
        ...             status = "EXPIRED" if data.is_expired else "VALID"
        ...             print(f"OK {result.domain}: {data.time_remaining_str} ({status})")
        ... 
        >>> asyncio.run(check_multiple_domains())
        Starting concurrent domain checks...
        OK google.com: 2 months, 15 days (VALID)
        OK example.com: 4 months, 6 days (VALID)
        ERROR invalid-domain-12345.com: [Errno 11001] getaddrinfo failed
        OK github.com: 1 year, 3 months (VALID)
    
    Note:
        Results may arrive in a different order than the input domains due to
        varying network response times. Use the domain field to identify which
        result corresponds to which input domain.
    """
    tasks = [asyncio.create_task(get_cert_expiration_no_raise(domain)) for domain in domains]
    
    for task in asyncio.as_completed(tasks):
        result = await task
        yield result


