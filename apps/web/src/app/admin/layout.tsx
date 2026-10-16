import { DashboardShell } from "@/components/dashboard/shell-frame";
import { getCurrentUser } from "@/lib/auth";
import { isAdminEmail } from "@/lib/roles";
import { redirect } from "next/navigation";

/**
 * The review console's shell.
 *
 * `/admin` had no layout at all, so its pages rendered straight into `<body>` — no navigation, no
 * sign-out, no way back to the dashboard, and no padding. Sharing `DashboardShell` with `/dashboard`
 * fixes all four at once and keeps them in step.
 *
 * The gate here is a redirect rather than `requireAdmin()`, which **throws** — a signed-in non-admin
 * should land back on their own dashboard, not on an error page. `requireAdmin()` still guards the page
 * body as well, and `src/proxy.ts` matches `/admin/:path*` before either runs.
 */
export const dynamic = "force-dynamic";
export const metadata = { title: "Review queue" };

export default async function AdminLayout({ children }: { children: React.ReactNode }) {
  const user = await getCurrentUser();
  if (!user) redirect("/login?next=/admin");

  const isAdmin = user.role === "ADMIN" && isAdminEmail(user.email);
  if (!isAdmin) redirect("/dashboard");

  return (
    <DashboardShell user={user} isAdmin wide>
      {children}
    </DashboardShell>
  );
}
