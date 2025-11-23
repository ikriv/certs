#!/usr/bin/env python3
"""
Unit tests for check_cert.py script using pytest.
"""

import datetime
import io
from unittest.mock import MagicMock, patch
from contextlib import redirect_stderr, redirect_stdout

import pytest

# Import the functions we want to test
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
        """Valid certificate data fixture."""
        return CertExpirationData(
            expiry_date=datetime.datetime(2024, 12, 31, 23, 59, 59, tzinfo=datetime.timezone.utc),
            time_remaining_str="2 months, 15 days",
            is_expired=False,
            days_remaining=75
        )
    
    @pytest.fixture
    def expired_cert_data(self):
        """Expired certificate data fixture."""
        return CertExpirationData(
            expiry_date=datetime.datetime(2023, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc),
            time_remaining_str="EXPIRED",
            is_expired=True,
            days_remaining=-10
        )
    
    @pytest.fixture
    def expiring_soon_cert_data(self):
        """Expiring soon certificate data fixture."""
        return CertExpirationData(
            expiry_date=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=15),
            time_remaining_str="15 days",
            is_expired=False,
            days_remaining=15
        )

    @pytest.mark.asyncio
    @patch('check_cert.get_cert_expiration_many')
    async def test_single_domain_success(self, mock_get_cert_expiration_many, valid_cert_data):
        """Test checking a single domain successfully."""
        # Setup mock
        mock_result = CertExpirationResult(
            domain="example.com",
            data=valid_cert_data,
            error=None
        )
        
        mock_get_cert_expiration_many.return_value = create_async_iter([mock_result])
        
        # Capture output
        with redirect_stdout(io.StringIO()) as stdout:
            await check_domains(["example.com"])
            output = stdout.getvalue()
        
        # Verify output
        expected_lines = [
            "example.com",
            "Certificate expires: 2024-12-31 23:59:59 UTC",
            "Time Remaining: 2 months, 15 days",
            "STATUS: VALID",
            ""
        ]
        for line in expected_lines:
            assert line in output

    @pytest.mark.asyncio
    @patch('check_cert.get_cert_expiration_many')
    async def test_multiple_domains_success(self, mock_get_cert_expiration_many, valid_cert_data, expired_cert_data, expiring_soon_cert_data):
        """Test checking multiple domains successfully."""
        # Setup mock
        mock_results = [
            CertExpirationResult(domain="example.com", data=valid_cert_data, error=None),
            CertExpirationResult(domain="test.com", data=expired_cert_data, error=None),
            CertExpirationResult(domain="demo.com", data=expiring_soon_cert_data, error=None)
        ]
        mock_get_cert_expiration_many.return_value = create_async_iter(mock_results)
        
        # Capture output
        with redirect_stdout(io.StringIO()) as stdout:
            await check_domains(["example.com", "test.com", "demo.com"])
            output = stdout.getvalue()
        
        # Verify all domains are in output
        assert "example.com" in output
        assert "test.com" in output
        assert "demo.com" in output
        
        # Verify status indicators
        assert "STATUS: VALID" in output
        assert "STATUS: EXPIRED" in output
        assert "STATUS: EXPIRING SOON (less than 30 days)" in output

    @pytest.mark.asyncio
    @patch('check_cert.get_cert_expiration_many')
    async def test_domain_not_found_error(self, mock_get_cert_expiration_many):
        """Test handling domain not found error."""
        # Setup mock
        mock_result = CertExpirationResult(
            domain="nonexistent-domain-12345.com",
            data=None,
            error="[Errno 11001] getaddrinfo failed"
        )
        mock_get_cert_expiration_many.return_value = create_async_iter([mock_result])
        
        # Capture output
        with redirect_stdout(io.StringIO()) as stdout:
            await check_domains(["nonexistent-domain-12345.com"])
            output = stdout.getvalue()
        
        # Verify error output
        expected_lines = [
            "nonexistent-domain-12345.com",
            "ERROR: [Errno 11001] getaddrinfo failed",
            ""
        ]
        for line in expected_lines:
            assert line in output

    @pytest.mark.asyncio
    @patch('check_cert.get_cert_expiration_many')
    async def test_no_cert_data_error(self, mock_get_cert_expiration_many):
        """Test handling case where no certificate data is returned."""
        # Setup mock
        mock_result = CertExpirationResult(
            domain="example.com",
            data=None,
            error=None
        )
        mock_get_cert_expiration_many.return_value = create_async_iter([mock_result])
        
        # Capture output
        with redirect_stdout(io.StringIO()) as stdout:
            await check_domains(["example.com"])
            output = stdout.getvalue()
        
        # Verify error output
        expected_lines = [
            "example.com",
            "ERROR: No data returned",
            ""
        ]
        for line in expected_lines:
            assert line in output

    @pytest.mark.asyncio
    @patch('check_cert.get_cert_expiration_many')
    async def test_mixed_success_and_error(self, mock_get_cert_expiration_many, valid_cert_data, expired_cert_data):
        """Test handling mix of successful and failed domain checks."""
        # Setup mock
        mock_results = [
            CertExpirationResult(domain="example.com", data=valid_cert_data, error=None),
            CertExpirationResult(domain="invalid-domain.com", data=None, error="Connection timeout"),
            CertExpirationResult(domain="test.com", data=expired_cert_data, error=None)
        ]
        mock_get_cert_expiration_many.return_value = create_async_iter(mock_results)
        
        # Capture output
        with redirect_stdout(io.StringIO()) as stdout:
            await check_domains(["example.com", "invalid-domain.com", "test.com"])
            output = stdout.getvalue()
        
        # Verify all domains are processed
        assert "example.com" in output
        assert "invalid-domain.com" in output
        assert "test.com" in output
        
        # Verify success case
        assert "STATUS: VALID" in output
        
        # Verify error case
        assert "ERROR: Connection timeout" in output
        
        # Verify expired case
        assert "STATUS: EXPIRED" in output

    @pytest.mark.asyncio
    @patch('check_cert.get_cert_expiration_many')
    async def test_expired_certificate(self, mock_get_cert_expiration_many, expired_cert_data):
        """Test handling expired certificate."""
        # Setup mock
        mock_result = CertExpirationResult(
            domain="expired.com",
            data=expired_cert_data,
            error=None
        )
        mock_get_cert_expiration_many.return_value = create_async_iter([mock_result])
        
        # Capture output
        with redirect_stdout(io.StringIO()) as stdout:
            await check_domains(["expired.com"])
            output = stdout.getvalue()
        
        # Verify expired status
        assert "STATUS: EXPIRED" in output
        assert "Time Remaining: EXPIRED" in output

    @pytest.mark.asyncio
    @patch('check_cert.get_cert_expiration_many')
    async def test_expiring_soon_certificate(self, mock_get_cert_expiration_many, expiring_soon_cert_data):
        """Test handling certificate expiring soon."""
        # Setup mock
        mock_result = CertExpirationResult(
            domain="expiring.com",
            data=expiring_soon_cert_data,
            error=None
        )
        mock_get_cert_expiration_many.return_value = create_async_iter([mock_result])
        
        # Capture output
        with redirect_stdout(io.StringIO()) as stdout:
            await check_domains(["expiring.com"])
            output = stdout.getvalue()
        
        # Verify expiring soon status
        assert "STATUS: EXPIRING SOON (less than 30 days)" in output
        assert "Time Remaining: 15 days" in output

    @pytest.mark.asyncio
    @patch('check_cert.get_cert_expiration_many')
    async def test_empty_domains_list(self, mock_get_cert_expiration_many):
        """Test handling empty domains list."""
        mock_get_cert_expiration_many.return_value = create_async_iter([])
        
        # Capture output
        with redirect_stdout(io.StringIO()) as stdout:
            await check_domains([])
            output = stdout.getvalue()
        
        # Verify no output
        assert output == ""

    @pytest.mark.asyncio
    @patch('check_cert.get_cert_expiration_many')
    async def test_ssl_handshake_error(self, mock_get_cert_expiration_many):
        """Test handling SSL handshake error."""
        # Setup mock
        mock_result = CertExpirationResult(
            domain="ssl-error.com",
            data=None,
            error="SSL handshake failed: certificate verify failed"
        )
        mock_get_cert_expiration_many.return_value = create_async_iter([mock_result])
        
        # Capture output
        with redirect_stdout(io.StringIO()) as stdout:
            await check_domains(["ssl-error.com"])
            output = stdout.getvalue()
        
        # Verify error output
        assert "ssl-error.com" in output
        assert "ERROR: SSL handshake failed: certificate verify failed" in output

    @pytest.mark.asyncio
    @patch('check_cert.get_cert_expiration_many')
    async def test_connection_timeout_error(self, mock_get_cert_expiration_many):
        """Test handling connection timeout error."""
        # Setup mock
        mock_result = CertExpirationResult(
            domain="timeout.com",
            data=None,
            error="Connection timeout after 30 seconds"
        )
        mock_get_cert_expiration_many.return_value = create_async_iter([mock_result])
        
        # Capture output
        with redirect_stdout(io.StringIO()) as stdout:
            await check_domains(["timeout.com"])
            output = stdout.getvalue()
        
        # Verify error output
        assert "timeout.com" in output
        assert "ERROR: Connection timeout after 30 seconds" in output


class TestMainFunction:
    @patch('check_cert.asyncio.run')
    @patch('check_cert.argparse.ArgumentParser.parse_args')
    def test_main_success_single_domain(self, mock_parse_args, mock_asyncio_run):
        """Test main function with single valid domain."""
        # Setup mock args
        mock_args = MagicMock()
        mock_args.domains = ["example.com"]
        mock_parse_args.return_value = mock_args
        
        # Call main
        main()
        
        # Verify asyncio.run was called
        mock_asyncio_run.assert_called_once()

    @patch('check_cert.asyncio.run')
    @patch('check_cert.argparse.ArgumentParser.parse_args')
    def test_main_success_multiple_domains(self, mock_parse_args, mock_asyncio_run):
        """Test main function with multiple valid domains."""
        # Setup mock args
        mock_args = MagicMock()
        mock_args.domains = ["example.com", "test.com", "demo.com"]
        mock_parse_args.return_value = mock_args
        
        # Call main
        main()
        
        # Verify asyncio.run was called
        mock_asyncio_run.assert_called_once()

    @patch('check_cert.sys.exit')
    @patch('check_cert.argparse.ArgumentParser.parse_args')
    def test_main_invalid_domain_no_dot(self, mock_parse_args, mock_sys_exit):
        """Test main function with invalid domain (no dot)."""
        # Setup mock args
        mock_args = MagicMock()
        mock_args.domains = ["invalid"]
        mock_parse_args.return_value = mock_args
        
        # Call main
        main()
        
        # Verify sys.exit was called with error code 400
        mock_sys_exit.assert_called_once_with(400)

    @patch('check_cert.sys.exit')
    @patch('check_cert.argparse.ArgumentParser.parse_args')
    def test_main_invalid_domain_empty(self, mock_parse_args, mock_sys_exit):
        """Test main function with empty domain."""
        # Setup mock args
        mock_args = MagicMock()
        mock_args.domains = [""]
        mock_parse_args.return_value = mock_args
        
        # Make sys.exit raise SystemExit to actually stop execution
        mock_sys_exit.side_effect = SystemExit(400)
        
        # Call main and expect SystemExit
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        # Verify the exit code
        assert exc_info.value.code == 400

    @patch('check_cert.sys.exit')
    @patch('check_cert.asyncio.run')
    @patch('check_cert.argparse.ArgumentParser.parse_args')
    def test_main_keyboard_interrupt(self, mock_parse_args, mock_asyncio_run, mock_sys_exit):
        """Test main function handling KeyboardInterrupt."""
        # Setup mock args
        mock_args = MagicMock()
        mock_args.domains = ["example.com"]
        mock_parse_args.return_value = mock_args
        
        # Setup asyncio.run to raise KeyboardInterrupt
        mock_asyncio_run.side_effect = KeyboardInterrupt()
        
        # Call main
        main()
        
        # Verify sys.exit was called with error code 408
        mock_sys_exit.assert_called_once_with(408)

    @patch('check_cert.sys.exit')
    @patch('check_cert.asyncio.run')
    @patch('check_cert.argparse.ArgumentParser.parse_args')
    def test_main_unexpected_exception(self, mock_parse_args, mock_asyncio_run, mock_sys_exit):
        """Test main function handling unexpected exception."""
        # Setup mock args
        mock_args = MagicMock()
        mock_args.domains = ["example.com"]
        mock_parse_args.return_value = mock_args
        
        # Setup asyncio.run to raise unexpected exception
        mock_asyncio_run.side_effect = Exception("Unexpected error")
        
        # Call main
        main()
        
        # Verify sys.exit was called with error code 500
        mock_sys_exit.assert_called_once_with(500)

    @patch('check_cert.sys.exit')
    @patch('check_cert.argparse.ArgumentParser.parse_args')
    def test_main_invalid_domain_whitespace_only(self, mock_parse_args, mock_sys_exit):
        """Test main function with whitespace-only domain."""
        # Setup mock args
        mock_args = MagicMock()
        mock_args.domains = ["   "]
        mock_parse_args.return_value = mock_args
        
        # Make sys.exit raise SystemExit to actually stop execution
        mock_sys_exit.side_effect = SystemExit(400)
        
        # Call main and expect SystemExit
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        # Verify the exit code
        assert exc_info.value.code == 400

    @patch('check_cert.sys.exit')
    @patch('check_cert.asyncio.run')
    @patch('check_cert.argparse.ArgumentParser.parse_args')
    def test_main_invalid_domain_multiple_dots(self, mock_parse_args, mock_asyncio_run, mock_sys_exit):
        """Test main function with domain that has multiple dots but is still invalid."""
        # Setup mock args
        mock_args = MagicMock()
        mock_args.domains = ["..."]
        mock_parse_args.return_value = mock_args
        
        # Setup asyncio.run to raise an exception (simulating network error)
        mock_asyncio_run.side_effect = Exception("Network error")
        
        # Make sys.exit raise SystemExit to actually stop execution
        mock_sys_exit.side_effect = SystemExit(500)
        
        # Call main and expect SystemExit
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        # Verify the exit code
        assert exc_info.value.code == 500


class TestIntegration:
    """Integration tests that test the full flow."""
    
    @pytest.mark.asyncio
    @patch('check_cert.get_cert_expiration_many')
    async def test_full_flow_single_domain(self, mock_get_cert_expiration_many):
        """Test the complete flow for a single domain."""
        # Setup mock
        valid_cert_data = CertExpirationData(
            expiry_date=datetime.datetime(2024, 12, 31, 23, 59, 59, tzinfo=datetime.timezone.utc),
            time_remaining_str="2 months, 15 days",
            is_expired=False,
            days_remaining=75
        )
        
        mock_result = CertExpirationResult(
            domain="example.com",
            data=valid_cert_data,
            error=None
        )
        mock_get_cert_expiration_many.return_value = create_async_iter([mock_result])
        
        # Capture output
        with redirect_stdout(io.StringIO()) as stdout:
            await check_domains(["example.com"])
            output = stdout.getvalue()
        
        # Verify complete output
        expected_output = """example.com
Certificate expires: 2024-12-31 23:59:59 UTC
Time Remaining: 2 months, 15 days
STATUS: VALID

"""
        assert output == expected_output

    @pytest.mark.asyncio
    @patch('check_cert.get_cert_expiration_many')
    async def test_full_flow_error_handling(self, mock_get_cert_expiration_many):
        """Test the complete flow with error handling."""
        # Setup mock with error
        mock_result = CertExpirationResult(
            domain="invalid.com",
            data=None,
            error="SSL handshake failed"
        )
        mock_get_cert_expiration_many.return_value = create_async_iter([mock_result])
        
        # Capture output
        with redirect_stdout(io.StringIO()) as stdout:
            await check_domains(["invalid.com"])
            output = stdout.getvalue()
        
        # Verify error output
        expected_output = """invalid.com
ERROR: SSL handshake failed

"""
        assert output == expected_output

    @pytest.mark.asyncio
    @patch('check_cert.get_cert_expiration_many')
    async def test_full_flow_mixed_results(self, mock_get_cert_expiration_many):
        """Test the complete flow with mixed success and error results."""
        # Setup mock with mixed results
        valid_cert_data = CertExpirationData(
            expiry_date=datetime.datetime(2024, 12, 31, 23, 59, 59, tzinfo=datetime.timezone.utc),
            time_remaining_str="2 months, 15 days",
            is_expired=False,
            days_remaining=75
        )
        
        expired_cert_data = CertExpirationData(
            expiry_date=datetime.datetime(2023, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc),
            time_remaining_str="EXPIRED",
            is_expired=True,
            days_remaining=-10
        )
        
        mock_results = [
            CertExpirationResult(domain="good.com", data=valid_cert_data, error=None),
            CertExpirationResult(domain="bad.com", data=None, error="Connection failed"),
            CertExpirationResult(domain="expired.com", data=expired_cert_data, error=None)
        ]
        mock_get_cert_expiration_many.return_value = create_async_iter(mock_results)
        
        # Capture output
        with redirect_stdout(io.StringIO()) as stdout:
            await check_domains(["good.com", "bad.com", "expired.com"])
            output = stdout.getvalue()
        
        # Verify all results are handled
        assert "good.com" in output
        assert "bad.com" in output
        assert "expired.com" in output
        assert "STATUS: VALID" in output
        assert "ERROR: Connection failed" in output
        assert "STATUS: EXPIRED" in output


# Parametrized tests for edge cases
class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("days_remaining,expected_status", [
        (0, "STATUS: EXPIRED"),
        (1, "STATUS: EXPIRING SOON (less than 30 days)"),
        (29, "STATUS: EXPIRING SOON (less than 30 days)"),
        (30, "STATUS: VALID"),
        (365, "STATUS: VALID"),
    ])
    @patch('check_cert.get_cert_expiration_many')
    async def test_status_boundary_conditions(self, mock_get_cert_expiration_many, days_remaining, expected_status):
        """Test status determination at boundary conditions."""
        # Create cert data with specific days remaining
        expiry_date = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=days_remaining)
        cert_data = CertExpirationData(
            expiry_date=expiry_date,
            time_remaining_str=f"{days_remaining} days",
            is_expired=days_remaining <= 0,
            days_remaining=days_remaining
        )
        
        mock_result = CertExpirationResult(
            domain="test.com",
            data=cert_data,
            error=None
        )
        mock_get_cert_expiration_many.return_value = create_async_iter([mock_result])
        
        # Capture output
        with redirect_stdout(io.StringIO()) as stdout:
            await check_domains(["test.com"])
            output = stdout.getvalue()
        
        # Verify expected status
        assert expected_status in output

    @pytest.mark.asyncio
    @pytest.mark.parametrize("error_message", [
        "Connection timeout",
        "SSL handshake failed",
        "Certificate verify failed",
        "Name or service not known",
        "Network is unreachable",
        "Connection refused",
    ])
    @patch('check_cert.get_cert_expiration_many')
    async def test_various_error_messages(self, mock_get_cert_expiration_many, error_message):
        """Test various error message formats."""
        mock_result = CertExpirationResult(
            domain="error.com",
            data=None,
            error=error_message
        )
        mock_get_cert_expiration_many.return_value = create_async_iter([mock_result])
        
        # Capture output
        with redirect_stdout(io.StringIO()) as stdout:
            await check_domains(["error.com"])
            output = stdout.getvalue()
        
        # Verify error message is displayed
        assert f"ERROR: {error_message}" in output