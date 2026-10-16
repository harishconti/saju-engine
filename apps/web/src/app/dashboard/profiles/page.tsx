import Link from "next/link";
import { Alert, buttonClasses, Card, CardContent, PageHeader } from "@/components/ui";
import { ProfileActions } from "@/components/dashboard/profile-actions";
import { ProfileForm } from "@/components/dashboard/profile-form";
import { DayMasterBadge, ElementBalanceBars, FourPillarsChart } from "@/components/viz";
import { requireUser } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { elementCountsFrom, parseChartSummary } from "@/lib/chart";
import { describeBirth } from "@/lib/birth";

export const dynamic = "force-dynamic";
export const metadata = { title: "People" };

export default async function ProfilesPage() {
  const user = await requireUser();

  const profiles = await prisma.profile.findMany({
    where: { userId: user.id, deletedAt: null },
    orderBy: [{ isDefault: "desc" }, { createdAt: "asc" }],
  });

  return (
    <>
      <PageHeader
        eyebrow="People"
        title="Your charts"
        description="Birth details are stored once per person and reused for every reading. A compatibility (궁합) reading needs two people."
        actions={
          <Link href="/reports/new" className={buttonClasses("outline", "md")}>
            Order a reading
          </Link>
        }
      />

      <Alert tone="neutral" title="Why we ask for a birthplace">
        Solar-time correction depends on longitude, and the hour pillar depends on the local clock. We
        resolve the coordinates from a fixed place list when you save — never on the fly, and never from a
        guess — so the same details always produce the same chart.
      </Alert>

      {profiles.length === 0 ? (
        <Card>
          <CardContent className="py-6">
            <p className="text-sm text-muted-foreground">
              No one saved yet. Add your own details below — you&apos;ll see your four pillars immediately,
              before ordering anything.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {profiles.map((p) => {
            const chart = parseChartSummary(p.chartJson);
            const counts = elementCountsFrom(chart);
            return (
              <Card key={p.id}>
                <CardContent className="space-y-4 py-5">
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <h2 className="font-display text-xl">{p.label}</h2>
                        {p.isDefault ? (
                          <span className="rounded-full border border-primary/50 px-2 py-0.5 text-xs text-primary">
                            primary
                          </span>
                        ) : null}
                        {!p.timeKnown ? (
                          <span className="rounded-full border border-warning/50 px-2 py-0.5 text-xs text-warning">
                            birth time unknown
                          </span>
                        ) : null}
                      </div>
                      <p className="mt-1 text-sm text-muted-foreground">
                        {p.fullName} · {p.gender === "F" ? "Female" : "Male"} ·{" "}
                        {describeBirth({
                          birthDate: p.birthDate,
                          birthTime: p.birthTime,
                          city: p.city,
                          country: p.country,
                          timeKnown: p.timeKnown,
                        })}
                      </p>
                    </div>
                    <ProfileActions profileId={p.id} isDefault={p.isDefault} />
                  </div>

                  {chart ? (
                    <div className="grid gap-5 lg:grid-cols-[minmax(0,320px)_1fr]">
                      <FourPillarsChart pillars={chart.pillars} animate={false} />
                      <div className="space-y-4">
                        <DayMasterBadge
                          char={chart.dayMaster.char}
                          element={chart.dayMaster.element ?? null}
                          polarity={chart.dayMaster.polarity ?? null}
                        />
                        <ElementBalanceBars counts={counts} />
                        {chart.caveats?.length ? (
                          <Alert tone="warning" title="Confidence note">
                            <ul className="space-y-1">
                              {chart.caveats.map((c) => (
                                <li key={c}>{c}</li>
                              ))}
                            </ul>
                          </Alert>
                        ) : null}
                      </div>
                    </div>
                  ) : (
                    <p className="text-xs text-muted-foreground">
                      Chart not derived yet — this happens automatically once the report engine is reachable.
                    </p>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      <Card>
        <CardContent className="py-5">
          <h2 className="pb-1 font-display text-xl">Add someone</h2>
          <p className="pb-4 text-sm text-muted-foreground">
            Yourself, a partner, or a friend. Nothing is ordered until you choose a reading.
          </p>
          <ProfileForm onDone={undefined} />
        </CardContent>
      </Card>
    </>
  );
}
