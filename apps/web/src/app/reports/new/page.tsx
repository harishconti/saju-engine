import { PageHeader, buttonClasses } from "@/components/ui";
import { OrderFlow } from "@/components/dashboard/order-flow";
import { requireUser } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { parseChartSummary } from "@/lib/chart";

export const dynamic = "force-dynamic";
export const metadata = { title: "Order a reading" };

export default async function NewOrderPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const user = await requireUser();
  const params = await searchParams;
  const requested = typeof params.tier === "string" ? params.tier : null;

  const profiles = await prisma.profile.findMany({
    where: { userId: user.id, deletedAt: null },
    orderBy: [{ isDefault: "desc" }, { createdAt: "asc" }],
    select: { id: true, label: true, fullName: true, gender: true, chartJson: true },
  });

  const orderProfiles = profiles.map((p) => ({
    id: p.id,
    label: p.label,
    fullName: p.fullName,
    gender: p.gender,
    hasChart: parseChartSummary(p.chartJson) !== null,
  }));

  return (
    <>
      <PageHeader
        eyebrow="New order"
        title="Order a reading"
        description="Pick a reading, choose who it's for, and we'll take it from there. Your chart is derived from the birth details you've already saved."
        actions={
          <a
            href="/demo/demo-rm-deep.html"
            target="_blank"
            rel="noreferrer"
            className={buttonClasses("outline", "sm")}
          >
            See a sample report
          </a>
        }
      />

      <OrderFlow profiles={orderProfiles} initialTier={requested} />
    </>
  );
}
