import { LegalLayout } from "@/components/legal";
import { CONTACT_EMAIL, CONTACT_HREF } from "@/lib/contact";

export const metadata = { title: "Refund policy" };

export default function RefundPolicyPage() {
  return (
    <LegalLayout
      title="Refund policy"
      intro="If the reading doesn't tell you anything true about you, ask for your money back. We would rather refund than argue."
    >
      <h2>The guarantee</h2>
      <p>
        If a paid reading misses the mark, email us within <strong>30 days</strong> of delivery and we will
        refund it in full. You do not have to prove anything or justify it beyond telling us it didn't land.
      </p>

      <h2>How to ask</h2>
      <p>
        Email{" "}
        <a href={CONTACT_HREF} className="underline">
          {CONTACT_EMAIL}
        </a>{" "}
        with the email address you bought with. If you can, tell us where it missed — it genuinely helps us
        improve the reports, but it is not a condition of the refund.
      </p>

      <h2>What we will refund without hesitation</h2>
      <ul>
        <li>The reading didn&apos;t resonate with you.</li>
        <li>We got your birth details wrong and the regenerated reading still isn&apos;t right.</li>
        <li>Something in the report was factually wrong about your chart.</li>
        <li>We couldn&apos;t deliver, or delivery took unreasonably long.</li>
        <li>You were charged twice.</li>
      </ul>

      <h2>What we may decline</h2>
      <ul>
        <li>Requests made more than 30 days after delivery.</li>
        <li>Readings that have already been refunded once.</li>
        <li>Evidence of abuse — repeated buy-and-refund cycles.</li>
      </ul>

      <h2>How refunds are processed</h2>
      <p>
        Payments are handled by Lemon Squeezy as merchant of record, so refunds are issued through them to
        your original payment method. It usually lands within 5–10 business days depending on your bank.
        Refunds are always issued in the currency you paid in; small exchange-rate differences are outside
        our control.
      </p>

      <h2>Free snapshots</h2>
      <p>
        The free chart snapshot costs nothing, so there is nothing to refund. If it isn&apos;t for you, you
        have lost only the two minutes it took to enter your details.
      </p>

      <h2>Your statutory rights</h2>
      <p>
        Nothing here reduces rights you have under the consumer law where you live, including any right to
        cancel a distance purchase. If you are in the EU or UK and want to cancel before we deliver your
        reading, contact us and we will cancel and refund in full.
      </p>
    </LegalLayout>
  );
}
