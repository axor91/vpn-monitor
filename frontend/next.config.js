/** @type {import('next').NextConfig} */
const nextConfig = {
  basePath: "/vpn-monitor",
  output: "standalone",
  async rewrites() {
    const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8052";
    return [
      {
        source: "/vpn-monitor/api/:path*",
        destination: `${apiBase}/vpn-monitor/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
