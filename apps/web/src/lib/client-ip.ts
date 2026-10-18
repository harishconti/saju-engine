/**
 * The caller's IP, from a header we can trust.
 *
 * Rate limits key on this value, so a spoofable source makes every IP-based limit
 * bypassable. `x-forwarded-for` is a comma-separated list that a client can prepend to;
 * the leftmost entry is therefore *not* trustworthy in general. On Vercel the platform
 * supplies `x-vercel-forwarded-for` and `x-real-ip`, which we prefer. If only the raw
 * header is available, take the **rightmost** hop — the address the nearest proxy
 * actually observed — rather than the client-controlled leftmost one.
 *
 * Contract: docs/webapp/14-security.md (§ Rate limiting).
 */

function first(value: string): string {
  return value.split(",")[0]?.trim() ?? "";
}

function last(value: string): string {
  const parts = value.split(",");
  return parts[parts.length - 1]?.trim() ?? "";
}

export function clientIp(req: Request): string {
  // Vercel sets this at the edge from the connection, so its first entry is the peer.
  const vercel = req.headers.get("x-vercel-forwarded-for");
  if (vercel && first(vercel)) return first(vercel);

  const real = req.headers.get("x-real-ip");
  if (real?.trim()) return real.trim();

  const forwarded = req.headers.get("x-forwarded-for");
  if (forwarded && last(forwarded)) return last(forwarded);

  return "unknown";
}
