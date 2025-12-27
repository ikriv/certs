# SSL Certificate Checker Server

A Quart-based web server for checking SSL certificate expiration.

## Prerequisites

- Python 3.11+
- pip

## Dependencies

This server requires `quart`. The core logic is in `cli/` (no external dependencies).

## Setup

```bash
cd server
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Running

```bash
python app.py
```

Server runs on `http://localhost:3000` (dev mode) or `http://localhost:5000` (Docker).

## API Endpoints

- `GET /api/?domain=google.com` - Check single domain
- `GET /api/?domains=google.com,github.com` - Check multiple domains
- `GET /api/status` - Health check

Set `Accept: application/x-ndjson` header for streaming results.
