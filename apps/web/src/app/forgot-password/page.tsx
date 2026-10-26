import { Card, CardContent } from "@/components/ui";
import { ForgotPasswordForm } from "@/components/forgot-password-form";

/**
 * Password reset, request step (AU-41, D6).
 *
 * Public by design: a person who cannot sign in has no session, so this page must not be added to
 * the middleware matcher in `src/proxy.ts` (which lists protected routes only).
 */

export const metadata = { title: "Reset your password" };

export default function ForgotPasswordPage() {
  return (
    <main className="grid-noise min-h-screen">
      <div className="mx-auto flex min-h-screen max-w-md flex-col justify-center gap-6 px-4 py-12">
        <div className="text-center">
          <h1 className="h2">Reset your password</h1>
        </div>
        <Card>
          <CardContent className="py-6">
            <ForgotPasswordForm />
          </CardContent>
        </Card>
        <p className="text-center text-xs text-muted-foreground">
          We never say whether an address has an account here — the answer is the same either way.
        </p>
      </div>
    </main>
  );
}
