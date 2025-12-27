"""
certcore - SSL Certificate Expiration Checker Core Library

A zero-dependency library for checking SSL certificate expiration dates.
Uses only Python standard library.
"""

from .schema import CertExpirationData, CertExpirationResult, CertExpirationHandler
from .expiration import (
    get_cert_expiration_data,
    get_cert_expiration_no_raise,
    get_cert_expiration_many,
)

__all__ = [
    "CertExpirationData",
    "CertExpirationResult",
    "CertExpirationHandler",
    "get_cert_expiration_data",
    "get_cert_expiration_no_raise",
    "get_cert_expiration_many",
]

