import Link from "next/link";
import { Alert, Card, CardContent, KeyValue, PageHeader } from "@/components/ui";
import { AccountNameForm, ConsentForm, DeletionPanel } from "@/components/dashboard/account-actions";
import { SessionsPanel } from "@/components/dashboard/account-sessions";
import { listAccountSessions, requireUser } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { formatDate } from "@/lib/format";
import { PRIVACY_EMAIL, PRIVACY_HREF } from "@/lib/contact";
import { POLICY_VERSION } from "@/lib/consent";

export const dynamic = "force-dynamic";
export const metadata = { title: "Account" };

const DELETION_GRACE_DAYS = 30;

export default async function AccountPage() {
  const user = await requireUser();

  const [latestConsent, deletion, counts, sessions] = await Promise.all([
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
    // AU-40 (D6). Null means the provider could not be asked, not "no other devices" — the card
    // says so rather than showing an empty list that would read as a promise.
    listAccountSessions(),
  ]);

  // Default to NOT granted. This previously said `service: true`, so an account with no
  // `ConsentRecord` at all rendered the required consent as already ticked — the UI asserting a
  // state the database did not have, in exactly the place the privacy policy makes claims. The
  // checkbox below is what records it; it must start unticked and be an explicit action.
  //
  // AU-23: a record written against an older policy text is not consent to the current one — the
  // same rule the server enforces — so it renders as ungranted here too, rather than showing a
  // ticked box for consent the server will refuse to honour.
  const purposes = (
    latestConsent && !latestConsent.withdrawnAt && latestConsent.policyVersion === POLICY_VERSION
      ? latestConsent.purposes
      : { service: false, service_messages: false }
  ) as { service: boolean; service_messages: boolean };

  const policyChanged = latestConsent != null && latestConsent.policyVersion !== POLICY_VERSION;

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
          <h2 className="pb-1 font-display text-xl">Where you&apos;re signed in</h2>
          {sessions ? (
            <SessionsPanel sessions={sessions} />
          ) : (
            <Alert tone="warning" title="We couldn't load your active sessions">
              Refresh the page, or sign out and back in, then try again. The list is unavailable
              until the sign-in provider answers.
            </Alert>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardContent className="py-5">
          <h2 className="pb-1 font-display text-xl">Consent</h2>
          <p className="pb-4 text-sm text-muted-foreground">
            Consent is recorded with the policy version and the date. Turning off the first item
            stops new orders and new readings; readings you have already paid for are still produced
            and delivered. The history is append-only — we never rewrite it.
          </p>
          <ConsentForm initial={purposes} policyVersion={POLICY_VERSION} />
          {policyChanged ? (
            <Alert tone="warning" title="The privacy policy has been updated">
              Your previous consent was recorded against an earlier version, so it is shown as not
              granted. Please review the{" "}
              <Link href="/privacy" className="underline hover:text-foreground">
                current policy
              </Link>{" "}
              and confirm again.
            </Alert>
          ) : null}
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
