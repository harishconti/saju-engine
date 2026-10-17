import type { Metadata, Viewport } from "next";
import { Analytics } from "@vercel/analytics/next";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_APP_URL ?? "https://cosmicsaju.com"),
  title: {
    default: "Cosmic Saju — Korean Four Pillars readings",
    template: "%s · Cosmic Saju",
  },
  description:
    "Korean Saju (Four Pillars) readings grounded in classical principles. An accurate engine and an honest interpreter — not a Korean master.",
  applicationName: "Cosmic Saju",
  openGraph: {
    title: "Cosmic Saju — Korean Four Pillars readings",
    description:
      "An accurate engine and an honest interpreter — not a Korean master. Start with a free chart snapshot.",
    type: "website",
    siteName: "Cosmic Saju",
  },
  robots: { index: true, follow: true },
};

export const viewport: Viewport = {
  themeColor: "#08080d",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        {/* Loaded via <link> rather than next/font so the build has no network dependency. */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400&family=IBM+Plex+Mono:wght@400;500&family=Inter:wght@300;400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-screen antialiased">
        {children}
        {/* Vercel Web Analytics: cookieless, aggregate page views. Served same-origin
            (`/_vercel/insights/script`), so the CSP's `script-src 'self'` already covers it and no
            `next.config.ts` change is needed — verified against the installed package rather than
            assumed, because a blocked script fails *silently* (see the Google Fonts incident in
            docs/webapp/13-launch-audit.md).

            NOTE: this component returns null on the server and injects its tag in a client effect,
            so it never appears in the page source. Do not "fix" its absence there. */}
        <Analytics />
      </body>
    </html>
  );
}
