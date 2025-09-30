/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  env: {
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8081',
  },
  async rewrites() {
    return [
      {
        source: '/api/chat/:path*',
        destination: 'http://localhost:8081/:path*',
      },
      {
        source: '/api/inventory/:path*',
        destination: 'http://localhost:8082/:path*',
      },
      {
        source: '/api/documents/:path*',
        destination: 'http://localhost:8083/:path*',
      },
      {
        source: '/api/admin/:path*',
        destination: 'http://localhost:8084/:path*',
      },
    ]
  },
}

module.exports = nextConfig
