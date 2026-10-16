import { DashboardShell } from "@/components/dashboard/shell-frame";
import { getCurrentUser } from "@/lib/auth";
import { isAdminEmail } from "@/lib/roles";
import { redirect } from "next/navigation";

/**
 * The authenticated shell.
 *
 * `src/proxy.ts` already gates /dashboard/*, but this re-checks server-side: defence in depth, and it
 * is what actually supplies the user to the tree. Never trust the middleware alone.
 *
 * The markup lives in `DashboardShell` so `/admin` can share it — see that file for why.
 */
export const dynamic = "force-dynamic";

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const user = await getCurrentUser();
  if (!user) redirect("/login?next=/dashboard");

  const isAdmin = user.role === "ADMIN" && isAdminEmail(user.email);

  return (
    <DashboardShell user={user} isAdmin>
      {children}
    </DashboardShell>
  );
}
