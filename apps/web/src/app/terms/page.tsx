import { LegalLayout } from "@/components/legal";

export const metadata = { title: "Terms of service" };

export default function TermsPage() {
  return (
    <LegalLayout
      title="Terms of service"
      intro="The rules for using Cosmic Saju. Short, because the product is short: you buy a reading, we produce and deliver it."
    >
      <h2>What you are buying</h2>
      <p>
        A written reading of your Korean Saju (사주) chart, delivered as a PDF and stored in your account. It
        is an interpretive document produced by a calculation engine and reviewed by a person before
        delivery. It is not a professional assessment of your health, finances, or legal position, and it is
        not a prediction of specific events.
      </p>

      <h2>Your account</h2>
      <ul>
        <li>You need an account to buy and store readings.</li>
        <li>Keep your credentials to yourself; activity under your account is your responsibility.</li>
        <li>You must be 18 or over.</li>
        <li>Provide accurate birth details. A wrong birth time produces a wrong chart — see the accuracy section.</li>
      </ul>

      <h2>Birth details and accuracy</h2>
      <p>
        Saju depends entirely on the birth date, time, and place. Where your recorded time is uncertain, or
        sits close to a two-hour branch boundary or a solar-term boundary, the reading will say so and mark
        the affected pillar as lower-confidence. We surface those cases rather than silently guessing. If
        you gave us incorrect details, we will regenerate once at no charge if you tell us promptly.
      </p>

      <h2>Reviews and delivery</h2>
      <p>
        Every paid reading is reviewed by a person before it is sent. The free snapshot is generated
        immediately without review. Paid readings are usually delivered within a day; occasionally longer if
        we want to check something.
      </p>

      <h2>What we will not claim</h2>
      <ul>
        <li>We do not claim certainty about future events.</li>
        <li>We do not claim to be, or to be endorsed by, a Korean master or any lineage.</li>
        <li>We do not provide medical, legal, or financial advice.</li>
      </ul>
      <p>
        Readings are for reflection and self-understanding. Decisions you make after reading one are yours.
      </p>

      <h2>Payment</h2>
      <p>
        Payments are processed by Lemon Squeezy, who act as merchant of record. That means your purchase
        contract for payment and tax purposes is with them, and they handle sales tax and VAT. Prices are in
        US dollars.
      </p>

      <h2>Licence and use</h2>
      <p>
        Your reading is for your personal use. You may print it and share it privately. You may not resell
        it, publish it commercially, or present it as your own product. The engine, the knowledge base, and
        the report templates remain our intellectual property.
      </p>

      <h2>Availability and changes</h2>
      <p>
        We aim to keep the service available but do not guarantee uninterrupted access. We may change or
        withdraw features. If we discontinue the service, you will be able to download the readings you have
        paid for for at least 90 days.
      </p>

      <h2>Liability</h2>
      <p>
        To the extent permitted by law, our liability for any claim relating to a reading is limited to the
        amount you paid for it. Nothing in these terms limits liability that cannot lawfully be limited.
      </p>

      <h2>Governing terms</h2>
      <p>
        These terms are governed by the laws applicable at our place of business, without affecting any
        statutory consumer rights you have where you live.
      </p>
    </LegalLayout>
  );
}
