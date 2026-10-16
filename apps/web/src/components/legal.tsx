import Link from "next/link";
import { SiteFooter, SiteHeader } from "@/components/site";
import { CONTACT_EMAIL } from "@/lib/contact";

/** Shared shell for the legal pages. These pages are also read by Lemon Squeezy during store
 *  activation, so they must be reachable and substantive. */

export const LEGAL_CONTACT = CONTACT_EMAIL;
export const LEGAL_UPDATED = "15 October 2026";

export function LegalLayout({
  title,
  intro,
  children,
}: {
  title: string;
  intro?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <>
      <SiteHeader cta={false} />
      <main className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
        <p className="eyebrow">Legal</p>
        <h1 className="h2 mt-2">{title}</h1>
        <p className="mt-2 font-mono text-xs text-muted-foreground">Last updated {LEGAL_UPDATED}</p>
        {intro ? <p className="lede mt-6 text-base">{intro}</p> : null}
        <div className="mt-8 space-y-6 text-sm leading-relaxed text-muted-foreground [&_h2]:mt-8 [&_h2]:font-display [&_h2]:text-lg [&_h2]:text-foreground [&_li]:ml-4 [&_strong]:text-foreground [&_ul]:list-disc [&_ul]:space-y-1.5">
          {children}
        </div>
        <div className="mt-10 border-t border-border pt-6 text-sm">
          <p>
            Questions about any of this:{" "}
            <a href={`mailto:${LEGAL_CONTACT}`} className="underline hover:text-foreground">
              {LEGAL_CONTACT}
            </a>
          </p>
          <p className="mt-3">
            <Link href="/" className="text-primary hover:underline">
              ← Back to Cosmic Saju
            </Link>
          </p>
        </div>
      </main>
      <SiteFooter />
    </>
  );
}
