import Link from "next/link";
import { Alert, Badge, Button, buttonClasses, Card, CardContent, SectionHeading } from "@/components/ui";
import { MobileStickyCta, SiteFooter, SiteHeader } from "@/components/site";
import { getCurrentUser } from "@/lib/auth";
import { ElementBalanceBars, ElementBalanceWheel, ElementLegend, FourPillarsChart, KoreanWatermark, SealMark, type PillarCell } from "@/components/viz";
import { PAID_TIERS, COMPAT_TIERS, SINGLE_TIERS, getTierById, type Tier } from "@/lib/tiers";
import { promoBadgeLabel, promoEndsLabel, promoPriceCents, promoScopeLabel } from "@/lib/promo";
import { offerPriceCents, promoIsLive } from "@/lib/pricing";
import { formatUSD } from "@/lib/format";

export const metadata = {
  title: "Cosmic Saju — Korean Four Pillars readings",
  description:
    "Your Korean Saju chart, read properly. Start with a free snapshot, then buy a report that a human has actually checked. An accurate engine and an honest interpreter — not a Korean master.",
};

/**
 * The demo chart is a real engine output for a public figure (RM / Kim Nam-joon, 1994-09-12 13:28 KST,
 * Seoul) — the same data behind the demo PDFs in /public/demo. Numbers are the engine's, not invented.
 */
const DEMO_PILLARS: PillarCell[] = [
  { label: "Year", stem: "甲", branch: "戌" },
  { label: "Month", stem: "癸", branch: "酉" },
  { label: "Day", stem: "辛", branch: "丑" },
  { label: "Hour", stem: "乙", branch: "未" },
];

const DEMO_ELEMENTS = { Wood: 34.1, Fire: 3.7, Earth: 16.9, Metal: 28.7, Water: 16.6 };

const FAQ = [
  {
    q: "Are you a Korean master?",
    a: "No — and we'd rather say so up front. This is a calculation engine built on classical 명리 principles, plus a human who reviews your reading before it reaches you. We're not a lineage holder, we don't claim to be, and the reading never pretends otherwise.",
  },
  {
    q: "Is this the same as BaZi?",
    a: "They share the same foundations — stems, branches, five elements, ten gods. This reading follows the Korean 명리 tradition, including the Korean 야자시 convention for the 23:00–01:00 hour. Where the schools disagree on an edge case, the reading tells you instead of picking silently.",
  },
  {
    q: "How is this different from a $9 app?",
    a: "Automated tools stop at the chart. A chart is arithmetic — the interpretation is the hard part. Every paid reading here is drafted by the engine and then reviewed by a person who can override the engine's favourable-element judgement when the classical reasoning says otherwise.",
  },
  {
    q: "How long until I get my report?",
    a: "The free snapshot is instant. A paid reading is checked by a person before it's sent, which usually takes under a day. If nobody gets to it within 10 hours it is delivered anyway, so you are never left waiting on a review that has not happened.",
  },
  {
    q: "What if my birth time is unknown?",
    a: "Say so when you enter your details. The hour pillar becomes genuinely uncertain, and the reading will mark it as lower-confidence rather than quietly assuming a time. You'll still get a useful reading from the year, month, and day pillars.",
  },
  {
    q: "Do you offer a guarantee?",
    a: "If the reading doesn't tell you anything true about you, ask for a refund and you'll get one. We'd rather refund than argue. See the refund policy for the practical details.",
  },
  {
    q: "What do you store about me?",
    a: "Your name, email, birth details, and your reports. Nothing is sold, nothing is shared. You can delete your reports, or your whole account, from your dashboard at any time.",
  },
];

/** Reading the session below opts this route out of static prerendering. That is a deliberate trade:
 *  a signed-in visitor must not be invited to sign in, and the header cannot know otherwise from HTML
 *  that was baked at build time. Revisit only with a client-side upgrade that cannot fail silently. */
export const dynamic = "force-dynamic";

/**
 * One pricing card. Shared by the single-chart grid and the "For two people" row so the two
 * surfaces cannot drift — the same reason the demo grid was collapsed into one array
 * (docs/webapp/06-frontend-ux.md).
 */
function TierCard({
  tier,
  badge = "Most complete",
  promoOn = false,
}: {
  tier: Tier;
  badge?: string;
  promoOn?: boolean;
}) {
  const free = tier.priceCents === 0;
  // While the offer runs, the customer pays the promotional price — the same number the server
  // records on the order and the store charges (see `lib/pricing.ts`).
  const now = promoOn ? promoPriceCents(tier.priceCents) : tier.priceCents;
  return (
    <Card className={tier.highlight ? "border-primary/50 relative" : undefined}>
      {tier.highlight ? (
        <span className="absolute -top-2.5 left-5">
          <Badge tone="primary">{badge}</Badge>
        </span>
      ) : null}
      {promoOn && !free ? (
        <span className="absolute -top-2.5 right-5">
          <Badge tone="primary">{promoBadgeLabel()}</Badge>
        </span>
      ) : null}
      <CardContent className="space-y-4 py-6">
        <div className="space-y-1">
          <p className="eyebrow">{tier.pages}</p>
          <h3 className="font-display text-2xl">{tier.name}</h3>
          <p className="text-sm text-muted-foreground">{tier.tagline}</p>
        </div>
        <p className="flex items-baseline gap-2">
          <span className="font-display text-3xl">{free ? "Free" : formatUSD(now)}</span>
          {promoOn && !free ? (
            <span className="text-sm text-muted-foreground line-through">{formatUSD(tier.priceCents)}</span>
          ) : null}
        </p>
        <ul className="space-y-1.5 text-sm text-muted-foreground">
          {tier.includes.map((line) => (
            <li key={line} className="flex gap-2">
              <span className="text-primary" aria-hidden>
                ·
              </span>
              <span>{line}</span>
            </li>
          ))}
        </ul>
        <Link
          href={free ? "/sample" : `/reports/new?tier=${tier.id}`}
          className={buttonClasses(tier.highlight ? "primary" : "outline", "md", "w-full")}
        >
          {free ? "Start free" : `Choose ${tier.name}`}
        </Link>
      </CardContent>
    </Card>
  );
}

export default async function LandingPage() {
  const user = await getCurrentUser();

  // The server decides whether the offer is running (it knows whether the promotional products
  // are configured, so the discount can fail closed). The client only renders the numbers.
  const promoOn = promoIsLive();
  const offerPairs = PAID_TIERS.map((t) => `${formatUSD(t.priceCents)} → ${formatUSD(offerPriceCents(t))}`);

  // One FAQ entry, and only while the offer is actually running — a "20% off" answer that
  // outlives the offer would be a claim we are not keeping.
  // The demo cards' price and page count come from the tier map, never from a string typed
  // here — a hardcoded "$19" is exactly how the price drift of 2026-10-16 happened.
  const demoItems = [
    { html: "demo-rm-sample.html", pdf: "demo-rm-sample.pdf", tierId: "sample", desc: "Single-chart reading for Kim Nam-joon." },
    { html: "demo-rm-essential.html", pdf: "demo-rm-essential.pdf", tierId: "essential", desc: "Single-chart reading for Kim Nam-joon." },
    { html: "demo-rm-deep.html", pdf: "demo-rm-deep.pdf", tierId: "deep", desc: "Single-chart reading for Kim Nam-joon." },
    { html: "demo-compat-basic.html", pdf: "demo-compat-basic.pdf", tierId: "compat-basic", desc: "Two-chart 궁합 reading across the eleven sub-systems." },
    { html: "demo-compat-deep.html", pdf: "demo-compat-deep.pdf", tierId: "compat-deep", desc: "Two-chart 궁합 reading across the eleven sub-systems." },
  ].map((d) => {
    const t = getTierById(d.tierId);
    return {
      html: d.html,
      pdf: d.pdf,
      desc: d.desc,
      tier: t?.name ?? d.tierId,
      note: t ? `${t.priceCents === 0 ? "Free" : formatUSD(offerPriceCents(t))} · ${t.pages}` : "",
    };
  });

  const faqItems = promoOn
    ? [
        ...FAQ,
        {
          q: "Is there a discount right now?",
          a: `Yes — ${promoBadgeLabel()} ${promoScopeLabel()} through ${promoEndsLabel()}: ${offerPairs.join(", ")}. It is the same reading and the same 10-hour delivery promise; only the price changes. After ${promoEndsLabel()} the standard prices apply.`,
        },
      ]
    : FAQ;

  return (
    <>
      <SiteHeader user={user} />

      <main className="pb-24 lg:pb-0">
        {/* ───────────────────────── 1. Hero ───────────────────────── */}
        <section className="relative overflow-hidden grid-noise">
          <KoreanWatermark char="四柱" />
          <div className="relative mx-auto grid max-w-6xl gap-12 px-4 py-16 sm:px-6 lg:grid-cols-[1.05fr_0.95fr] lg:py-24">
            <div className="flex flex-col justify-center gap-6">
              <div className="flex flex-wrap items-center gap-3">
                <Badge tone="primary">Korean Four Pillars · 사주</Badge>
                <Badge tone="muted">Delivered within 10 hours</Badge>
                {promoOn ? (
                  <Badge tone="primary">
                    {promoBadgeLabel()} {promoScopeLabel()} — through {promoEndsLabel()}
                  </Badge>
                ) : null}
              </div>

              <h1 className="h1">
                Your chart is arithmetic.
                <br />
                The <span className="text-primary">reading</span> is the hard part.
              </h1>

              <p className="lede">
                Saju (사주) reads a life from the four pillars of birth — year, month, day, hour. We compute
                yours from the classical sources, show you exactly what we derived, and then have a person
                check the interpretation before it reaches you.
              </p>

              <div className="flex flex-wrap items-center gap-3">
                <Link href="/sample" className={buttonClasses("primary", "lg")}>
                  Get your free chart snapshot
                </Link>
                <Link href="#demo" className={buttonClasses("outline", "lg")}>
                  See a real report
                </Link>
              </div>

              <p className="text-sm text-muted-foreground">
                No account needed for the snapshot. {formatUSD(offerPriceCents(PAID_TIERS[0]!))} up for the
                full reading.
                {promoOn ? (
                  <>
                    {" "}
                    <span className="line-through">{formatUSD(PAID_TIERS[0]!.priceCents)}</span> — the
                    launch price lasts until {promoEndsLabel()}.
                  </>
                ) : null}
              </p>
            </div>

            {/* Live chart card */}
            <div className="relative">
              <Card className="relative overflow-hidden">
                <div className="absolute inset-0 grid-noise opacity-60" aria-hidden />
                <CardContent className="relative space-y-5 py-6">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="eyebrow">Worked example</p>
                      <p className="font-display text-lg">Kim Nam-joon · 12 Sep 1994, 13:28 KST</p>
                    </div>
                    <SealMark char="印" />
                  </div>

                  <FourPillarsChart pillars={DEMO_PILLARS} />

                  <div className="flex flex-col items-center gap-4 sm:flex-row sm:items-center sm:justify-center">
                    <ElementBalanceWheel counts={DEMO_ELEMENTS} size={150} />
                    <div className="w-full max-w-xs">
                      <ElementBalanceBars counts={DEMO_ELEMENTS} />
                    </div>
                  </div>

                  <ElementLegend counts={{ Wood: 34, Fire: 4, Earth: 17, Metal: 29, Water: 17 }} />

                  <Alert tone="warning" title="Hour-boundary note">
                    The corrected birth time sits seconds from a two-hour branch boundary, so the hour pillar
                    is flagged as lower-confidence. This is the kind of thing an automated tool quietly
                    ignores. We surface it.
                  </Alert>
                </CardContent>
              </Card>
            </div>
          </div>
        </section>

        {/* ───────────────────────── 1b. The offer ───────────────────────── */}
        {/* Only rendered while the offer is running AND the store can charge it. The prices here
            are the same ones the server records on the order — no separate "marketing" number. */}
        {promoOn ? (
          <section aria-label="Launch offer" className="border-y border-primary/30 bg-primary/5">
            <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-7 sm:px-6 lg:flex-row lg:items-center lg:justify-between">
              <div className="space-y-1">
                <p className="font-display text-xl">
                  {promoBadgeLabel()} {promoScopeLabel()}
                </p>
                <p className="text-sm text-muted-foreground">
                  A launch offer through {promoEndsLabel()} — {offerPairs.join(" · ")}. The same readings,
                  the same human review; only the price changes.
                </p>
              </div>
              <Link href="#pricing" className={buttonClasses("primary", "md", "shrink-0")}>
                See the offer prices
              </Link>
            </div>
          </section>
        ) : null}

        {/* ───────────────────────── 2. Why Saju ───────────────────────── */}
        <section id="why" className="border-t border-border bg-surface/60 scroll-mt-20">
          <div className="mx-auto max-w-6xl space-y-10 px-4 py-16 sm:px-6 lg:py-20">
            <SectionHeading
              eyebrow="Why Saju"
              title="A different question from the one astrology asks"
              description="Western astrology starts from the sky at your birth. Saju starts from time itself — a sixty-term cycle that has been refined for two thousand years and applied, in Korea, to marriages, careers, and the timing of a decision."
            />

            <div className="grid gap-5 md:grid-cols-3">
              {[
                {
                  t: "Four pillars, one system",
                  d: "Year, month, day, and hour each become a pair of a heavenly stem and an earthly branch. Eight characters that describe the whole chart before a single word of interpretation.",
                },
                {
                  t: "Five elements in balance",
                  d: "Wood, fire, earth, metal, water — and the relations between them. Your Day Master is strong or weak against the season you were born into, and that decides which element helps you most.",
                },
                {
                  t: "Ten gods, not ten planets",
                  d: "The chart reads through 십신 — the relationships each character has to your Day Master. That's where personality, work, and partnership actually come from.",
                },
              ].map((c) => (
                <Card key={c.t}>
                  <CardContent className="space-y-2 py-5">
                    <h3 className="font-display text-xl">{c.t}</h3>
                    <p className="text-sm leading-relaxed text-muted-foreground">{c.d}</p>
                  </CardContent>
                </Card>
              ))}
            </div>

            <Alert tone="primary" title="What we will not do">
              We will not tell you that something <em>will</em> happen. Readings describe tendencies and
              timing. Where the classical schools genuinely disagree, the reading says so rather than
              picking a side and sounding confident.
            </Alert>
          </div>
        </section>

        {/* ───────────────────────── 3. Demo reports ───────────────────────── */}
        <section id="demo" className="scroll-mt-20">
          <div className="mx-auto max-w-6xl space-y-10 px-4 py-16 sm:px-6 lg:py-20">
            <SectionHeading
              eyebrow="See a report"
              title="Read what you'd actually receive"
              description="Real engine output, unedited, using a public figure's birth data. Download any tier and judge the writing for yourself before spending anything."
            />

            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {demoItems.map((d) => (
                <Card key={d.html} className="flex flex-col">
                  <CardContent className="flex flex-1 flex-col gap-3 py-5">
                    <p className="eyebrow">{d.note}</p>
                    <h3 className="font-display text-xl">{d.tier}</h3>
                    <p className="flex-1 text-sm text-muted-foreground">{d.desc}</p>
                    {/* The web document is what a client reads; the PDF is the
                        keepsake. Same order here, so the marketing matches the product —
                        for the compatibility tiers too. */}
                    <a
                      href={`/demo/${d.html}`}
                      className={buttonClasses("primary", "sm", "w-full")}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Read it
                    </a>
                    <div className="flex gap-2">
                      <a
                        href={`/demo/${d.html}`}
                        download
                        className={buttonClasses("outline", "sm", "w-1/2")}
                      >
                        Save
                      </a>
                      <a
                        href={`/demo/${d.pdf}`}
                        target="_blank"
                        rel="noreferrer"
                        className={buttonClasses("outline", "sm", "w-1/2")}
                      >
                        PDF
                      </a>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* ───────────────────────── 4 + 5. Pricing and comparison ───────────────────────── */}
        <section id="pricing" className="border-t border-border bg-surface/60 scroll-mt-20">
          <div className="mx-auto max-w-6xl space-y-10 px-4 py-16 sm:px-6 lg:py-20">
            <SectionHeading
              eyebrow="Pricing"
              title="Start free. Pay only when you want depth."
              description="Every paid reading is reviewed by a person before delivery. That's the difference between a printout and a reading."
            />

            <div className="grid gap-4 lg:grid-cols-3">
              {SINGLE_TIERS.map((tier) => (
                <TierCard key={tier.id} tier={tier} promoOn={promoOn} />
              ))}
            </div>

            {/* For two people. Both compatibility tiers already existed and were buyable, but this
                grid filtered them out (`kind === "SINGLE"`), so the sharpest differentiator was
                reachable only from inside the dashboard. Same card and same CTA pattern as the
                single-chart tiers — `/reports/new?tier=…` already handles COMPAT (two profiles,
                one order, one review). */}
            <div className="space-y-4">
              <div className="space-y-1">
                <p className="eyebrow">For two people</p>
                <h3 className="font-display text-xl">Read the relationship, not just one chart</h3>
                <p className="text-sm text-muted-foreground">
                  Both charts, compared across eleven classical sub-systems and given a composite
                  score. The Snapshot is the verdict; the Deep reading works through every
                  sub-system and overlays both people&apos;s timing.
                </p>
              </div>
              <div className="grid gap-4 lg:grid-cols-2">
                {COMPAT_TIERS.map((tier) => (
                  <TierCard key={tier.id} tier={tier} badge="Most complete 궁합" promoOn={promoOn} />
                ))}
              </div>
            </div>

            {/* Compare tiers */}
            {/* Scrollable regions must be reachable without a mouse, or the rest of this table is
                invisible to keyboard and screen-reader users at ≤768px (axe
                `scrollable-region-focusable`). `role="region"` + a label also makes it a landmark. */}
            <div
              className="overflow-x-auto"
              tabIndex={0}
              role="region"
              aria-label="Comparison of single-chart report tiers"
            >
              <table className="w-full min-w-[640px] border-collapse text-sm">
                <caption className="sr-only">Comparison of single-chart report tiers</caption>
                <thead>
                  <tr className="border-b border-border text-left">
                    <th scope="col" className="py-3 pr-4 font-medium">Includes</th>
                    {SINGLE_TIERS.map((t) => (
                      <th scope="col" key={t.id} className="px-3 py-3 font-display text-base">
                        {t.name}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="text-muted-foreground">
                  {[
                    ["Four pillars & element balance", [true, true, true]],
                    ["Day Master and strength", [false, true, true]],
                    ["Career & wealth", [false, true, true]],
                    ["Major-luck (대운) table", [false, true, true]],
                    ["Relationships", [false, false, true]],
                    ["Health & vitality", [false, false, true]],
                    ["Year-by-year timing", [false, false, true]],
                    ["Checked by a person, or delivered at 10h", [false, true, true]],
                  ].map(([label, marks]) => (
                    <tr key={label as string} className="border-b border-border/60">
                      <th scope="row" className="py-2.5 pr-4 text-left font-normal text-foreground">
                        {label as string}
                      </th>
                      {(marks as boolean[]).map((m, i) => (
                        <td key={i} className="px-3 py-2.5">
                          {m ? <span className="text-success">✓</span> : <span className="text-border">—</span>}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* ───────────────────────── 6. How it's built ───────────────────────── */}
        <section id="how" className="scroll-mt-20">
          <div className="mx-auto max-w-6xl space-y-10 px-4 py-16 sm:px-6 lg:py-20">
            <SectionHeading
              eyebrow="How it's built"
              title="An engine you can inspect, and a person who can disagree with it"
              description="We'd rather show the machinery than sell the mystique. Here's exactly what happens between your birth details and your inbox."
            />

            <ol className="grid gap-4 md:grid-cols-4">
              {[
                {
                  n: "01",
                  t: "Compute",
                  d: "Solar-time correction for your birthplace, the Korean 야자시 convention for late hours, and the classical lookup tables for ten gods, twelve stages, and special formations.",
                },
                {
                  n: "02",
                  t: "Derive",
                  d: "Day Master strength is argued from the season and the branch support, not asserted. The favourable element (용신) is derived and its provenance recorded.",
                },
                {
                  n: "03",
                  t: "Review",
                  d: "A person reads the draft and can override the engine's favourable-element judgement, then regenerate. That override is the whole point of having a human in the loop.",
                },
                {
                  n: "04",
                  t: "Deliver",
                  d: "Reviewed readings are sent to your inbox and filed in your profile, where you can download them whenever you like.",
                },
              ].map((s) => (
                <li key={s.n} className="card-surface p-5">
                  <p className="font-mono text-xs text-primary">{s.n}</p>
                  <h3 className="mt-2 font-display text-lg">{s.t}</h3>
                  <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{s.d}</p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        {/* ───────────────────────── 7. About the reader ───────────────────────── */}
        <section id="about" className="border-t border-border bg-surface/60 scroll-mt-20">
          <div className="mx-auto flex max-w-4xl flex-col gap-6 px-4 py-16 sm:px-6 lg:py-20">
            <SectionHeading eyebrow="About" title="Who reads your chart" />
            <div className="space-y-4 text-sm leading-relaxed text-muted-foreground">
              <p>
                My name is Harish. I'm not a Korean master, and I'm not going to pretend to be one on a
                website. What I built is a calculation engine that follows classical Korean 명리 — and a
                process where someone actually reads what it produces before you do.
              </p>
              <p>
                The reason is simple. Automated tools are cheap because nobody looks at the output. The
                interpretation is where the work is: arguing the Day Master's strength from the season,
                deciding which element genuinely helps this chart, and knowing when the classical sources
                disagree enough that the honest answer is "we don't know".
              </p>
              <p className="text-foreground">
                So: an accurate engine, and an honest interpreter. Nothing more is claimed.
              </p>
            </div>
          </div>
        </section>

        {/* ───────────────────────── 8. FAQ ───────────────────────── */}
        <section id="faq" className="scroll-mt-20">
          <div className="mx-auto max-w-3xl space-y-8 px-4 py-16 sm:px-6 lg:py-20">
            <SectionHeading eyebrow="FAQ" title="The questions worth asking" />
            <div className="space-y-3">
              {faqItems.map((item) => (
                <details key={item.q} className="card-surface group px-5 py-4">
                  <summary className="cursor-pointer list-none font-display text-lg marker:hidden">
                    <span className="flex items-center justify-between gap-4">
                      {item.q}
                      <span className="text-muted-foreground transition-transform group-open:rotate-45" aria-hidden>
                        +
                      </span>
                    </span>
                  </summary>
                  <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{item.a}</p>
                </details>
              ))}
            </div>
          </div>
        </section>

        {/* ───────────────────────── 9. Final CTA ───────────────────────── */}
        <section className="border-t border-border bg-surface/60">
          <div className="mx-auto max-w-3xl px-4 py-16 text-center sm:px-6 lg:py-20">
            <SectionHeading
              align="center"
              eyebrow="Start here"
              title="See your four pillars first"
              description="The free snapshot gives you the chart, the element balance, and your Day Master. If it doesn't say something true about you, you've lost nothing."
            />
            <div className="mt-6 flex flex-wrap justify-center gap-3">
              <Link href="/sample" className={buttonClasses("primary", "lg")}>
                Get your free chart snapshot
              </Link>
              <Link href="/login" className={buttonClasses("ghost", "lg")}>
                Sign in
              </Link>
            </div>
          </div>
        </section>
      </main>

      <SiteFooter />
      <MobileStickyCta />
    </>
  );
}
