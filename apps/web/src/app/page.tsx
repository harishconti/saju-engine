import Link from "next/link";
import { Alert, Badge, Button, buttonClasses, Card, CardContent, SectionHeading } from "@/components/ui";
import { MobileStickyCta, SiteFooter, SiteHeader } from "@/components/site";
import { getCurrentUser } from "@/lib/auth";
import { ElementBalanceBars, ElementBalanceWheel, ElementLegend, FourPillarsChart, KoreanWatermark, SealMark, type PillarCell } from "@/components/viz";
import { PAID_TIERS, TIERS } from "@/lib/tiers";
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
    a: "The free snapshot is instant. Paid reports are reviewed before they're sent, which usually takes under a day — occasionally longer if you ask a question we want to answer properly.",
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

export default async function LandingPage() {
  const user = await getCurrentUser();

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
                <Badge tone="muted">Reviewed by a human</Badge>
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
                No account needed for the snapshot. {formatUSD(PAID_TIERS[0]!.priceCents)} up for the full
                reading.
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
              {[
                { file: "demo-rm-sample.pdf", tier: "The Hook", note: "Free · ~1 page" },
                { file: "demo-rm-essential.pdf", tier: "The Essential Report", note: "$19 · 6–7 pages" },
                { file: "demo-rm-deep.pdf", tier: "The Deep Destiny Report", note: "$55 · 25–30 pages" },
              ].map((d) => (
                <Card key={d.file} className="flex flex-col">
                  <CardContent className="flex flex-1 flex-col gap-3 py-5">
                    <p className="eyebrow">{d.note}</p>
                    <h3 className="font-display text-xl">{d.tier}</h3>
                    <p className="flex-1 text-sm text-muted-foreground">
                      Single-chart reading for Kim Nam-joon.
                    </p>
                    <a
                      href={`/demo/${d.file}`}
                      className={buttonClasses("outline", "sm", "w-full")}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Open the PDF
                    </a>
                  </CardContent>
                </Card>
              ))}

              {[
                { file: "demo-compat-basic.pdf", tier: "Compatibility Snapshot", note: "$24 · ~4 pages" },
                { file: "demo-compat-deep.pdf", tier: "Deep Compatibility", note: "$45 · 9–10 pages" },
              ].map((d) => (
                <Card key={d.file} className="flex flex-col">
                  <CardContent className="flex flex-1 flex-col gap-3 py-5">
                    <p className="eyebrow">{d.note}</p>
                    <h3 className="font-display text-xl">{d.tier}</h3>
                    <p className="flex-1 text-sm text-muted-foreground">
                      Two-chart 궁합 reading across the eleven sub-systems.
                    </p>
                    <a
                      href={`/demo/${d.file}`}
                      className={buttonClasses("outline", "sm", "w-full")}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Open the PDF
                    </a>
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
              {TIERS.filter((t) => t.kind === "SINGLE").map((tier) => (
                <Card
                  key={tier.id}
                  className={tier.highlight ? "border-primary/50 relative" : undefined}
                >
                  {tier.highlight ? (
                    <span className="absolute -top-2.5 left-5">
                      <Badge tone="primary">Most complete</Badge>
                    </span>
                  ) : null}
                  <CardContent className="space-y-4 py-6">
                    <div className="space-y-1">
                      <p className="eyebrow">{tier.pages}</p>
                      <h3 className="font-display text-2xl">{tier.name}</h3>
                      <p className="text-sm text-muted-foreground">{tier.tagline}</p>
                    </div>
                    <p className="font-display text-3xl">
                      {tier.priceCents === 0 ? "Free" : formatUSD(tier.priceCents)}
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
                      href={tier.priceCents === 0 ? "/sample" : `/reports/new?tier=${tier.id}`}
                      className={buttonClasses(tier.highlight ? "primary" : "outline", "md", "w-full")}
                    >
                      {tier.priceCents === 0 ? "Start free" : `Choose ${tier.name}`}
                    </Link>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Compare tiers */}
            {/* Scrollable regions must be reachable without a mouse, or the rest of this table is
                invisible to keyboard and screen-reader users at ≤768px (axe
                `scrollable-region-focusable`). `role="region"` + a label also makes it a landmark. */}
            <div
              className="overflow-x-auto"
              tabIndex={0}
              role="region"
              aria-label="Comparison of report tiers"
            >
              <table className="w-full min-w-[640px] border-collapse text-sm">
                <caption className="sr-only">Comparison of report tiers</caption>
                <thead>
                  <tr className="border-b border-border text-left">
                    <th scope="col" className="py-3 pr-4 font-medium">Includes</th>
                    {TIERS.filter((t) => t.kind === "SINGLE").map((t) => (
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
                    ["Reviewed by a human", [false, true, true]],
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
              {FAQ.map((item) => (
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
