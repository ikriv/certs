# SSL Certificate Checker Server

A Quart-based web server for checking SSL certificate expiration information for domains.

## Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

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
python check_cert_server.py
```

The server will start on `http://0.0.0.0:5000` (accessible at `http://localhost:5000`).

## API Endpoints

### Check Certificate Status
`GET /?domain=<domain>` or `GET /?domains=<domain1>,<domain2>,...`

Check SSL certificate expiration for one or more domains.

**Examples:**
- Single domain: `http://localhost:5000/?domain=google.com`
- Multiple domains: `http://localhost:5000/?domains=google.com,github.com,example.com`

**Streaming Response:**
Set the `Accept` header to `application/x-ndjson` for streaming results when checking multiple domains.

### Health Check
`GET /status`

Returns server status information.

## Development

The server runs in debug mode when started locally, which enables auto-reload on code changes.

