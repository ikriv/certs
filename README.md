# SSL Certificate Checker

## Motivation

[Let's Encrypt is ending support for expiration notification emails](https://letsencrypt.org/2025/01/22/ending-expiration-emails) on June 4, 2025. This project provides:
- A command-line tool to check certificate expiration
- An email alert script for cron-based monitoring  
- A web dashboard for visual monitoring

## Quick Start: Manual Check

Check certificate expiration from the command line (no dependencies required):

```bash
cd server/core
python check_cert.py google.com github.com example.com
```

## Cron Setup: Email Alerts

### 1. Create Configuration File

```bash
cp server/core/config.example.ini /etc/ssl-cert-alert.ini
```

Edit `/etc/ssl-cert-alert.ini`:

```ini
[email]
from = alerts@yourdomain.com
to = admin@yourdomain.com

[alerts]
# Send alerts when certificate expires in these many days
warning_days = 30,14,7,1

[domains]
list = yourdomain.com, api.yourdomain.com, mail.yourdomain.com
```

### 2. Test the Script

```bash
cd /path/to/server/core

# Preview email content without sending
python check_cert_email.py --config /etc/ssl-cert-alert.ini --dry-run

# Send a summary email for all domains (regardless of expiration status)
python check_cert_email.py --config /etc/ssl-cert-alert.ini --force
```

### 3. Add to Cron

```bash
crontab -e
```

Add:

```cron
# Check SSL certificates daily at 8 AM
0 8 * * * cd /path/to/server/core && python check_cert_email.py --config /etc/ssl-cert-alert.ini
```

**Note:** Requires `sendmail` configured on the system.

## Web Dashboard Deployment

The web dashboard runs as a Docker container. Apache or Nginx acts as a reverse proxy, forwarding requests to the container.

### 1. Start the Docker Container

```bash
# Build frontend first
cd frontend && npm install && npm run build && cd ..

# Start the server
docker-compose up -d
```

The container runs on port 5000.

### 2. Configure Reverse Proxy

Add to your existing site configuration to serve the dashboard at `/certs/`:

#### Apache

Enable required modules:

```bash
a2enmod proxy proxy_http
```

Add to your Apache virtual host:

```apache
# SSL Certificate Checker at /certs/
ProxyPass /certs/ http://127.0.0.1:5000/
ProxyPassReverse /certs/ http://127.0.0.1:5000/
```

#### Nginx

Add to your server block:

```nginx
# SSL Certificate Checker at /certs/
location /certs/ {
    proxy_pass http://127.0.0.1:5000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

The dashboard will be available at `https://yourdomain.com/certs/`.

## Development Setup

### Backend

```bash
cd server
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Backend runs on `http://localhost:3000`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:5000` and proxies API requests to the backend.

**Note:** Both servers must be running for the web dashboard to work in development.

## API

```bash
# Single domain
curl "http://localhost:5000/api/?domain=google.com"

# Multiple domains  
curl "http://localhost:5000/api/?domains=google.com,github.com"

# Streaming (for many domains)
curl -H "Accept: application/x-ndjson" "http://localhost:5000/api/?domains=google.com,github.com"
```
