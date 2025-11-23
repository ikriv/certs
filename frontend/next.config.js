/** @type {import('next').NextConfig} */
const nextConfig = {
    // If deploying under a subpath (e.g., /certs)
    // basePath: '/certs',

    // API proxy for development
    async rewrites() {
        return [
            {
                source: '/api/:path*',
                destination: 'http://localhost:5000/:path*',
            },
        ];
    },
};

module.exports = nextConfig;

