# SSL Certificate Checker Server

A Quart-based web server for checking SSL certificate expiration information for domains.

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

## Dependencies

This server requires `quart`. The core certificate checking logic is in `certcore/` (no external dependencies).

## Setup

1. Navigate to the server directory:
```bash
cd server
```

2. Create a virtual environment:
```bash
python -m venv .venv
```

3. Activate the virtual environment:

   **On Windows:**
   ```bash
   .venv\Scripts\activate
   ```

   **On macOS/Linux:**
   ```bash
   source .venv/bin/activate
   ```

## Installation

Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Server

Start the server locally:
```bash
python app.py
```

The server will start on `http://0.0.0.0:3000` (accessible at `http://localhost:3000`) in development mode.

**Note**: In Docker mode, the server runs on port 5000 and serves both the frontend and API. In development mode, it runs on port 3000 and only serves the API (frontend runs separately on port 5000).

## API Endpoints

### Check Certificate Status
`GET /?domain=<domain>` or `GET /?domains=<domain1>,<domain2>,...`

Check SSL certificate expiration for one or more domains.

**Examples:**
- Single domain: `http://localhost:3000/api/?domain=google.com` (dev mode)
- Multiple domains: `http://localhost:3000/api/?domains=google.com,github.com,example.com` (dev mode)
- Docker mode: `http://localhost:5000/api/?domain=google.com`

**Streaming Response:**
Set the `Accept` header to `application/x-ndjson` for streaming results when checking multiple domains.

### Health Check
`GET /api/status`

Returns server status information.

**Examples:**
- Dev mode: `http://localhost:3000/api/status`
- Docker mode: `http://localhost:5000/api/status`

## Development

The server runs in debug mode when started locally, which enables auto-reload on code changes.
