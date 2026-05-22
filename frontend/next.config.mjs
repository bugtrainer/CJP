/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'https://cjp-production.up.railway.app/api/:path*',
      },
    ]
  },
}

export default nextConfig;
