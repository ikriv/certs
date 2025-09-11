#!/usr/bin/env python3
import ssl
import socket
import datetime
import subprocess
import argparse
from pathlib import Path
import logging
from typing import List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/ssl_checker.log'),
        logging.StreamHandler()
    ]
)

class SSLChecker:
    def __init__(self, sender_email: str, recipient_email: str, dry_run: bool = False):
        self.sender_email = sender_email
        self.recipient_email = recipient_email
        self.dry_run = dry_run
        self.warning_days = [14, 7, 3, 0]  # 0 means expired

    def get_certificate_expiry(self, domain: str) -> Tuple[datetime.datetime, str]:
        """Get SSL certificate expiration date for a domain."""
        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443)) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    exp_date = datetime.datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y GMT')
                    return exp_date, None
        except Exception as e:
            return None, str(e)

    def send_email_alert(self, domain: str, days_remaining: int, expiry_date: datetime.datetime):
        """Send email alert for certificate expiration using sendmail."""
        subject = f"SSL Certificate Alert - {domain}"
        
        if days_remaining < 0:
            status = "EXPIRED"
        else:
            status = f"Expires in {days_remaining} days"

        email_content = f"""From: {self.sender_email}
To: {self.recipient_email}
Subject: {subject}
Content-Type: text/plain; charset=utf-8

SSL Certificate Alert for {domain}

Status: {status}
Expiration Date: {expiry_date.strftime('%Y-%m-%d %H:%M:%S')} GMT
Days Remaining: {days_remaining}

Please take appropriate action to renew the SSL certificate.
"""
        if self.dry_run:
            print(f"[DRY RUN] Would send email for {domain}:")
            print("------- Email Content -------")
            print(email_content)
            print("--------------------------")
            return

        print(f"Sending email alert for {domain}")
        
        try:
            # Use subprocess to pipe the email content to sendmail
            process = subprocess.Popen(['/usr/sbin/sendmail', '-t'], stdin=subprocess.PIPE)
            process.communicate(email_content.encode())
            
            if process.returncode != 0:
                raise Exception(f"Sendmail returned non-zero exit code: {process.returncode}")
                
            logging.info(f"Alert email sent for {domain}")
        except Exception as e:
            logging.error(f"Failed to send email alert for {domain}: {str(e)}")

    def format_time_remaining(self, days_remaining: int) -> str:
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

    def check_domains(self, domains: List[str]):
        """Check SSL certificates for all domains."""
        for domain in domains:
            expiry_date, error = self.get_certificate_expiry(domain)
            
            if error:
                print(f"Error checking {domain}: {error}")
                logging.error(f"Error checking {domain}: {error}")
                continue

            days_remaining = (expiry_date - datetime.datetime.utcnow()).days
            time_remaining = self.format_time_remaining(days_remaining)
            print(f"Domain: {domain}")
            print(f"  Expiration Date: {expiry_date.strftime('%Y-%m-%d %H:%M:%S')} GMT")
            print(f"  Time Remaining: {time_remaining}")
            
            logging.info(f"Domain: {domain}, Time remaining: {time_remaining}")

            # Check if we need to send an alert
            for warning_day in self.warning_days:
                if warning_day == 0 and days_remaining <= 0:
                    print(f"  WARNING: Certificate has expired!")
                    self.send_email_alert(domain, days_remaining, expiry_date)
                elif days_remaining == warning_day:
                    print(f"  WARNING: Certificate will expire in {warning_day} days!")
                    self.send_email_alert(domain, days_remaining, expiry_date)
            print()  # Add blank line between domains

def main():
    domains = [
        "ikriv.com", 
        "hodka.net", 
        "hodka.ikriv.com",
        "dev.ikriv.com",
        "korov.net"]

    parser = argparse.ArgumentParser(description='SSL Certificate Expiration Checker')
    parser.add_argument('--dry-run', action='store_true', help='Print what would be done without sending emails')

    args = parser.parse_args()

    checker = SSLChecker(
        "feedback@ikriv.com",
        "ivan@ikriv.com",
        args.dry_run
    )

    checker.check_domains(domains)

if __name__ == "__main__":
    main()
