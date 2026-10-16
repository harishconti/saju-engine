"use client";

import { useEffect } from "react";
import Link from "next/link";
import { Button, buttonClasses } from "@/components/ui";
import { ElementalRule, SealMark } from "@/components/viz";

/**
 * Error boundary. Shows something honest and gives the user a way out.
 * In development the digest is shown; in production only the reference is, and never a stack.
 */
export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Never log the message — it can contain user data. The digest is the support handle.
    console.error("app error", error.digest ?? error.name);
  }, [error]);

  return (
    <main className="grid-noise grid min-h-screen place-items-center px-4">
      <div className="flex max-w-md flex-col items-center gap-5 text-center">
        <SealMark char="止" />
        <p className="eyebrow">Something went wrong</p>
        <h1 className="h2">We hit a problem on our side</h1>
        <p className="text-sm text-muted-foreground">
          Nothing you did caused this, and nothing has been lost. Try again — if it keeps happening, email us
          with the reference below.
        </p>
        {error.digest ? (
          <p className="font-mono text-xs text-muted-foreground">reference: {error.digest}</p>
        ) : null}
        <ElementalRule className="max-w-24" />
        <div className="flex flex-wrap justify-center gap-3">
          <Button onClick={reset}>Try again</Button>
          <Link href="/dashboard" className={buttonClasses("outline", "md")}>
            Your dashboard
          </Link>
        </div>
      </div>
    </main>
  );
}
