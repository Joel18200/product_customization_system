import type { NextConfig } from "next";
import os from "os";

/**
 * Collect every local IPv4 address (e.g. 192.168.x.x, 10.x.x.x) so the
 * dev server's printed "Network" URL is treated as a trusted origin.
 *
 * Next.js blocks cross-origin requests to dev-only assets (/_next/static/*,
 * HMR websocket) by default. Without this, loading the app from the Network
 * URL on another device gets the HTML shell but no JS chunks -> blank page.
 */
function localNetworkOrigins(): string[] {
  const origins = new Set<string>();
  const ifaces = os.networkInterfaces();
  for (const name of Object.keys(ifaces)) {
    for (const net of ifaces[name] ?? []) {
      if (net.family === "IPv4" && !net.internal) {
        origins.add(net.address);
      }
    }
  }
  return [...origins];
}

const nextConfig: NextConfig = {
  // Allow the LAN/Network URL(s) to load dev assets and connect to HMR.
  allowedDevOrigins: localNetworkOrigins(),
};

export default nextConfig;
