# SSL Certificate Checker

A full-stack application for checking SSL certificate expiration information. Built with Next.js frontend and Quart (Python) backend, containerized with Docker.

## Architecture

- **cli/**: Core library + standalone scripts (zero external dependencies)
- **server/**: Web server (requires quart)
- **frontend/**: Next.js (static export) - React-based UI

## Project Structure

```
certs_new/
├── cli/                         # Standalone tools (zero deps)
│   ├── schema.py                # Data classes
│   ├── expiration.py            # Certificate checking logic
│   ├── check_cert.py            # Console checker
│   ├── check_cert_email.py      # Email alert for cron
│   └── config.example.ini       # Example config file
│
├── server/                      # Web server (requires quart)
│   ├── app.py
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

The scripts in `cli/` require only Python 3.11+ standard library. Run from the `cli/` directory:

### Console Script

```bash
cd cli
python check_cert.py google.com github.com example.com
```

### Email Alert Script (for cron)

```bash
cd cli

# Create config file from example
cp config.example.ini /etc/cert_alert.ini
# Edit with your email settings

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
# Check certificates daily at 8 AM
0 8 * * * cd /path/to/cli && /usr/bin/python3 check_cert_email.py --config /etc/cert_alert.ini google.com github.com
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

### 3. Access the Application

- **Frontend**: `http://localhost:5000`
- **API Endpoint**: `http://localhost:5000/api/?domain=google.com`
- **Health Check**: `http://localhost:5000/api/status`

## Development

### Development Mode (Separate Frontend and Backend)

**Frontend (Next.js Dev Server):**
```bash
cd frontend
npm install
npm run dev
```

**Backend (Quart Server):**
```bash
cd server
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

**Ports:**
- Frontend: 5000 (dev server)
- Backend: 3000 (dev mode)
- Docker: 5000 (serves both)

## API Usage

### Check Single Domain

```bash
curl "http://localhost:5000/api/?domain=google.com"
```

### Check Multiple Domains

```bash
curl "http://localhost:5000/api/?domains=google.com,github.com,example.com"
```

### Streaming Response (NDJSON)

```bash
curl -H "Accept: application/x-ndjson" "http://localhost:5000/api/?domains=google.com,github.com"
```

## Dependencies Summary

| Component | External Dependencies |
|-----------|----------------------|
| `cli/` | None (stdlib only) |
| `server/` | quart |

## Prerequisites

- Docker and Docker Compose (for web app)
- Node.js 18+ and npm (for building frontend)
- Python 3.11+ (for CLI scripts and local development)
