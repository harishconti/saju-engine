import type { NextConfig } from "next";
import path from "path";

const r2 = "https://*.r2.cloudflarestorage.com";
// Cloudflare Turnstile (bot protection on the free-sample form). It needs:
//   script-src  — to load https://challenges.cloudflare.com/turnstile/v0/api.js
//   frame-src   — the widget is rendered in an iframe served from that origin
// The challenge itself is then fetched from a REGIONAL subdomain (observed:
// hagen.challenges.cloudflare.com), so the wildcard is required as well as the bare host — a CSP
// source of `https://challenges.cloudflare.com` matches that host only, never its subdomains.
// (Adding the bare host is still right: `*.challenges.cloudflare.com` does not match it.)
// Omitting any of these does not throw: the widget simply never completes, and because the client
// treats an unverified widget as "not yet done", every submission is then blocked and no visitor can
// take a free snapshot. The funnel dies silently.
const turnstileHosts = "https://challenges.cloudflare.com https://*.challenges.cloudflare.com";
// Google Fonts, loaded by a <link> in app/layout.tsx. `style-src` covers the stylesheet and
// `font-src` the font files themselves; without both, the three brand faces silently fall back.
const googleFontsCss = "https://fonts.googleapis.com";
const googleFontsFiles = "https://fonts.gstatic.com";
const isProd = process.env.NODE_ENV === "production";

/**
 * CSP + security headers.
 *
 * `frame-src 'self'` allows the admin console to embed a presigned R2 PDF in an <iframe>.
 * `connect-src`/`img-src` allow R2. `'unsafe-inline'` for styles is required by Next's
 * injected critical CSS; scripts stay strict in production.
 *
 * NOTE for a future privacy pass: the Google Fonts entries make every visitor's browser call
 * Google, which shares their IP. Self-hosting the three faces under `public/fonts/` would drop
 * those two sources entirely and is the better answer for a product with a privacy policy — see
 * docs/webapp/10-privacy-and-compliance.md.
 */
const csp = [
  "default-src 'self'",
  `script-src 'self' 'unsafe-inline' ${turnstileHosts}${isProd ? "" : " 'unsafe-eval'"}`,
  `style-src 'self' 'unsafe-inline' ${googleFontsCss}`,
  `img-src 'self' data: blob: ${r2}`,
  `font-src 'self' data: ${googleFontsFiles}`,
  `connect-src 'self' ${r2} https://api.resend.com ${turnstileHosts}`,
  `frame-src 'self' blob: ${r2} ${turnstileHosts}`,
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
  /**
   * `src/lib/city-data.server.ts` reads `public/city-index.json` at import time, so every function that
   * resolves a birthplace needs the file beside it. A `readFileSync(path.join(process.cwd(), …))` is
   * invisible to Next's output tracing — the build succeeds and the *deploy* fails at request time with
   * ENOENT, which is the worst place to find out. Listed explicitly instead.
   */
  outputFileTracingIncludes: {
    "/**/*": ["./public/city-index.json"],
  },
  // Pin the workspace root so Next does not climb to a parent directory that has a stray lockfile.
  turbopack: {
    root: path.resolve(process.cwd()),
  },
  async headers() {
    return [{ source: "/(.*)", headers: securityHeaders }];
  },
};

export default nextConfig;
