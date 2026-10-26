import { Suspense } from "react";
import { Card, CardContent } from "@/components/ui";
import { ResetPasswordForm } from "@/components/reset-password-form";

/**
 * Password reset, confirm step (AU-41, D6).
 *
 * Public by design: the emailed token is the authorisation, and there is no session. Not added to the
 * middleware matcher in `src/proxy.ts`.
 *
 * The page must never be cached: the URL carries a one-time credential on arrival, and a cached HTML
 * response (or a shared CDN copy) would be the wrong thing to serve to the next visitor. The form
 * scrubs the token from the address bar as soon as it mounts; `referrer: "no-referrer"` keeps the
 * URL out of any outbound Referer header.
 */

export const dynamic = "force-dynamic";
export const fetchCache = "force-no-store";
export const metadata = { title: "Choose a new password", referrer: "no-referrer" };

export default function ResetPasswordPage() {
  return (
    <main className="grid-noise min-h-screen">
      <div className="mx-auto flex min-h-screen max-w-md flex-col justify-center gap-6 px-4 py-12">
        <div className="text-center">
          <h1 className="h2">Choose a new password</h1>
        </div>
        <Card>
          <CardContent className="py-6">
            {/* `useSearchParams` needs a Suspense boundary so a static shell never embeds it. */}
            <Suspense fallback={<p className="text-sm text-muted-foreground">Loading…</p>}>
              <ResetPasswordForm />
            </Suspense>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
