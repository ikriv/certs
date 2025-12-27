# SSL Certificate Checker

A full-stack application for checking SSL certificate expiration information. Built with Next.js frontend and Quart (Python) backend, containerized with Docker.

## Architecture

- **Frontend**: Next.js (static export) - React-based UI
- **Backend**: Quart (Python) - Serves static files and provides API endpoints
- **Containerization**: Docker Compose for easy deployment

## Prerequisites

- Docker and Docker Compose
- Node.js 18+ and npm (for building frontend)
- Python 3.11+ (for local development)

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
python check_cert_server.py
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

## Project Structure

```
certs_new/
├── frontend/          # Next.js frontend application
│   ├── src/
│   ├── out/          # Static export output (generated)
│   └── package.json
├── server/           # Quart backend
│   ├── check_cert_server.py
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml
└── README.md
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

