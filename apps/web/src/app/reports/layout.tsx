import { DashboardShell } from "@/components/dashboard/shell-frame";
import { getCurrentUser } from "@/lib/auth";
import { isAdminEmail } from "@/lib/roles";
import { redirect } from "next/navigation";

/**
 * The ordering flow runs inside the authenticated shell.
 *
 * `/reports/new` is a top-level route and there was **no `reports/layout.tsx`**, so it rendered into the
 * bare `<body>`: no navigation, no sign-out, and no padding wrapper — which is what made the page look
 * broken no matter how sound its contents were. Same single cause as `/admin`.
 *
 * `src/proxy.ts` already matches `/reports/:path*`; this re-checks server-side as well and is what
 * supplies the user to the shell.
 */
export const dynamic = "force-dynamic";

export default async function ReportsLayout({ children }: { children: React.ReactNode }) {
  const user = await getCurrentUser();
  if (!user) redirect("/login?next=/reports/new");

  return (
    <DashboardShell user={user} isAdmin={user.role === "ADMIN" && isAdminEmail(user.email)}>
      {children}
    </DashboardShell>
  );
}
