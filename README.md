# SSL Certificate Checker

A full-stack application for checking SSL certificate expiration information. Built with Next.js frontend and Quart (Python) backend, containerized with Docker.

## Project Structure

```
certs_new/
├── server/
│   ├── core/                    # Core library + CLI scripts (zero deps)
│   │   ├── schema.py            # Data classes
│   │   ├── expiration.py        # Certificate checking logic
│   │   ├── check_cert.py        # Console checker
│   │   ├── check_cert_email.py  # Email alert for cron
│   │   └── config.example.ini   # Example config file
│   ├── app.py                   # Web server (requires quart)
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                    # Next.js frontend
│   ├── src/
│   ├── out/                     # Static export (generated)
│   └── package.json
│
├── docker-compose.yml
└── README.md
```

## Standalone Scripts (Zero Dependencies)

The scripts in `server/core/` require only Python 3.11+ standard library. Run from the `core/` directory:

### Console Script

```bash
cd server/core
python check_cert.py google.com github.com example.com
```

### Email Alert Script (for cron)

```bash
cd server/core

# Create config file from example
cp config.example.ini /etc/cert_alert.ini

# Run the script
python check_cert_email.py --config /etc/cert_alert.ini google.com github.com

# Dry run (print email instead of sending)
python check_cert_email.py --config /etc/cert_alert.ini --dry-run google.com
```

**Configuration file format (INI):**

```ini
[email]
from = alerts@company.com
to = admin@company.com

[alerts]
warning_days = 7,14,30
```

**Cron example:**

```bash
0 8 * * * cd /path/to/server/core && python check_cert_email.py --config /etc/cert_alert.ini google.com github.com
```

## Quick Start (Web Application)

### 1. Build the Frontend

```bash
cd frontend
npm install
npm run build
cd ..
```

### 2. Run with Docker Compose

```bash
docker-compose up --build
```

The application will be available at `http://localhost:5000`.

## Development

### Backend (Quart Server)

```bash
cd server
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

### Frontend (Next.js Dev Server)

```bash
cd frontend
npm install
npm run dev
```

**Ports:**
- Frontend: 5000 (dev server)
- Backend: 3000 (dev mode)
- Docker: 5000 (serves both)

## API Usage

```bash
# Single domain
curl "http://localhost:5000/api/?domain=google.com"

# Multiple domains
curl "http://localhost:5000/api/?domains=google.com,github.com"

# Streaming (NDJSON)
curl -H "Accept: application/x-ndjson" "http://localhost:5000/api/?domains=google.com,github.com"
```

## Dependencies

| Component | External Dependencies |
|-----------|----------------------|
| `server/core/` | None (stdlib only) |
| `server/app.py` | quart |
