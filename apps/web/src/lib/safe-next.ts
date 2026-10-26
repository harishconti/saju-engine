/**
 * The single validator for a post-sign-in `next` target (AU-06).
 *
 * `next` arrives from the query string, so passing it straight to a redirect is an open redirect.
 * The check resolves the candidate against a fixed origin and requires it to stay there, rather
 * than trusting a prefix: `/\evil.com` starts with a single `/` and becomes `//evil.com` once a
 * browser normalises the backslash. A backslash is rejected outright as well — including the
 * percent-encoded `%5C` — and so are control characters, which URL parsers strip or reinterpret.
 */
const SENTINEL_ORIGIN = "https://example.invalid";
const CONTROL_CHARACTERS = /[\u0000-\u001f\u007f]/;

export function safeNext(raw: string | null | undefined, fallback = "/dashboard"): string {
  if (!raw || !raw.startsWith("/") || raw.startsWith("//")) return fallback;
  if (CONTROL_CHARACTERS.test(raw)) return fallback;

  let decoded: string;
  try {
    decoded = decodeURIComponent(raw);
  } catch {
    return fallback; // malformed escape: not a target we can vouch for
  }
  // Decode exactly once: `%5C` is an encoded backslash, and `/%2F%2Fevil.com` an encoded `///…`.
  if (decoded.includes("\\") || decoded.startsWith("//") || CONTROL_CHARACTERS.test(decoded)) return fallback;

  let resolved: URL;
  try {
    resolved = new URL(raw, SENTINEL_ORIGIN);
  } catch {
    return fallback;
  }
  return resolved.origin === SENTINEL_ORIGIN ? raw : fallback;
}
