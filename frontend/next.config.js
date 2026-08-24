/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',

  async rewrites() {
    // 服务端 rewrite：浏览器请求 /api/v1/* → 代理到后端
    // API_BACKEND_URL 是服务端变量（Docker 内部可解析 backend hostname）
    // NEXT_PUBLIC_API_URL 是客户端变量（浏览器不能解析 Docker hostname）
    const backendUrl = process.env.API_BACKEND_URL
      || process.env.NEXT_PUBLIC_API_URL
      || 'http://localhost:8000';
    return [
      {
        source: '/api/:path*',
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },

  images: {
    remotePatterns: [],
  },
};

module.exports = nextConfig;
