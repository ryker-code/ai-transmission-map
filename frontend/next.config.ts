import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  images: {
    domains: ["bloomberg.com", "www.bloomberg.com"],
  },
};

export default nextConfig;
