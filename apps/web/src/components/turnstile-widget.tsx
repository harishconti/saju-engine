"use client";

import { useEffect, useRef } from "react";

/**
 * Cloudflare Turnstile widget.
 *
 * Renders nothing and reports nothing when `NEXT_PUBLIC_TURNSTILE_SITE_KEY` is unset, so local
 * development works without keys. The server is what enforces the control (`lib/turnstile.ts`),
 * and it fails closed only once `TURNSTILE_SECRET_KEY` exists.
 *
 * The script is injected by hand rather than through `next/script` so this stays independent of
 * Next's script-injection semantics, and rendered in **explicit** mode so a used token can be
 * reset — Turnstile tokens are single-use, so a retry after a failed submit needs a fresh one.
 */

const SITE_KEY = process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY;
const SCRIPT_ID = "cf-turnstile-script";
const SCRIPT_SRC = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";

interface TurnstileApi {
  render: (el: HTMLElement, opts: Record<string, unknown>) => string;
  reset: (widgetId?: string) => void;
  remove: (widgetId: string) => void;
}

function turnstileApi(): TurnstileApi | undefined {
  return (window as unknown as { turnstile?: TurnstileApi }).turnstile;
}

/** True when the widget should be rendered. Exported so the caller can require a token. */
export const turnstileEnabled = Boolean(SITE_KEY);

export function TurnstileWidget({
  onToken,
  resetKey = 0,
}: {
  onToken: (token: string) => void;
  /** Bump this to discard a spent token and demand a new challenge. */
  resetKey?: number;
}) {
  const container = useRef<HTMLDivElement>(null);
  const widgetId = useRef<string | null>(null);
  const appliedReset = useRef(resetKey);

  // Keep the latest callback in a ref so the render effect never re-runs (and never re-renders
  // the widget, which would invalidate the visitor's solution).
  const callback = useRef(onToken);
  useEffect(() => {
    callback.current = onToken;
  }, [onToken]);

  useEffect(() => {
    if (!SITE_KEY) return;

    const mount = () => {
      const api = turnstileApi();
      if (!api || !container.current || widgetId.current) return;
      widgetId.current = api.render(container.current, {
        sitekey: SITE_KEY,
        callback: (token: string) => callback.current(token),
        "expired-callback": () => callback.current(""),
        "error-callback": () => callback.current(""),
      });
    };

    if (turnstileApi()) {
      mount();
      return;
    }

    let script = document.getElementById(SCRIPT_ID) as HTMLScriptElement | null;
    if (!script) {
      script = document.createElement("script");
      script.id = SCRIPT_ID;
      script.src = SCRIPT_SRC;
      script.async = true;
      script.defer = true;
      document.head.appendChild(script);
    }
    script.addEventListener("load", mount);
    return () => script?.removeEventListener("load", mount);
  }, []);

  useEffect(() => {
    if (appliedReset.current === resetKey) return;
    appliedReset.current = resetKey;
    const api = turnstileApi();
    if (api && widgetId.current) {
      api.reset(widgetId.current);
      callback.current("");
    }
  }, [resetKey]);

  if (!SITE_KEY) return null;
  return <div ref={container} className="cf-turnstile" />;
}
