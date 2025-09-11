#!/usr/bin/env python3
"""
Console program to check SSL certificate expiration for multiple domains.
Usage: python check_domain.py <domain1> [domain2] [domain3] ...
Example: python check_domain.py google.com github.com example.com
"""

import asyncio
import sys
import argparse
from get_cert_expiration import get_cert_expiration_many
from schema import CertExpirationHandler, CertExpirationResult


async def check_domains(domains: list[str], handler: CertExpirationHandler) -> None:
    with handler:
        async for result in get_cert_expiration_many(domains):
            await handler.handleExpirationResul(result)

class ConsoleHandler(CertExpirationHandler):
    async def handleExpirationResul(self, result: CertExpirationResult) -> None:
        print(result.domain)
        if result.error:
            print(f"ERROR: {result.error}\n")
        else:
            data = result.data
            print(f"Certificate expires: {data.expiry_date.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            print(f"Time Remaining: {data.time_remaining_str}")
            
            # Add status indicator using the pre-calculated days_remaining
            if data.is_expired:
                print("STATUS: EXPIRED")
            elif data.days_remaining < 30:
                print("STATUS: EXPIRING SOON (less than 30 days)")
            else:
                print("STATUS: VALID")
        print("")


def eprint(message: str) -> None:
    print(message, file=sys.stderr)

def main() -> None:
    """Main function to handle command line arguments and run the check."""
    parser = argparse.ArgumentParser(
        description="Check SSL certificate expiration for multiple domains concurrently",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python check_domain.py google.com
  python check_domain.py google.com github.com example.com
  python check_domain.py subdomain.example.com another-domain.com
        """
    )
    
    parser.add_argument(
        'domains',
        nargs='+',
        help='One or more domain names to check (e.g., google.com github.com)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='SSL Certificate Checker 2.0'
    )
    
    args = parser.parse_args()
    
    # Validate domain format (basic check)
    domains = []
    for domain in args.domains:
        domain = domain.strip().lower()
        if not domain or '.' not in domain:
            eprint(f"Error: Invalid domain name '{domain}'. Please provide valid domain names (e.g., google.com)")
            sys.exit(2)
        domains.append(domain)
    
    # Run the async check
    try:
        asyncio.run(check_domains(domains, ConsoleHandler()))
    except KeyboardInterrupt:
        eprint("\nCheck cancelled by user")
        sys.exit(3)
    except Exception as e:
        eprint(f"Unexpected error: {e}")
        sys.exit(4)


if __name__ == "__main__":
    main()
