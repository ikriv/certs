# SSL Certificate Checker Frontend

Next.js frontend application for checking SSL certificate expiration.

## Prerequisites

- Node.js 18+ and npm
- Backend server running on `http://localhost:5000` (see `../server/README.md`)

## Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

## Development

Start the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`.

The Next.js dev server is configured to proxy API requests from `/api/*` to `http://localhost:5000/*`, so make sure the Quart backend is running.

## Building for Production

Build the application:
```bash
npm run build
```

Start the production server:
```bash
npm start
```

## Features

- Check SSL certificate expiration for one or more domains
- Real-time status indicators (Valid, Expiring Soon, Expired)
- Input field to specify domains to check
- Responsive table layout with Tailwind CSS

