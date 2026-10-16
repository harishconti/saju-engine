"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";
import { FileText, LayoutDashboard, LogOut, Receipt, Settings, ShieldCheck, Sparkles, Users } from "lucide-react";
import { cn } from "@/lib/utils";
import { authClient } from "@/lib/auth/client";

type NavItem = {
  href: string;
  label: string;
  icon: React.ComponentType<{ size?: number | string; "aria-hidden"?: boolean }>;
  exact?: boolean;
};

const NAV: NavItem[] = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard, exact: true },
  { href: "/dashboard/reports", label: "Reports", icon: FileText },
  { href: "/dashboard/profiles", label: "People", icon: Users },
  { href: "/dashboard/orders", label: "Purchases", icon: Receipt },
  { href: "/dashboard/account", label: "Account", icon: Settings },
];

const ADMIN_NAV: NavItem[] = [{ href: "/admin", label: "Review queue", icon: ShieldCheck }];

export function DashboardNav({ isAdmin }: { isAdmin: boolean }) {
  const pathname = usePathname();
  const items = isAdmin ? [...NAV, ...ADMIN_NAV] : NAV;

  return (
    <nav aria-label="Dashboard" className="flex gap-1 overflow-x-auto lg:flex-col lg:gap-0.5 lg:overflow-visible">
      {items.map((item) => {
        const active = item.exact ? pathname === item.href : pathname.startsWith(item.href);
        const Icon = item.icon;
        const isAdminItem = item.href.startsWith("/admin");
        return (
          <Link
            key={item.href}
            href={item.href}
            aria-current={active ? "page" : undefined}
            className={cn(
              "flex shrink-0 items-center gap-2.5 rounded-md px-3 py-2.5 text-sm transition-colors",
              "min-h-11",
              active
                ? "bg-muted font-medium text-foreground"
                : "text-muted-foreground hover:bg-muted/50 hover:text-foreground",
              isAdminItem && "lg:mt-2 lg:border-t lg:border-border lg:pt-3",
            )}
          >
            <Icon size={16} aria-hidden />
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}

export function SignOutButton() {
  const router = useRouter();
  const [busy, setBusy] = useState(false);

  return (
    <button
      type="button"
      disabled={busy}
      onClick={async () => {
        setBusy(true);
        try {
          await authClient.signOut();
        } catch {
          /* sign out locally regardless */
        }
        router.push("/login");
        router.refresh();
      }}
      className="inline-flex min-h-11 items-center gap-2 rounded-md px-3 py-2.5 text-sm text-muted-foreground transition-colors hover:bg-muted/50 hover:text-foreground disabled:opacity-50"
    >
      <LogOut size={16} aria-hidden />
      {busy ? "Signing out…" : "Sign out"}
    </button>
  );
}

export function NewOrderButton() {
  return (
    <Link
      href="/reports/new"
      className="inline-flex min-h-11 items-center gap-2 rounded-md bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground transition-[filter] hover:brightness-110"
    >
      <Sparkles size={16} aria-hidden />
      Order a reading
    </Link>
  );
}
