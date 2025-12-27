# SSL Certificate Checker

A full-stack application for checking SSL certificate expiration information. Built with Next.js frontend and Quart (Python) backend, containerized with Docker.

## Architecture

- **certcore/**: Core library (zero external dependencies)
- **scripts/**: Standalone CLI scripts (zero external dependencies)
- **server/**: Web server (requires quart)
- **frontend/**: Next.js (static export) - React-based UI

## Prerequisites

- Docker and Docker Compose
- Node.js 18+ and npm (for building frontend)
- Python 3.11+ (for local development and scripts)

## Project Structure

```
certs_new/
├── certcore/                # Core library (zero deps)
│   ├── __init__.py
│   ├── expiration.py        # Certificate checking logic
│   └── schema.py            # Data classes
│
├── scripts/                 # Standalone scripts (zero deps)
│   ├── check_cert.py        # Console checker
│   ├── check_cert_email.py  # Email alert for cron
│   └── config.example.ini   # Example config file
│
├── server/                  # Web server (requires quart)
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                # Next.js frontend
│   ├── src/
│   ├── out/                 # Static export (generated)
│   └── package.json
│
├── docker-compose.yml
└── README.md
```

## Quick Start

### 1. Build the Frontend

First, build the Next.js frontend as a static export:

```bash
cd frontend
npm install
npm run build
cd ..
```

This creates the `frontend/out` directory with static files.

### 2. Run with Docker Compose

From the project root:

```bash
docker-compose up --build
```

The application will be available at `http://localhost:5000`.

### 3. Access the Application

- **Frontend**: `http://localhost:5000`
- **API Endpoint**: `http://localhost:5000/api/?domain=google.com`
- **Health Check**: `http://localhost:5000/api/status`

## Standalone Scripts (Zero Dependencies)

The scripts in `scripts/` directory require only Python 3.11+ standard library.

### Console Script

Check certificate expiration from the command line:

```bash
cd scripts
python check_cert.py google.com github.com example.com
```

### Email Alert Script (for cron)

Send email alerts for expiring certificates:

```bash
# Create config file from example
cp scripts/config.example.ini /etc/cert_alert.ini
# Edit with your email settings
nano /etc/cert_alert.ini

# Run the script
python scripts/check_cert_email.py --config /etc/cert_alert.ini google.com github.com

# Dry run (print email instead of sending)
python scripts/check_cert_email.py --config /etc/cert_alert.ini --dry-run google.com
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
0 8 * * * /usr/bin/python3 /path/to/scripts/check_cert_email.py --config /etc/cert_alert.ini google.com github.com
```

## Development

### Development Mode (Separate Frontend and Backend)

In development mode, the frontend and backend run separately:

**Frontend (Next.js Dev Server):**
```bash
cd frontend
npm install
npm run dev
```

The frontend dev server runs on `http://localhost:5000` and proxies API requests to the backend.

**Backend (Quart Server):**
```bash
cd server
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

The backend runs on `http://localhost:3000` (default port).

**Port Configuration:**
- **Frontend**: Port 5000 (dev server)
- **Backend**: Port 3000 (dev mode)
- **Docker**: Port 5000 (Quart serves both frontend and backend)

**Note**: Both servers must be running for the application to work in dev mode. The frontend proxies `/api/*` requests to `http://localhost:3000`.

### Environment Variables

#### Frontend

Create `frontend/.env.local`:

```bash
NEXT_PUBLIC_DOMAINS_TO_CHECK=google.com;microsoft.com;github.com
```

Domains should be semicolon-separated. Defaults to `google.com;microsoft.com` if not set.

#### Backend

No environment variables required for basic operation.

## Docker Details

### Building the Image

```bash
docker-compose build
```

### Running in Detached Mode

```bash
docker-compose up -d
```

### Viewing Logs

```bash
docker-compose logs -f backend
```

### Stopping the Container

```bash
docker-compose down
```

### Rebuilding After Changes

```bash
docker-compose up --build
```

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

## Production Deployment

### Building for Production

1. Build the frontend:
   ```bash
   cd frontend
   npm run build
   ```

2. Build and run Docker container:
   ```bash
   docker-compose up --build -d
   ```

### Using with Apache/Nginx

The Quart server can be reverse-proxied through Apache or Nginx:

**Apache Example:**
```apache
ProxyPass / http://localhost:5000/
ProxyPassReverse / http://localhost:5000/
```

**Nginx Example:**
```nginx
location / {
    proxy_pass http://localhost:5000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

## Dependencies Summary

| Component | External Dependencies |
|-----------|----------------------|
| `certcore/` | None (stdlib only) |
| `scripts/` | None (stdlib only) |
| `server/` | quart |

## Troubleshooting

### Frontend not loading

- Ensure `frontend/out` directory exists (run `npm run build` in frontend directory)
- Check that the volume mount in `docker-compose.yml` is correct

### API requests failing

- Verify the backend container is running: `docker-compose ps`
- Check backend logs: `docker-compose logs backend`
- Ensure port 5000 is not already in use

### Static files not found

- Rebuild the frontend: `cd frontend && npm run build`
- Restart the Docker container: `docker-compose restart`

## License

[Add your license here]
