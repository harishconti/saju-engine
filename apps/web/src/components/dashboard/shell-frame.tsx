import Link from "next/link";
import { ElementalRule, SealMark } from "@/components/viz";
import { DashboardNav, SignOutButton } from "@/components/dashboard/shell";

/**
 * The authenticated shell: sidebar on desktop, sticky nav on mobile, footer — and, the part that
 * actually mattered, the `px-4 py-6 sm:px-6 lg:px-8 lg:py-8` padding wrapper.
 *
 * Extracted from `dashboard/layout.tsx` so `/admin` can have it too. `/admin` previously had **no
 * layout at all**, so its pages rendered straight into `<body>`: no navigation, no sign-out, no route
 * back to the dashboard, and content flush against the viewport edges because nothing supplied the
 * padding. Reported by the owner as "no back button and all padding are not good" — it was one cause.
 *
 * `wide` gives the review queue a little more room than the customer-facing pages.
 */
export function DashboardShell({
  user,
  isAdmin,
  wide = false,
  children,
}: {
  user: { email: string | null };
  isAdmin: boolean;
  wide?: boolean;
  children: React.ReactNode;
}) {
  const width = wide ? "max-w-6xl" : "max-w-5xl";

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[248px_1fr]">
      {/* Sidebar (desktop) */}
      <aside className="hidden border-r border-border bg-surface lg:flex lg:flex-col">
        <div className="flex h-16 items-center gap-3 border-b border-border px-4">
          <Link href="/" className="flex items-center gap-3" aria-label="Cosmic Saju home">
            <SealMark char="四" />
            <span className="font-display text-lg leading-none">Cosmic Saju</span>
          </Link>
        </div>
        <div className="flex-1 overflow-y-auto p-3">
          <DashboardNav isAdmin={isAdmin} />
        </div>
        <div className="border-t border-border p-3">
          <p className="truncate px-3 pb-1 text-xs text-muted-foreground" title={user.email ?? undefined}>
            {user.email}
          </p>
          <SignOutButton />
        </div>
      </aside>

      {/* Main */}
      <div className="flex min-h-screen flex-col">
        {/* Mobile header */}
        <header className="sticky top-0 z-30 border-b border-border bg-background/90 backdrop-blur lg:hidden">
          <div className="flex h-14 items-center justify-between gap-3 px-4">
            <Link href="/" className="flex items-center gap-2" aria-label="Cosmic Saju home">
              <SealMark char="四" />
              <span className="font-display text-base">Cosmic Saju</span>
            </Link>
            <SignOutButton />
          </div>
          <div className="border-t border-border px-2 py-1.5">
            <DashboardNav isAdmin={isAdmin} />
          </div>
          <ElementalRule className="opacity-50" />
        </header>

        <main className="flex-1 px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
          <div className={`mx-auto ${width} space-y-6`}>{children}</div>
        </main>

        <footer className="border-t border-border px-4 py-4 text-xs text-muted-foreground sm:px-6 lg:px-8">
          <div className={`mx-auto ${width} flex flex-wrap items-center justify-between gap-3`}>
            <span>
              Readings describe tendencies and timing, not fixed outcomes. Not medical, legal, or financial
              advice.
            </span>
            <span className="flex items-center gap-3">
              <Link href="/privacy" className="hover:text-foreground">
                Privacy
              </Link>
              <Link href="/terms" className="hover:text-foreground">
                Terms
              </Link>
            </span>
          </div>
        </footer>
      </div>
    </div>
  );
}
