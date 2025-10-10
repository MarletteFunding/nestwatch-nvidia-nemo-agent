/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  // Temporarily disable rewrites to fix Next.js error
  // async rewrites() {
  //   return [
  //     {
  //       source: '/api/backend/chat',
  //       destination: 'http://localhost:8000/api/v1/chat',
  //     },
  //     {
  //       source: '/api/backend/api/v1/:path*',
  //       destination: 'http://localhost:8000/api/v1/:path*',
  //     },
  //     {
  //       source: '/api/backend/event_interactions/:path*',
  //       destination: 'http://localhost:8000/event_interactions/:path*',
  //     },
  //   ];
  // },
};

module.exports = nextConfig;
