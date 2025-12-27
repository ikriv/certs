# SSL Certificate Checker Server

## Structure

```
server/
├── core/                    # Core library + CLI (zero deps)
│   ├── schema.py
│   ├── expiration.py
│   ├── check_cert.py
│   ├── check_cert_email.py
│   └── config.example.ini
├── app.py                   # Web server (requires quart)
├── requirements.txt
└── Dockerfile
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

## CLI Scripts (run from core/ directory)

```bash
cd core
python check_cert.py google.com
python check_cert_email.py --config config.example.ini --dry-run google.com
```

## API

- `GET /api/?domain=google.com`
- `GET /api/?domains=google.com,github.com`
- `GET /api/status`
