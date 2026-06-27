import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  transpilePackages: ["@hubei-gaokao-advisor/shared-types"],
  allowedDevOrigins: ["127.0.0.1"],
};

export default nextConfig;

