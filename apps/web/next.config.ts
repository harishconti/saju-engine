import type { NextConfig } from "next";
import path from "path";

const r2 = "https://*.r2.cloudflarestorage.com";
const isProd = process.env.NODE_ENV === "production";

/**
 * CSP + security headers.
 *
 * `frame-src 'self'` allows the admin console to embed a presigned R2 PDF in an <iframe>.
 * `connect-src`/`img-src` allow R2. `'unsafe-inline'` for styles is required by Next's
 * injected critical CSS; scripts stay strict in production.
 */
const csp = [
  "default-src 'self'",
  `script-src 'self' 'unsafe-inline'${isProd ? "" : " 'unsafe-eval'"}`,
  "style-src 'self' 'unsafe-inline'",
  `img-src 'self' data: blob: ${r2}`,
  "font-src 'self' data:",
  `connect-src 'self' ${r2} https://api.resend.com`,
  `frame-src 'self' blob: ${r2}`,
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "frame-ancestors 'none'",
].join("; ");

const securityHeaders = [
  { key: "Content-Security-Policy", value: csp },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=(), interest-cohort=()" },
  { key: "X-DNS-Prefetch-Control", value: "on" },
  ...(isProd
    ? [{ key: "Strict-Transport-Security", value: "max-age=63072000; includeSubDomains; preload" }]
    : []),
];

const nextConfig: NextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  // Pin the workspace root so Next does not climb to a parent directory that has a stray lockfile.
  turbopack: {
    root: path.resolve(process.cwd()),
  },
  async headers() {
    return [{ source: "/(.*)", headers: securityHeaders }];
  },
};

export default nextConfig;
