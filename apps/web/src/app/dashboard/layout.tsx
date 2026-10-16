import { redirect } from "next/navigation";
import Link from "next/link";
import { getCurrentUser } from "@/lib/auth";
import { isAdminEmail } from "@/lib/roles";
import { DashboardNav, SignOutButton } from "@/components/dashboard/shell";
import { ElementalRule, SealMark } from "@/components/viz";

/**
 * The authenticated shell.
 *
 * `src/proxy.ts` already gates /dashboard/*, but this re-checks server-side: defence in depth, and it
 * is what actually supplies the user to the tree. Never trust the middleware alone.
 */
export const dynamic = "force-dynamic";

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const user = await getCurrentUser();
  if (!user) redirect("/login?next=/dashboard");

  const isAdmin = user.role === "ADMIN" && isAdminEmail(user.email);

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
          <p className="truncate px-3 pb-1 text-xs text-muted-foreground" title={user.email}>
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
          <div className="mx-auto max-w-5xl space-y-6">{children}</div>
        </main>

        <footer className="border-t border-border px-4 py-4 text-xs text-muted-foreground sm:px-6 lg:px-8">
          <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-3">
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
