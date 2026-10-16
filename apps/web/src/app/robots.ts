import type { MetadataRoute } from "next";

/**
 * robots.txt
 *
 * Blocks the operational surface (`/api/*`, the dashboard, the admin console) and points crawlers at
 * the sitemap. Preview deployments are protected separately by Vercel's Deployment Protection.
 */
export default function robots(): MetadataRoute.Robots {
  const base = (process.env.NEXT_PUBLIC_APP_URL ?? "https://www.cosmicsaju.com").replace(/\/+$/, "");

  return {
    rules: [
      {
        userAgent: "*",
        allow: ["/", "/sample", "/privacy", "/terms", "/refund-policy", "/demo/"],
        disallow: ["/api/", "/dashboard", "/dashboard/", "/admin", "/admin/", "/auth/", "/login"],
      },
    ],
    sitemap: `${base}/sitemap.xml`,
    host: base,
  };
}
