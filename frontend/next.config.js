/** @type {import('next').NextConfig} */
const isProduction = process.env.NODE_ENV === 'production';

const nextConfig = {
    // Read basePath from env var (e.g., '/certs'). Empty string = no basePath.
    basePath: process.env.NEXT_PUBLIC_BASE_PATH || '',

    // Enable static export only for production builds (not dev mode)
    // This allows rewrites to work in dev mode
    ...(isProduction ? { output: 'export' } : {}),

    // API proxy for development mode only
    // Rewrites don't work with static export, so we only enable them in dev
    async rewrites() {
        if (isProduction) {
            return [];
        }
        return [
            {
                source: '/api/:path*',
                destination: 'http://localhost:3000/api/:path*',  // Backend runs on 3000 in dev, preserve /api path
            },
            {
                source: '/api',
                destination: 'http://localhost:3000/api',  // Handle /api without trailing slash
            },
        ];
    },
};

module.exports = nextConfig;

