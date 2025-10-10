/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  env: {
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8081',
  },
  async rewrites() {
    // For production, use Cloud Run service URLs
    const isProduction = process.env.NODE_ENV === 'production'
    
    if (isProduction) {
      // Use numeric project ID for Cloud Run URLs
      const projectNumericId = '117860496175'
      const region = 'us-central1'
      return [
        {
          source: '/api/chat/:path*',
          destination: `https://project-agent-chat-api-${projectNumericId}.${region}.run.app/:path*`,
        },
        {
          source: '/api/inventory/:path*',
          destination: `https://project-agent-admin-api-${projectNumericId}.${region}.run.app/inventory/:path*`,
        },
        {
          source: '/api/documents/:path*',
          destination: `https://project-agent-documents-api-${projectNumericId}.${region}.run.app/:path*`,
        },
        {
          source: '/api/admin/:path*',
          destination: `https://project-agent-admin-api-${projectNumericId}.${region}.run.app/admin/:path*`,
        },
        {
          source: '/api/upload/:path*',
          destination: `https://project-agent-upload-api-${projectNumericId}.${region}.run.app/:path*`,
        },
      ]
    }
    
    // For development, use localhost
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
        destination: 'http://localhost:8084/admin/:path*',
      },
      {
        source: '/api/upload/:path*',
        destination: 'http://localhost:8085/:path*',
      },
    ]
  },
}

module.exports = nextConfig
