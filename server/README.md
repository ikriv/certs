# Server

Quart-based web server and CLI tools for SSL certificate checking.

## Structure

```
server/
├── core/                        # Core library + CLI (zero dependencies)
│   ├── schema.py                # Data classes: CertExpirationData, CertExpirationResult
│   ├── expiration.py            # Certificate checking: get_cert_expiration_many()
│   ├── check_cert.py            # CLI: console output
│   ├── check_cert_email.py      # CLI: email alerts
│   └── config.example.ini       # Example email configuration
│
├── app.py                       # Web server (requires quart)
├── requirements.txt             # Python dependencies (quart only)
├── Dockerfile
└── test_check_cert.py           # Unit tests
```

## Dependencies

| Component | External Dependencies |
|-----------|----------------------|
| `core/` | None (Python 3.11+ stdlib only) |
| `app.py` | quart |

## CLI Tools

Run from the `core/` directory:

```bash
cd core

# Console check
python check_cert.py google.com github.com

# Email alert (dry run)
python check_cert_email.py --config config.example.ini --dry-run google.com

# Email alert (actual)
python check_cert_email.py --config /etc/ssl-cert-alert.ini google.com
```

## Web Server

### Local Development

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Runs on `http://localhost:3000`.

### Docker

```bash
docker build -t ssl-checker .
docker run -p 5000:5000 -v /path/to/frontend/out:/app/static:ro ssl-checker
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/?domain=example.com` | Check single domain |
| `GET /api/?domains=a.com,b.com` | Check multiple domains |
| `GET /api/status` | Health check |

### Streaming

Set `Accept: application/x-ndjson` header for newline-delimited JSON streaming.

## Core Library API

```python
from core.expiration import get_cert_expiration_many
from core.schema import CertExpirationResult

async for result in get_cert_expiration_many(["google.com", "github.com"]):
    if result.error:
        print(f"{result.domain}: ERROR - {result.error}")
    else:
        print(f"{result.domain}: {result.data.days_remaining} days remaining")
```
