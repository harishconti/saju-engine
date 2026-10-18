import { describe, expect, it } from "vitest";

import { clientIp } from "@/lib/client-ip";

function request(headers: Record<string, string>): Request {
  return new Request("https://www.cosmicsaju.com/api/sample", { headers });
}

describe("clientIp", () => {
  it("prefers Vercel's own header over a client-supplied X-Forwarded-For", () => {
    const req = request({
      "x-forwarded-for": "1.2.3.4", // attacker-supplied
      "x-vercel-forwarded-for": "9.9.9.9",
    });
    expect(clientIp(req)).toBe("9.9.9.9");
  });

  it("uses x-real-ip when the Vercel header is absent", () => {
    const req = request({ "x-real-ip": "203.0.113.7", "x-forwarded-for": "1.2.3.4" });
    expect(clientIp(req)).toBe("203.0.113.7");
  });

  it("takes the rightmost X-Forwarded-For hop, not the spoofable leftmost", () => {
    const req = request({ "x-forwarded-for": "6.6.6.6, 203.0.113.7" });
    expect(clientIp(req)).toBe("203.0.113.7");
  });

  it("returns a stable fallback when no address header is present", () => {
    expect(clientIp(request({}))).toBe("unknown");
  });
});
