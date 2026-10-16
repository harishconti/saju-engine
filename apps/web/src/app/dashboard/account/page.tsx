import Link from "next/link";
import { Alert, Card, CardContent, KeyValue, PageHeader } from "@/components/ui";
import { AccountNameForm, ConsentForm, DeletionPanel } from "@/components/dashboard/account-actions";
import { requireUser } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { formatDate } from "@/lib/format";
import { PRIVACY_EMAIL, PRIVACY_HREF } from "@/lib/contact";

export const dynamic = "force-dynamic";
export const metadata = { title: "Account" };

const POLICY_VERSION = "2026-10-15";
const DELETION_GRACE_DAYS = 30;

export default async function AccountPage() {
  const user = await requireUser();

  const [latestConsent, deletion, counts] = await Promise.all([
    prisma.consentRecord.findFirst({
      where: { userId: user.id },
      orderBy: { grantedAt: "desc" },
    }),
    prisma.deletionRequest.findFirst({
      where: { userId: user.id },
      orderBy: { requestedAt: "desc" },
    }),
    prisma.user.findUnique({
      where: { id: user.id },
      select: {
        createdAt: true,
        _count: { select: { profiles: true, reports: true, orders: true } },
      },
    }),
  ]);

  const purposes = (latestConsent?.purposes ?? { service: true, service_messages: false }) as {
    service: boolean;
    service_messages: boolean;
  };

  const deletionActive = deletion?.status === "pending" ? deletion : null;

  return (
    <>
      <PageHeader
        eyebrow="Account"
        title="Your account and your data"
        description="What we hold, what you consented to, and how to make us delete it."
      />

      <Card>
        <CardContent className="py-5">
          <h2 className="pb-3 font-display text-xl">You</h2>
          <AccountNameForm initialName={user.name} />
          <dl className="mt-6">
            <KeyValue label="Email" value={user.email} />
            <KeyValue label="Member since" value={formatDate(counts?.createdAt ?? null)} />
            <KeyValue
              label="Stored"
              value={`${counts?._count.profiles ?? 0} people · ${counts?._count.reports ?? 0} readings · ${
                counts?._count.orders ?? 0
              } orders`}
            />
            <KeyValue label="Role" value={user.role} />
          </dl>
          <p className="pt-3 text-xs text-muted-foreground">
            Your email is the sign-in identity and is managed by our authentication provider. To change it,
            contact us.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="py-5">
          <h2 className="pb-1 font-display text-xl">Consent</h2>
          <p className="pb-4 text-sm text-muted-foreground">
            Consent is recorded with the policy version and the date. Withdrawing the first item stops
            processing and begins the deletion path. The history is append-only — we never rewrite it.
          </p>
          <ConsentForm initial={purposes} policyVersion={latestConsent?.policyVersion ?? POLICY_VERSION} />
          <p className="pt-4 text-xs text-muted-foreground">
            Latest record: {latestConsent ? formatDate(latestConsent.grantedAt) : "none"} · policy version{" "}
            {latestConsent?.policyVersion ?? POLICY_VERSION}
            {latestConsent?.withdrawnAt ? ` · withdrawn ${formatDate(latestConsent.withdrawnAt)}` : ""}.{" "}
            See the{" "}
            <Link href="/privacy" className="underline hover:text-foreground">
              privacy policy
            </Link>
            .
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="py-5">
          <h2 className="pb-3 font-display text-xl">Your data</h2>
          <p className="pb-3 text-sm text-muted-foreground">
            You can ask for a copy of everything we hold, or ask us to correct something. Email{" "}
            <a
              href={PRIVACY_HREF}
              className="underline hover:text-foreground"
            >
              {PRIVACY_EMAIL}
            </a>{" "}
            and we&apos;ll respond within 30 days.
          </p>
          <p className="text-xs text-muted-foreground">
            Individual readings can be deleted from the{" "}
            <Link href="/dashboard/reports" className="underline hover:text-foreground">
              reports page
            </Link>
            .
          </p>
        </CardContent>
      </Card>

      <Card className="border-destructive/30">
        <CardContent className="py-5">
          <h2 className="pb-3 font-display text-xl">Delete account</h2>
          {deletionActive ? (
            <Alert tone="warning" title="A deletion request is already scheduled">
              Scheduled for {formatDate(deletionActive.scheduledFor)}.
            </Alert>
          ) : null}
          <DeletionPanel
            scheduledFor={deletionActive ? formatDate(deletionActive.scheduledFor) : null}
            status={deletion?.status ?? null}
          />
          <p className="pt-4 text-xs text-muted-foreground">
            Grace period: {DELETION_GRACE_DAYS} days. Cancellable any time before it completes.
          </p>
        </CardContent>
      </Card>
    </>
  );
}
