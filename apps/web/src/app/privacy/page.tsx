import { LegalLayout } from "@/components/legal";
import { PRIVACY_EMAIL, PRIVACY_HREF } from "@/lib/contact";

export const metadata = { title: "Privacy policy" };

// The shared legal shell reads the session so the header can offer "Dashboard" instead of
// "Sign in". Declared explicitly: without this, Next attempts to prerender the page, discovers
// `cookies()` and recovers by rendering dynamically anyway — correct, but it logs a
// "Dynamic server usage" error on every build, which reads like a failure.
export const dynamic = "force-dynamic";
export default function PrivacyPage() {
  return (
    <LegalLayout
      title="Privacy policy"
      intro="This policy explains what we collect, why we need it, how long we keep it, and how to make us delete it. It is written to be read, not to be survived."
    >
      <h2>The short version</h2>
      <p>
        We collect your name, email, birth date, birth time, and birth place — and we need all three birth
        details to compute your chart. We store your reports so you can download them again. We don't sell
        your data, we don't share it for advertising, and you can delete reports or your entire account
        yourself from your dashboard.
      </p>

      <h2>What we collect and why</h2>
      <ul>
        <li>
          <strong>Account:</strong> name and email address. Needed to sign you in and deliver your report.
          Lawful basis: performance of a contract.
        </li>
        <li>
          <strong>Birth details:</strong> date, time, place, and coordinates. Needed to compute the four
          pillars, apply solar-time correction, and determine major-luck direction. This is sensitive
          personal data and we rely on your explicit consent, which you give when you create an account and
          when you save a profile.
        </li>
        <li>
          <strong>Your reports:</strong> the PDF we produce plus the underlying markdown, kept so you can
          re-download and so we can answer &ldquo;what did we actually send you?&rdquo;.
        </li>
        <li>
          <strong>The email you give for a free snapshot:</strong> if you ask us to email your snapshot, we
          keep the address so we can send it and so we can send the course you opted into. We keep no birth
          details for an anonymous snapshot — only the address and your marketing choice. Replying to any
          email we send unsubscribes you.
        </li>
        <li>
          <strong>Payment records:</strong> our payment provider, Dodo Payments, is the merchant of record.
          They hold your card details — we never see or store them. We keep only an order reference,
          amount, currency, and date.
        </li>
        <li>
          <strong>Operational records:</strong> security and audit logs (who did what, when, from which IP),
          consent records, and delivery records.
        </li>
      </ul>

      <h2>What we never hold</h2>
      <p>
        Card numbers, CVVs, passwords, OAuth tokens, and session tokens. Passwords and sessions are managed
        by our authentication provider; card data is managed by Dodo Payments.
      </p>

      <h2>Who processes data for us</h2>
      <ul>
        <li>
          <strong>Neon</strong> — Postgres database and authentication, hosting your account and birth data.
        </li>
        <li>
          <strong>Cloudflare</strong> — R2 object storage, holding your report PDFs in a private bucket.
        </li>
        <li>
          <strong>Vercel</strong> — application hosting, and Web Analytics: aggregate page-view counts
          with no cookies, no cross-site tracking and no personal identifiers.
        </li>
        <li>
          <strong>Resend</strong> — transactional email, to tell you your report is ready.
        </li>
        <li>
          <strong>Dodo Payments</strong> — payments and tax. They are the merchant of record for your
          purchase.
        </li>
        <li>
          <strong>Hostinger</strong> — the mailbox that receives email sent to us and to{" "}
          {PRIVACY_EMAIL}. It holds correspondence
          only; nothing from your account is stored there.
        </li>
        <li>
          <strong>Google</strong> — only if you choose &ldquo;Continue with Google&rdquo;, for sign-in.
        </li>
      </ul>

      <h2>How long we keep it</h2>
      <ul>
        <li>Birth details and reports: until you delete them, or after 24 months of inactivity.</li>
        <li>Anonymous free snapshots that were never saved to an account: 7 days.</li>
        <li>Delivery records: 24 months. Audit logs: 24 months.</li>
        <li>
          Consent records: while your account exists, and 24 months afterwards — we need to be able to show
          that consent was given and withdrawn.
        </li>
        <li>
          Order records (amount, date, reference — no birth data): kept as long as tax and accounting rules
          require. In practice these live with Dodo Payments as merchant of record.
        </li>
      </ul>

      <h2>Deleting your data</h2>
      <p>
        From your dashboard you can delete individual reports, or your whole account. Account deletion has a
        30-day grace period and can be cancelled during it. When it completes we anonymise your account,
        delete your birth details and reports, and delete the report PDFs from storage.
      </p>
      <p>
        <strong>What survives, honestly:</strong> order records are retained in anonymised form (amount,
        date, provider reference) because we have to be able to account for the money, and consent records
        are retained to show that consent was given and later withdrawn. Neither contains your birth
        details, name, or email.
      </p>

      <h2>Your other rights</h2>
      <p>
        You can ask for a copy of everything we hold about you, ask us to correct it, or object to a
        particular use. Email{" "}
        <a href={PRIVACY_HREF} className="underline">
          {PRIVACY_EMAIL}
        </a>{" "}
        and we will respond within 30 days.
      </p>

      <h2>Security</h2>
      <p>
        Everything is served over TLS. Data is encrypted at rest by our database and storage providers.
        Report files live in a private store and are only reachable through short-lived signed links issued
        after we check that the report is yours.
      </p>

      <h2>Children</h2>
      <p>
        This service is not intended for anyone under 18, and we do not knowingly collect data from
        children.
      </p>

      <h2>Changes</h2>
      <p>
        If this policy changes materially we will tell you by email before the change takes effect.
      </p>
    </LegalLayout>
  );
}
