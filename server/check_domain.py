#!/usr/bin/env python3
"""
Console program to check SSL certificate expiration for multiple domains.
Usage: python check_domain.py <domain1> [domain2] [domain3] ...
Example: python check_domain.py google.com github.com example.com
"""

import asyncio
import sys
import argparse
import os
from typing import List, Optional
from dotenv import load_dotenv
from get_cert_expiration import get_cert_expiration_many
from schema import CertExpirationHandler, CertExpirationResult
from email_handler import EmailHandler


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


def load_env_file(config_file: str) -> None:
    """
    Load environment variables from a .env file using python-dotenv.
    
    Args:
        config_file: Path to the .env file
        
    Raises:
        FileNotFoundError: If the config file doesn't exist
        ValueError: If there's an error loading the file
    """
    try:
        # Load .env file, override=False means don't override existing env vars
        success = load_dotenv(config_file, override=False)
        if not success:
            raise FileNotFoundError(f"Config file not found: {config_file}")
    except Exception as e:
        raise ValueError(f"Error loading config file '{config_file}': {e}")


def parse_warning_days(warning_days_str: Optional[str]) -> List[int]:
    """Parse comma-separated warning days string into a list of integers."""
    if not warning_days_str:
        return [14, 7, 3, 0]  # Default warning days
    
    try:
        days = [int(day.strip()) for day in warning_days_str.split(',')]
        return sorted(days, reverse=True)  # Sort in descending order
    except ValueError as e:
        raise ValueError(f"Invalid warning days format '{warning_days_str}': {e}")


def create_handler_from_env(force_dry_run: bool = False) -> CertExpirationHandler:
    """Create the appropriate handler based on environment variables."""
    mode = os.getenv('CHECK_DOMAIN_MODE', 'console').lower()
    
    if mode == 'console':
        return ConsoleHandler()
    
    elif mode in ['email', 'email_dry_run']:
        # Get email configuration
        email_from = os.getenv('CHECK_DOMAIN_EMAIL_FROM')
        email_to = os.getenv('CHECK_DOMAIN_EMAIL_TO')
        warning_days_str = os.getenv('CHECK_DOMAIN_WARNING_DAYS')
        
        # Validate required email parameters
        if not email_from:
            raise ValueError("CHECK_DOMAIN_EMAIL_FROM environment variable is required for email mode")
        if not email_to:
            raise ValueError("CHECK_DOMAIN_EMAIL_TO environment variable is required for email mode")
        
        # Parse warning days
        try:
            warning_days = parse_warning_days(warning_days_str)
        except ValueError as e:
            raise ValueError(f"Invalid warning days configuration: {e}")
        
        # Create email handler
        # Force dry_run if --dry-run flag is used, otherwise use mode setting
        dry_run = force_dry_run or (mode == 'email_dry_run')
        return EmailHandler(
            sender_email=email_from,
            recipient_email=email_to,
            warning_days=warning_days,
            dry_run=dry_run
        )
    
    else:
        raise ValueError(f"Invalid CHECK_DOMAIN_MODE '{mode}'. Must be 'console', 'email', or 'email_dry_run'")


def eprint(message: str) -> None:
    print(message, file=sys.stderr)

def main() -> None:
    """Main function to handle command line arguments and run the check."""
    parser = argparse.ArgumentParser(
        description="Check SSL certificate expiration for multiple domains concurrently",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment Variables:
  CHECK_DOMAIN_MODE        Output mode: 'console', 'email', or 'email_dry_run' (default: console)
  CHECK_DOMAIN_EMAIL_FROM  Sender email address (required for email modes)
  CHECK_DOMAIN_EMAIL_TO    Recipient email address (required for email modes)
  CHECK_DOMAIN_WARNING_DAYS Comma-separated warning days (e.g., '7,14,30', default: '14,7,3,0')

Exit codes:
    0: Success. This includes cases when some certificates are expired
    400: Invalid parameters or config
    408: Check cancelled by user
    500: Unexpected error

Examples:
  # Console mode (default)
  python check_domain.py google.com github.com
  
  # Email mode with environment variables
  CHECK_DOMAIN_MODE=email CHECK_DOMAIN_EMAIL_FROM=alerts@company.com CHECK_DOMAIN_EMAIL_TO=admin@company.com python check_domain.py google.com
  
  # Email dry-run mode with custom warning days
  CHECK_DOMAIN_MODE=email_dry_run CHECK_DOMAIN_EMAIL_FROM=alerts@company.com CHECK_DOMAIN_EMAIL_TO=admin@company.com CHECK_DOMAIN_WARNING_DAYS=30,14,7,0 python check_domain.py google.com
  
  # Using configuration file
  python check_domain.py --config config.env google.com github.com
  
  # Force dry-run mode for email output
  CHECK_DOMAIN_MODE=email CHECK_DOMAIN_EMAIL_FROM=alerts@company.com CHECK_DOMAIN_EMAIL_TO=admin@company.com python check_domain.py --dry-run google.com
        """
    )
    
    parser.add_argument(
        'domains',
        nargs='+',
        help='One or more domain names to check (e.g., google.com github.com)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Path to .env configuration file with environment variables'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Force dry-run mode for email output (overrides CHECK_DOMAIN_MODE=email)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='SSL Certificate Checker 2.0'
    )
    
    args = parser.parse_args()
    
    # Load configuration file if specified
    if args.config:
        try:
            load_env_file(args.config)
        except (FileNotFoundError, ValueError) as e:
            eprint(f"Config file error: {e}")
            sys.exit(400)
    
    # Validate domain format (basic check)
    domains = []
    for domain in args.domains:
        domain = domain.strip().lower()
        if not domain or '.' not in domain:
            eprint(f"Error: Invalid domain name '{domain}'. Please provide valid domain names (e.g., google.com)")
            sys.exit(400)
        domains.append(domain)
    
    # Create handler based on environment variables
    try:
        handler = create_handler_from_env(force_dry_run=args.dry_run)
    except ValueError as e:
        eprint(f"Configuration error: {e}")
        sys.exit(400)
    
    # Run the async check
    try:
        asyncio.run(check_domains(domains, handler))
    except KeyboardInterrupt:
        eprint("\nCheck cancelled by user")
        sys.exit(408)
    except Exception as e:
        eprint(f"Unexpected error: {e}")
        sys.exit(500)


if __name__ == "__main__":
    main()
