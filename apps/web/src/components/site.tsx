import Link from "next/link";
import { buttonClasses } from "@/components/ui";
import { ElementalRule, SealMark } from "@/components/viz";
import { CONTACT_EMAIL, CONTACT_HREF } from "@/lib/contact";

/** Static marketing chrome. Deliberately does NOT read the session — the landing page stays cheap
 *  and keeps working before the database is migrated. Signed-in chrome lives in the dashboard. */

const NAV = [
  { href: "/#why", label: "Why Saju" },
  { href: "/#demo", label: "See a report" },
  { href: "/#pricing", label: "Pricing" },
  { href: "/#how", label: "How it's built" },
  { href: "/#faq", label: "FAQ" },
];

/**
 * Site header.
 *
 * `user` is passed in by the page rather than fetched here, so the shell stays a plain component and
 * the page controls its own caching. It is `null` for signed-out visitors — the common case, and the
 * one the prerendered HTML should match.
 *
 * This used to hardcode "Sign in" with no way to know otherwise, and the landing page was statically
 * prerendered, so a signed-in visitor was still invited to sign in — the page could not tell. Where
 * the header is rendered, the callers now read the session and pass it down.
 */
export function SiteHeader({
  user = null,
  cta = true,
}: {
  user?: { name?: string | null } | null;
  cta?: boolean;
}) {
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/85 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
        <Link href="/" className="flex items-center gap-3" aria-label="Cosmic Saju home">
          <SealMark char="四" />
          <span className="font-display text-xl leading-none">
            Cosmic Saju
            <span className="ml-2 hidden align-middle font-mono text-[10px] uppercase tracking-[0.2em] text-muted-foreground sm:inline">
              사주
            </span>
          </span>
        </Link>

        <nav className="hidden items-center gap-6 text-sm text-muted-foreground lg:flex" aria-label="Sections">
          {NAV.map((item) => (
            <a key={item.href} href={item.href} className="transition-colors hover:text-foreground">
              {item.label}
            </a>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          {user ? (
            <Link href="/dashboard" className={buttonClasses("primary", "sm")}>
              Dashboard
            </Link>
          ) : (
            <Link href="/login" className={buttonClasses("ghost", "sm")}>
              Sign in
            </Link>
          )}
          {cta ? (
            <Link href="/sample" className={buttonClasses(user ? "outline" : "primary", "sm")}>
              Free chart snapshot
            </Link>
          ) : null}
        </div>
      </div>
      <ElementalRule className="opacity-60" />
    </header>
  );
}

export function SiteFooter() {
  const year = new Date().getFullYear();
  return (
    <footer className="border-t border-border bg-surface">
      <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
        <div className="flex flex-col gap-8 md:flex-row md:justify-between">
          <div className="max-w-sm space-y-3">
            <div className="flex items-center gap-3">
              <SealMark char="四" />
              <span className="font-display text-lg">Cosmic Saju</span>
            </div>
            <p className="text-sm text-muted-foreground">
              An accurate engine and an honest interpreter — not a Korean master.
            </p>
            <p className="font-mono text-xs text-muted-foreground">사주 · 四柱 · Four Pillars of Destiny</p>
          </div>

          <div className="grid grid-cols-2 gap-8 text-sm sm:grid-cols-3">
            <div className="space-y-2">
              <p className="eyebrow">Product</p>
              <ul className="space-y-1.5 text-muted-foreground">
                <li>
                  <Link href="/sample" className="hover:text-foreground">
                    Free snapshot
                  </Link>
                </li>
                <li>
                  <Link href="/#pricing" className="hover:text-foreground">
                    Pricing
                  </Link>
                </li>
                <li>
                  <Link href="/dashboard" className="hover:text-foreground">
                    Your reports
                  </Link>
                </li>
              </ul>
            </div>
            <div className="space-y-2">
              <p className="eyebrow">Legal</p>
              <ul className="space-y-1.5 text-muted-foreground">
                <li>
                  <Link href="/privacy" className="hover:text-foreground">
                    Privacy
                  </Link>
                </li>
                <li>
                  <Link href="/terms" className="hover:text-foreground">
                    Terms
                  </Link>
                </li>
                <li>
                  <Link href="/refund-policy" className="hover:text-foreground">
                    Refunds
                  </Link>
                </li>
              </ul>
            </div>
            <div className="space-y-2">
              <p className="eyebrow">Contact</p>
              <ul className="space-y-1.5 text-muted-foreground">
                <li>
                  <a
                    href={CONTACT_HREF}
                    className="hover:text-foreground"
                  >
                    {CONTACT_EMAIL}
                  </a>
                </li>
              </ul>
            </div>
          </div>
        </div>

        <div className="mt-8 space-y-3 border-t border-border pt-6">
          <ElementalRule className="max-w-40" />
          <p className="max-w-3xl text-xs leading-relaxed text-muted-foreground">
            Readings describe tendencies and timing, not fixed outcomes, and are intended for reflection
            rather than as professional medical, legal, or financial advice. Saju is a traditional Korean
            interpretive system; disagreements between schools on edge cases are disclosed in the reading
            rather than silently resolved.
          </p>
          <p className="text-xs text-muted-foreground">© {year} Cosmic Saju. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
}

export function MobileStickyCta() {
  return (
    <div className="fixed inset-x-0 bottom-0 z-40 border-t border-border bg-background/95 p-3 backdrop-blur lg:hidden">
      <Link href="/sample" className={buttonClasses("primary", "md", "w-full")}>
        Get your free chart snapshot
      </Link>
    </div>
  );
}
