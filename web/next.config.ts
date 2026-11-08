import type { NextConfig } from "next";

// Where the FastAPI backend runs. The browser always calls /api on this origin;
// the rewrite below forwards those requests, so no CORS setup is needed.
const API_URL = process.env.API_URL ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true,
  typedRoutes: true,
  devIndicators: false,
  experimental: {
    // The /api proxy: uploads may be up to 20 MB (the API's limit), and a chat answer from a
    // busy model can take longer than the 30 second default
    proxyClientMaxBodySize: "21mb",
    proxyTimeout: 120_000,
  },
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${API_URL}/api/:path*` }];
  },
};

export default nextConfig;
