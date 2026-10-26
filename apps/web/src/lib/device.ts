/**
 * A short, honest device name from a user-agent string (AU-40 / D6).
 *
 * The account page shows where a user is signed in. A raw user-agent is unreadable and long, and a
 * confident wrong guess is worse than an admission, so anything unrecognised is "Unknown device".
 *
 * Order matters in both halves: Edge and Opera also claim Chrome, Chrome on iOS is `CriOS`, every
 * Android UA contains "Linux", and an iPhone UA contains "like Mac OS X".
 */
export function describeUserAgent(userAgent: string | null | undefined): string {
  const ua = (userAgent ?? "").trim();
  if (!ua) return "Unknown device";

  const browser = /Edg\//.test(ua)
    ? "Edge"
    : /OPR\//.test(ua)
      ? "Opera"
      : /Firefox\//.test(ua)
        ? "Firefox"
        : /CriOS\//.test(ua)
          ? "Chrome"
          : /Chrome\//.test(ua)
            ? "Chrome"
            : /Safari\//.test(ua)
              ? "Safari"
              : null;

  const platform = /iPhone|iPad|iPod/.test(ua)
    ? "iOS"
    : /Android/.test(ua)
      ? "Android"
      : /Windows/.test(ua)
        ? "Windows"
        : /Macintosh|Mac OS X/.test(ua)
          ? "macOS"
          : /Linux/.test(ua)
            ? "Linux"
            : null;

  if (browser && platform) return `${browser} on ${platform}`;
  return browser ?? platform ?? "Unknown device";
}
