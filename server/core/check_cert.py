#!/usr/bin/env python3
"""
Console program to check SSL certificate expiration for multiple domains.
Usage: python check_cert.py <domain1> [domain2] [domain3] ...
Example: python check_cert.py google.com github.com example.com

No external dependencies - uses only Python standard library.
"""

import sys
from pathlib import Path

# Allow running as a script from any directory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
import argparse
from core.expiration import get_cert_expiration_many


def eprint(*args, **kwargs):
    """Print to stderr."""
    print(*args, file=sys.stderr, **kwargs)


async def check_domains(domains: list[str]) -> None:
    """Check domains and print results to console."""
    async for result in get_cert_expiration_many(domains):
        print(result.domain)
        if result.error:
            print(f"ERROR: {result.error}")
        elif result.data is None:
            print("ERROR: No data returned")
        else:
            data = result.data
            print(f"Certificate expires: {data.expiry_date.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            print(f"Time Remaining: {data.time_remaining_str}")

            if data.is_expired:
                print("STATUS: EXPIRED")
            elif data.days_remaining < 30:
                print("STATUS: EXPIRING SOON (less than 30 days)")
            else:
                print("STATUS: VALID")
        print("")


def main() -> None:
    """Main function to handle command line arguments and run the check."""
    parser = argparse.ArgumentParser(
        description="Check SSL certificate expiration for multiple domains concurrently",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exit codes:
    0: Success (includes cases when some certificates are expired)
    400: Invalid parameters
    408: Check cancelled by user
    500: Unexpected error

Examples:
  python check_cert.py google.com github.com
  python check_cert.py example.com
        """,
    )

    parser.add_argument(
        "domains",
        nargs="+",
        help="One or more domain names to check (e.g., google.com github.com)",
    )

    parser.add_argument(
        "--version", action="version", version="SSL Certificate Checker 2.0"
    )

    args = parser.parse_args()

    domains = []
    for domain in args.domains:
        domain = domain.strip().lower()
        if not domain or "." not in domain:
            eprint(f"Error: Invalid domain name '{domain}'")
            sys.exit(400)
        domains.append(domain)

    try:
        asyncio.run(check_domains(domains))
    except KeyboardInterrupt:
        eprint("\nCheck cancelled by user")
        sys.exit(408)
    except Exception as e:
        eprint(f"Unexpected error: {e}")
        sys.exit(500)


if __name__ == "__main__":
    main()

