#!/usr/bin/env python3
"""
Unit tests for check_cert.py script using pytest.
Run from cli/ directory: cd cli && pytest ../server/test_check_cert.py
Or set PYTHONPATH: PYTHONPATH=cli pytest server/test_check_cert.py
"""

import sys
import os
import datetime
import io
from unittest.mock import MagicMock, patch
from contextlib import redirect_stdout

import pytest

# Add cli directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'cli'))

from check_cert import check_domains, main
from schema import CertExpirationResult, CertExpirationData


async def create_async_iter(results):
    """Helper function to create an async iterator from a list of results."""
    for result in results:
        yield result


class TestCheckDomains:
    """Test the check_domains function."""
    
    @pytest.fixture
    def valid_cert_data(self):
        return CertExpirationData(
            expiry_date=datetime.datetime(2024, 12, 31, 23, 59, 59, tzinfo=datetime.timezone.utc),
            time_remaining_str="2 months, 15 days",
            is_expired=False,
            days_remaining=75
        )
    
    @pytest.fixture
    def expired_cert_data(self):
        return CertExpirationData(
            expiry_date=datetime.datetime(2023, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc),
            time_remaining_str="EXPIRED",
            is_expired=True,
            days_remaining=-10
        )
    
    @pytest.fixture
    def expiring_soon_cert_data(self):
        return CertExpirationData(
            expiry_date=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=15),
            time_remaining_str="15 days",
            is_expired=False,
            days_remaining=15
        )

    @pytest.mark.asyncio
    @patch('check_cert.get_cert_expiration_many')
    async def test_single_domain_success(self, mock_get_cert_expiration_many, valid_cert_data):
        mock_result = CertExpirationResult(domain="example.com", data=valid_cert_data, error=None)
        mock_get_cert_expiration_many.return_value = create_async_iter([mock_result])
        
        with redirect_stdout(io.StringIO()) as stdout:
            await check_domains(["example.com"])
            output = stdout.getvalue()
        
        assert "example.com" in output
        assert "STATUS: VALID" in output

    @pytest.mark.asyncio
    @patch('check_cert.get_cert_expiration_many')
    async def test_expired_certificate(self, mock_get_cert_expiration_many, expired_cert_data):
        mock_result = CertExpirationResult(domain="expired.com", data=expired_cert_data, error=None)
        mock_get_cert_expiration_many.return_value = create_async_iter([mock_result])
        
        with redirect_stdout(io.StringIO()) as stdout:
            await check_domains(["expired.com"])
            output = stdout.getvalue()
        
        assert "STATUS: EXPIRED" in output

    @pytest.mark.asyncio
    @patch('check_cert.get_cert_expiration_many')
    async def test_expiring_soon(self, mock_get_cert_expiration_many, expiring_soon_cert_data):
        mock_result = CertExpirationResult(domain="expiring.com", data=expiring_soon_cert_data, error=None)
        mock_get_cert_expiration_many.return_value = create_async_iter([mock_result])
        
        with redirect_stdout(io.StringIO()) as stdout:
            await check_domains(["expiring.com"])
            output = stdout.getvalue()
        
        assert "STATUS: EXPIRING SOON" in output

    @pytest.mark.asyncio
    @patch('check_cert.get_cert_expiration_many')
    async def test_error_handling(self, mock_get_cert_expiration_many):
        mock_result = CertExpirationResult(domain="bad.com", data=None, error="Connection failed")
        mock_get_cert_expiration_many.return_value = create_async_iter([mock_result])
        
        with redirect_stdout(io.StringIO()) as stdout:
            await check_domains(["bad.com"])
            output = stdout.getvalue()
        
        assert "ERROR: Connection failed" in output


class TestMainFunction:
    @patch('check_cert.asyncio.run')
    @patch('check_cert.argparse.ArgumentParser.parse_args')
    def test_main_success(self, mock_parse_args, mock_asyncio_run):
        mock_args = MagicMock()
        mock_args.domains = ["example.com"]
        mock_parse_args.return_value = mock_args
        
        main()
        
        mock_asyncio_run.assert_called_once()

    @patch('check_cert.sys.exit')
    @patch('check_cert.argparse.ArgumentParser.parse_args')
    def test_main_invalid_domain(self, mock_parse_args, mock_sys_exit):
        mock_args = MagicMock()
        mock_args.domains = ["invalid"]
        mock_parse_args.return_value = mock_args
        
        main()
        
        mock_sys_exit.assert_called_once_with(400)
