# MVP Go-to-Market Strategy — Saju Manual Delivery (First 200 Customers)

**Date:** 2026-06-26
**Scope:** The shortest path from today to first paid customer — no web app, no backend, manual WhatsApp/email delivery. Validates product-market fit before committing to the 12-week architecture buildout in `13-architecture-saju-web-cosmicid.md`.
**Companion files:**
- `14-mvp-go-to-market.html` — visual/printable version of this strategy
- `13-architecture-saju-web-cosmicid.md` — the full architecture to graduate into once validated

---

## 0. The thesis in one paragraph

**Don't build the web app until customers are paying you.** The architecture research describes a 12-week build of FastAPI + Postgres + Razorpay + Vercel + Next.js + Clerk + Google Play RTDN. That's the right *eventual* shape. But none of it is needed for the first 200 customers — those can be served with Instagram Reels + WhatsApp + Razorpay Payment Links + this repo's existing engine + Gmail. Total tooling cost: **₹0/mo**. Validate demand first, automate second.

---

## 1. MVP workflow (no code, no app)

```
Customer sees Instagram Reel
        │
        ▼
Clicks bio link (WhatsApp or Google Form)
        │
        ▼
Fills intake (name, DOB, time, location)
        │
        ▼
You send Razorpay Payment Link via WhatsApp
        │
        ▼
Customer pays ₹1,499
        │
        ▼
You run 2 commands (chart + PDF) — 5 min
        │
        ▼
You personalize the engine draft — 15-20 min
        │
        ▼
You email + WhatsApp the PDF
        │
        ▼
You ask for testimonial (offer ₹200 off next reading)
```

**Time per customer: 25–35 minutes.**
**Tooling cost: ₹0/mo + Razorpay 2% per transaction.**

### Tools you need (all free or near-free)

| Tool | Use | Cost |
|---|---|---|
| Instagram business account | Discovery + funnel | Free |
| WhatsApp Business | Intake + delivery | Free |
| Google Form (optional) | Structured intake | Free |
| Razorpay Payment Links | No-code checkout | Free + 2% per txn |
| Gmail | PDF delivery | Free |
| `tools/saju_engine/` | Chart calculation | Already built |
| `tools/build-pdf.sh` | PDF rendering | Already built |

---

## 2. Pricing — simplify to ONE product

The 3-tier structure (`Spark` / `Reading` / `Full Map`) was designed for an automated web app where customers self-serve. For manual delivery, **one product is enough** until you have evidence of demand breadth.

### The only product (for now)

| Field | Value |
|---|---|
| Name | **The Reading** |
| Price | **₹1,499** |
| Format | 10–12 page PDF |
| Sections | Cover, Chart at a Glance, Day Master Portrait, Career & Wealth, Relationships, Health & Vitality, Timing (대운 + annual), Practical Guidance, Closing Note |
| Generation | Engine premium report (tier=reading) + founder personalization |
| Delivery | WhatsApp + email, 24–48h turnaround |
| Support | 1 free follow-up question by WhatsApp within 30 days |

### What this price point means

- ₹1,499 is high enough for **serious margin** even at 25 min/customer (effective rate ≈ ₹3,600/hr)
- Low enough for **impulse conversion** on Instagram after a strong Reel
- Comparable to mid-tier Indian astrology products (Anytime Astro, Astroyogi consultations run ₹500–2,000)
- Anchors future pricing (when you add `Full Map` at ₹3,499, customers see it as premium)

### What to NOT sell yet

- ❌ **Spark (₹499)** — eats your time at this delivery rate, customers who want cheap aren't your tribe
- ❌ **Full Map (₹3,499)** — needs founder review depth you can't sustain at <50 customers
- ❌ **Companion subscription (₹799/mo)** — needs web dashboard, save for Phase 5
- ❌ **궁합 compatibility (₹999 standalone)** — can add as add-on after 50 customers

### Volume math

| Scenario | Customers/week | Monthly revenue (gross) | After Razorpay 2% | Notes |
|---|---|---|---|---|
| Slow start | 2 | ₹11,992 | ₹11,752 | Side income, validating |
| Healthy | 5 | ₹29,980 | ₹29,380 | Real side business |
| Scaling | 10 | ₹59,960 | ₹58,760 | Hire part-time reader |

**5 customers/week × ₹1,499 = ₹30k/week ≈ ₹15L/year.** That's serious side income.

### Add-on revenue (after month 2)

Once you have 20+ base customers, you can offer:
- **Career deep-dive add-on:** ₹499
- **Relationship deep-dive add-on:** ₹499
- **궁합 compatibility (with another person):** ₹999
- **Year-ahead forecast (December):** ₹999

These don't require a new product, just a new file in the customer's existing folder per the CLAUDE.md candidate-report folder structure.

---

## 3. The exact manual workflow (copy-paste ready)

Once a customer pays, here's the literal command sequence for a placeholder name "Priya Sharma":

### Step 1: Build the chart + premium markdown (1 min)

```bash
cd /mnt/data2/git_repos/saju

python -m saju_engine \
  --name "Priya Sharma" \
  --dob 1992-08-15 \
  --time 14:30 \
  --location "Mumbai, IN" \
  --utc-offset-min 330 \
  --gender female \
  --format premium \
  --tier reading \
  --output-file candidates_horoscope/reports/priya-sharma/priya-sharma-report.md
```

This generates the 10–12 page markdown draft marked `[ENGINE DRAFT — REVIEW REQUIRED]`.

### Step 2: Review + personalize (15–20 min)

1. Open `candidates_horoscope/reports/priya-sharma/priya-sharma-report.md`
2. Read through the engine-drafted prose
3. Refine each section using your CLAUDE.md rules + `knowledge/` citations
4. Replace any placeholders with concrete personalization
5. Remove `[ENGINE DRAFT — REVIEW REQUIRED]` markers
6. Add a personal note at the top (1–2 lines about why their chart stood out to you)

### Step 3: Render PDF (30 sec)

```bash
./tools/build-pdf.sh priya-sharma
```

Outputs `priya-sharma-report.pdf` next to the `.md`.

### Step 4: Deliver (5 min)

**Email template:**
```
Subject: Your Korean Saju Reading — Priya ✨

Hi Priya,

Your Reading is attached. The PDF covers your Day Master, your major luck periods
running out to age 60, and the elements that support you.

Quick highlights:
- Your Day Master is [丙] (the Sun) — [one-line insight]
- Your favorable element is [Earth] — [one practical recommendation]
- Your next major luck shift is in [year] — [one-line preview]

If anything resonates (or doesn't), reply to this email or WhatsApp me within
30 days — one follow-up question is included.

Wishing you clarity,
[Your name]

Confidential — prepared for Priya Sharma
```

**WhatsApp message:**
```
🌙 Priya, your Reading is ready.

📧 Sent to your email just now.
📎 Also attached here for easy reading on phone.

A few highlights you'll find inside:
• Day Master [丙] — what that means for how you lead
• Your favorable element + how to use it
• Your next 10 years of major luck shifts

One free follow-up question within 30 days — just message here.

Thanks for trusting me with your chart 🙏
```

### Step 5: Ask for testimonial (2 min)

After 24h, send:
```
🙏 One small ask, Priya:

If anything in the Reading resonated, I'd love a 2-line testimonial
(just your first name + city is fine). It helps others decide.

In return, ₹200 off your next reading or follow-up question.

No pressure either way!
```

### Total time per customer

| Step | Time |
|---|---|
| Step 1: Generate | 1 min |
| Step 2: Personalize | 15–20 min |
| Step 3: Render PDF | 30 sec |
| Step 4: Deliver | 5 min |
| Step 5: Testimonial ask | 2 min |
| **Total** | **25–30 min** |

---

## 4. How to get clients — channels ranked by ROI

### Tier 1: Free + fast feedback (Week 1–4)

#### A. Instagram Reels — the primary channel

**Why Instagram:** Highest concentration of astrology-interested women 22–45 in urban India. Reels reach non-followers via Explore. WhatsApp click-to-chat in bio is frictionless.

**Hook formulas (proven for astrology niche):**
- "Your Day Master reveals how you handle stress" — universal appeal
- "What's your 천간 (Heavenly Stem)? Comment your birth year" — engagement bait
- "Day Master 丙 = The Sun. Here's what that means" — educational
- "Your birth month reveals your zodiac animal — but Day Master is more accurate"
- "5 things a Korean Saju reader knows that you don't" — listicle

**Production recipe (30–60 sec Reel):**
1. Hook (text on screen, 0–3 sec): bold claim or question
2. Voiceover or text overlay (3–25 sec): the insight
3. Visual: chart screenshot from your engine output, or simple animated text
4. CTA (last 5 sec): "Get your Reading — link in bio"

**Music:** Soft Korean instrumental (search "Korean traditional background"). Don't use trending pop — wrong vibe.

**Posting frequency:** 3–4 Reels/week. Daily is better but burns you out. Consistency beats volume.

**Hashtags (mix of broad + niche):**
```
#koreansaju #bazi #fourpillars #fourpillarsofdestiny
#사주 #koreanastrology #indianastrology #zodiac
#astrology #daymaster #odiac #odiac
#spirituality #mindfulness #selfdiscovery
```

**Bio template:**
```
🌙 Korean Saju (사주) Readings
📜 Classical tradition · 경락고요 · 적천수
✨ Get your Reading → WhatsApp below
📩 DM for free Day Master sample
```

**The "link in bio" trap:** Instagram only allows one bio link. Use a free Linktree (linktr.ee) with:
1. WhatsApp click-to-chat (primary)
2. Email contact
3. Instagram (recursive, but used by some)
4. Testimonials page (later)

#### B. WhatsApp Status (daily, free)

Your existing contacts are your first 100 potential customers. They already trust you.

**Daily status ideas:**
- Quote-of-the-day from `knowledge/` (e.g., "甲木 people grow best when rooted — that's why your environment matters more than your effort")
- Behind-the-scenes: "Just finished a Reading for a 丙 day master — her career chapter for the next decade is going to surprise her"
- Testimonial (with permission, screenshot from chat)
- Countdown: "5 Reading slots open this week"
- Day Master spotlight series: post about one Day Master per week, all 10 over 10 weeks

#### C. YouTube Shorts (repurpose Reels)

Same video, uploaded to YouTube Shorts. Doubles your surface area with zero extra work. YouTube search drives long-tail traffic for years.

### Tier 2: Build your portfolio (Week 1–2, before charging)

#### D. 5 free pilot readings — DO THIS FIRST

**This is the single most important step.** Before you charge anyone, deliver 5 free readings to friends/family and collect 5 testimonials.

**Why 5:** One testimonial is an anecdote. Five is a pattern. Five diverse charts let you claim "I've read charts for software engineers, teachers, mothers, students, and business owners."

**Pilot selection criteria:**
- Mix of ages (different 대운 stages)
- Mix of genders
- Mix of professions
- Different Day Masters (so you can showcase variety)
- People who will give honest feedback, not just "wow amazing"

**What to ask in exchange:**
- Written testimonial (3 lines minimum): their name, city, biggest insight from the reading
- Permission to share anonymized chart snippets (e.g., "a 28-year-old teacher with 壬 day master")
- Video testimonial (bonus, ₹200 credit): 30-second selfie testimonial

**Deliver the FULL premium experience:**
- Same engine output, same 15-min personalization
- Same email template, same WhatsApp message
- Don't cut corners — the pilot is your template

**Store outputs in:**
```
candidates_horoscope/case-studies/
  ├── 01-pilot-software-engineer-bangalore.md
  ├── 02-pilot-teacher-mumbai.md
  ├── 03-pilot-mother-delhi.md
  ├── 04-pilot-student-pune.md
  └── 05-pilot-business-owner-hyderabad.md
```

These become:
- Anonymized content for Reels
- Social proof in your bio link
- Validation that your workflow works

#### E. Reddit (low-frequency, high-quality)

- Subreddits: r/astrology, r/BaZi, r/IndianAstrology, r/spirituality
- 2–3 genuine comments/week answering questions about Day Masters, 용신, etc.
- Link in profile (NOT in comments — gets you banned)
- Position as practitioner, not promoter
- Over time, this builds E-E-A-T (Experience, Expertise, Authority, Trust) for SEO

#### F. Quora (long-term SEO)

- Answer: "What is Korean Saju?", "What does my Day Master mean?", "How is Korean Saju different from Vedic astrology?"
- 2,000+ word answers with charts and examples
- Link to your Instagram/WhatsApp in profile
- Old answers keep driving traffic for years (passive lead gen)

### Tier 3: Paid marketing (after 20+ customers)

#### G. Instagram/Facebook Ads

Only start when:
- You have 5+ testimonials
- Your organic Reels are getting consistent views (>1k per Reel)
- You have a free lead magnet to capture interest

**Budget:** ₹500–1,000/day test. Scale to ₹2k/day once cost-per-lead is <₹100.

**Funnel:**
1. Ad: "Your Day Master reveals your stress pattern — free sample inside"
2. Landing page: free "Day Master one-pager" PDF in exchange for email
3. Email sequence: 3 emails over 7 days with insights + CTA to paid Reading
4. WhatsApp: closer for ₹1,499 sale

**Targeting:**
- India, 22–45
- Female-skewed (60F/40M based on astrology app demographics)
- Interests: tarot, astrology, spirituality, mindfulness, self-improvement
- Lookalike audiences based on your WhatsApp contact list (after 100+)

### Channels to SKIP for now

- ❌ **Twitter/X** — wrong audience for this niche in India
- ❌ **LinkedIn** — wrong demographic, too professional for astrology
- ❌ **TikTok** — banned in India
- ❌ **Google Ads** — too expensive for unproven funnel, save for Phase 5
- ❌ **Pinterest** — wrong demographic for paid astrology
- ❌ **Telegram** — works for crypto, not for this niche in India
- ❌ **Own website/blog** — premature; Instagram bio link is enough

---

## 5. The 1-page funnel — minimum viable landing page

You don't need a website yet. Two options, pick based on volume.

### Option A: WhatsApp-only (Day 1, recommended to start)

**Instagram bio:**
```
🌙 Korean Saju (사주) Readings
📜 Classical tradition · 경락고요 · 적천수
✨ Get your Reading → WhatsApp below
📩 DM for free Day Master sample
```

**WhatsApp click-to-chat URL format:**
```
https://wa.me/91XXXXXXXXXX?text=Hi%2C%20I%27d%20like%20a%20Korean%20Saju%20Reading
```

**Auto-reply (set up in WhatsApp Business):**
```
🌙 Thanks for reaching out!

To prepare your Korean Saju Reading, I need:

1. Full name
2. Date of birth (DD/MM/YYYY)
3. Exact birth time (or "approximate")
4. Birth city
5. Gender

I'll send you a payment link within a few hours.
Reading delivered in 24-48h as a beautiful PDF.

✨ Free Day Master sample available — just ask!
```

**When they reply with details:**
```
Perfect, thank you 🌙

Your Reading covers:
• Day Master portrait
• Career & wealth chapter
• Relationships & compatibility style
• Health tendencies
• Major luck periods (next 10-20 years)
• Practical guidance + favorable elements

Price: ₹1,499
Delivery: 24-48h after payment

I'll send the Razorpay payment link in a moment.
```

**Send Razorpay Payment Link:**
- Generate in Razorpay dashboard (no API needed)
- ₹1,499, description "Korean Saju Reading — [Name]"
- Share via WhatsApp
- Customer pays via UPI/card/netbanking
- You get instant notification

**After payment confirmed:**
```
Payment received — thank you 🙏

Your Reading is in progress. I'll send it within 24-48h via email + WhatsApp.

If you have a specific question you'd like me to address, let me know now.
```

### Option B: Google Form (Day 3, when getting 3+ DMs/day)

Create form with fields:
- Full name
- Date of birth (DD/MM/YYYY)
- Birth time (HH:MM)
- Birth city
- Gender (M/F/Other/Prefer not to say)
- Email address
- Relationship status (optional)
- "What's your main question for the Reading?" (text area)

Form auto-saves to Google Sheets. Set up email notification. You follow up on WhatsApp with payment link.

**Recommendation: Start with Option A. Graduate to Option B once you're getting 3+ DMs/day or starting to forget details.**

---

## 6. Free lead magnet — the Day Master one-pager

Before customers pay ₹1,499, give them a taste. A 1-page PDF for free.

### Generate it

```bash
cd /mnt/data2/git_repos/saju

# For a real lead (use their actual birth data)
python -m saju_engine \
  --name "Lead Name" \
  --dob 1990-06-15 \
  --time 10:30 \
  --location "Delhi, IN" \
  --utc-offset-min 330 \
  --format spark \
  --tier spark \
  --output-file /tmp/day-master-sample.md

./tools/build-pdf.sh /tmp/day-master-sample.md
```

Or use the existing candidate reports as samples (anonymized).

### Use it as

- **Instagram DM response** when someone says "I'm interested but not sure": "Let me send you a free sample so you can see what you get"
- **Lead magnet for ads** (later, Phase Tier 3)
- **Email attachment** for "Is this for me?" leads
- **WhatsApp broadcast** to your status viewers (occasional, not spammy)

### What to include in the sample

A 1-pager with:
- Their Day Master in 한자 (e.g., 丙火)
- One-line Day Master description (e.g., "丙 = The Sun — bright, generous, visionary")
- Element balance mini-chart
- One teaser insight (e.g., "Your favorable element is Earth — grounding will help you most")
- CTA: "Want the full 12-page Reading? ₹1,499 → WhatsApp +91-XXXXXXXXXX"

This works because it gives value upfront (they learn something real about themselves) AND shows what the paid product looks like.

---

## 7. Operational checklist (Day 1 → Day 14)

### Day 1–2: Setup

- [ ] Create Instagram business account (use your existing personal if you have one)
- [ ] Set up Linktree with WhatsApp link (free)
- [ ] Set up WhatsApp Business with auto-reply (free)
- [ ] Draft the DM intake script (copy from §5 above)
- [ ] Create Razorpay Payment Link template (₹1,499, "Korean Saju Reading")
- [ ] Save all scripts to `templates/` folder in this repo
- [ ] Take 3 photos of yourself (for Instagram profile + first posts)
- [ ] Write a short bio (50–80 words)

### Day 3–5: Free pilots

- [ ] Pick 5 friends/family — diverse ages, charts, professions
- [ ] Generate 5 readings using the engine (use real birth data)
- [ ] Spend 20 min each personalizing (no shortcuts on pilots)
- [ ] Deliver PDFs to pilots, ask for written testimonials
- [ ] Collect: name, city, biggest insight from the reading, optional 30-sec video
- [ ] Save testimonials in `candidates_horoscope/case-studies/` (anonymize if needed)

### Day 6–7: Portfolio + first posts

- [ ] Create `candidates_horoscope/case-studies/` folder with 5 anonymized pilot summaries
- [ ] Post 3 Reels:
  - Reel 1: Hook "What is Korean Saju?" — educational, 45 sec
  - Reel 2: Highlight one pilot's Day Master insight (with permission, anonymized)
  - Reel 3: Behind-the-scenes — your reading setup, engine output, PDF render
- [ ] Update bio with first testimonial snippet
- [ ] Send WhatsApp broadcast to your contacts: "I now offer Korean Saju Readings 🌙"

### Day 8–10: First paid customer

- [ ] Someone DMs you → you run the workflow (§3) → deliver within 48h
- [ ] Ask for video testimonial (offer ₹200 off next reading)
- [ ] Post the testimonial Reel (with permission, blur their face if they prefer)
- [ ] Note what worked: which Reel drove the DM? Which hook converted? Double down.

### Day 11–14: Iterate

- [ ] 2–3 more paid customers
- [ ] Notice: which Reels get DMs? Double down on those hooks
- [ ] Notice: where do customers get stuck in payment? Fix the link flow
- [ ] Notice: which Day Masters do people ask about most? Make those Reels
- [ ] Adjust pricing if conversion is too low (test ₹999 vs ₹1,499 with different cohorts)

### Day 15–30: 20-customer milestone

- [ ] If you have 5+ customers/week → keep going, hire a part-time reader
- [ ] If you have 1–2/week → tweak hooks, try different content, ask pilots for referrals
- [ ] If you have 0 → reassess pricing or positioning, consider niching down

### Day 30+: Decision point

After 30 days and 10+ paid customers, evaluate against the 3 graduation signals (§8).

---

## 8. When to graduate to the full architecture

**Don't build the web app until you see ALL 3 signals:**

| Signal | Threshold | Why it matters |
|---|---|---|
| **Consistent demand** | 5+ paid customers/week for 4 weeks straight | Proves product-market fit. Worth the 12-week build. |
| **Manual time bottleneck** | Spending 20+ hrs/week on delivery | Proves automation ROI. Your time is the limiting factor. |
| **Quality holds** | Refund/complaint rate <10% | Proves the engine + your personalization scales. |

### Decision matrix

| Signals hit | Action |
|---|---|
| 0 of 3 | Keep manual. Don't build. |
| 1 of 3 (usually just demand) | Keep manual, optimize the workflow. Build a Google Form. |
| 2 of 3 (demand + bottleneck) | Hire a part-time reader. Defer the app. |
| All 3 of 3 | Start the architecture plan (`13-architecture-saju-web-cosmicid.md`) Phase 1. |

### Why this discipline matters

Most failed astrology businesses built the app first, then had no customers. The instinct to "automate so I can scale" is wrong if you don't yet know:
- What hook converts (Instagram? YouTube? Reddit?)
- What price converts (₹999? ₹1,499? ₹2,499?)
- What product converts (Reading? 궁합? Year-ahead?)
- What delivery works (WhatsApp? Email? In-app?)

All of these only reveal themselves through manual delivery. Automate after you know.

**Hard rule: Do NOT spend 12 weeks building the web app until you've validated that customers pay at ₹1,499 for a Korean Saju Reading delivered via WhatsApp.**

---

## 9. Content ideas — 30 Reels in 30 days

To save you thinking, here's a month of content:

### Week 1: Educational (build authority)
1. "Korean Saju vs Chinese BaZi — what's the difference?"
2. "What is a Day Master?" (60-second explainer)
3. "The 5 elements in 60 seconds"
4. "Why your birth TIME matters more than your birth DATE"

### Week 2: Hooks (drive DMs)
5. "Comment your birth year — I'll tell you your Day Master"
6. "Day Master 丙 = The Sun. Here's what that means for you"
7. "Day Master 壬 = The Ocean. The deepest of all stems"
8. "If you were born in [month], your zodiac animal is [X] — but your Day Master is more accurate"

### Week 3: Testimonials (social proof)
9. Pilot 1's biggest insight (anonymized)
10. Pilot 2's biggest insight (anonymized)
11. Pilot 3 video testimonial (with permission)
12. "5 readings, 5 life paths — what I learned"

### Week 4: Behind-the-scenes (build trust)
13. "How I read a chart — the 5-step process"
14. "What's inside a Korean Saju Reading" (PDF walkthrough)
15. "Why I quote 경락고요 and 적천수"
16. "The difference between a Saju reader and a fortune teller"

### Bonus days (29–30): Deep dives
17. "용신 — your favorable element, explained"
18. "What 'major luck periods' actually mean for your 20s, 30s, 40s"
19. "Korean Saju vs Vedic astrology — which is more accurate?"
20. "궁합 — how compatibility actually works in classical Saju"

(That's 20 — extend with more hooks and testimonials as you go.)

---

## 10. Pricing experiments to consider

After 10 customers, you'll have data. Consider:

| Experiment | Hypothesis | How to test |
|---|---|---|
| Price ₹999 vs ₹1,499 | Lower price = more volume but lower quality leads | A/B test with two different Reels |
| Add ₹499 follow-up question | Existing customers want more depth | Just ask — offer once, see uptake |
| Year-end "year-ahead" Reading ₹999 | December is peak astrology interest | Test in November |
| Couples 궁합 ₹1,999 | Couples buy together | Test after 30 single customers |

**Don't run more than one experiment at a time.** You'll lose attribution.

---

## 11. What the existing research supports that you're NOT using yet

Quick wins sitting in your repo:

| Asset | Location | Use |
|---|---|---|
| 5+ real candidate charts | `candidates_horoscope/` | Anonymize for case studies |
| 12운성 tables | `knowledge/06-twelve-stages.md` | "Day Master explainer" Reel content |
| Prose scaffold drafts | `tools/saju_engine/prose_scaffold.py` | Cuts your personalization time |
| Combine tool | `tools/combine_candidate_report.py` | Add follow-up topics as paid add-ons |
| HTML/Playwright PDF backend | `tools/md_to_saju_html_pdf.py` | Premium-looking PDFs for paying customers |
| Tiered premium generator | `tools/saju_engine/premium_report.py` | Already does the 9-section layout |

**You already have everything needed to deliver the ₹1,499 Reading.** The architecture plan only adds automation, not new product capability.

---

## 12. Risks and mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| No customers in first 30 days | Medium | Iterate hooks, ask pilots for referrals, try Reddit |
| Customers complain about generic advice | Medium | Always personalize — never send raw engine draft |
| Birth time uncertain | High | Default to 12:00 (noon), note uncertainty in Reading, offer rectification later |
| Time zone confusion | Medium | Always ask UTC offset or country, cross-verify city |
| Refund request | Low initially | 7-day no-questions-asked refund policy, build into Terms |
| "Fortune-telling" perception | Medium | Position as "self-knowledge tool" not "prediction", use language carefully |
| Competitor copies your hooks | Low | Your edge is personalization + classical tradition citations |
| Burnout from personalization | High after 20 customers | Hire part-time reader by customer #25 |

---

## 13. Success metrics to track weekly

Create a simple Google Sheet with these columns:

| Date | DMs received | Pilots delivered | Paid orders | Revenue (₹) | Avg delivery time | Testimonials collected |
|---|---|---|---|---|---|---|

Review weekly. The two key metrics:
1. **Conversion rate:** DMs → paid orders (target: 20–30%)
2. **Reel performance:** which hooks drive DMs (double down on winners)

After 50 customers, add:
- Repeat customer rate (% who buy a follow-up)
- Referral rate (% who came from existing customer's word-of-mouth)
- Average testimonial rating (if you start collecting)

---

## 14. Summary — what to do THIS WEEK

If you do nothing else, do these 5 things in the next 7 days:

1. **Create your 5 pilot readings** — 5 friends/family, full premium experience, collect testimonials
2. **Post 3 Instagram Reels** — use the scripts in §9, post one every other day
3. **Set up Razorpay Payment Link** for ₹1,499, save the template
4. **Update your WhatsApp bio + auto-reply** using the scripts in §5
5. **Send your first WhatsApp broadcast** to your contacts: "I now offer Korean Saju Readings 🌙"

If you do those 5 things, you will have:
- 5 testimonials
- 3 pieces of content
- A working payment flow
- A discovery surface
- A pipeline of warm leads

Within 14 days, you should have 1–3 paid customers. Within 30 days, 5–10 paid customers. Within 90 days, you'll know whether to build the app or keep manual.

---

## 15. Privacy & Separation — Don't Use Your Personal Number or WhatsApp Status

**The problem:** Exposing your personal number on Instagram bio, Razorpay receipts, and WhatsApp Business means every curious browser, failed payment, or angry customer has a permanent line to your family chat. Mixing personal WhatsApp Status with business broadcasts pollutes your private feed. If you ever want to hire a part-time reader, sell the business, or take a break, the personal number is welded in.

**The fix:** Keep business and personal in separate silos. Four options, ranked by cost and effort.

### Option A — Dedicated SIM + Business WhatsApp (recommended, ₹150/mo)

**Setup:** Buy a cheap prepaid SIM, put it in a second phone or 4G/WiFi tablet, install WhatsApp Business on that device using the new number. Use that number everywhere — Instagram bio, Razorpay link, auto-reply.

**Why it works:**
- Your personal number stays private — never published, never leaked via a breach
- WhatsApp Business gives you auto-reply, **Labels** (e.g., "New Inquiry", "Paid", "Delivered"), **Quick Replies**, and a **Catalog** — features the personal app doesn't have
- Customers see "Korean Saju by [Name]" as the business name, not your personal contact
- If you need to hand off to a part-time reader later, you hand off the business number, not your life
- A tablet on your desk means business WhatsApp stays out of your personal phone

**Cost:**
| Item | One-time | Monthly |
|---|---|---|
| Prepaid SIM (Airtel/Jio) | ₹100–300 | — |
| ₹99–149 plan (data + SMS) | — | ₹0–149 |
| Tablet (used, 7-inch, WiFi-only) | ₹2,000–5,000 | — |
| **Total** | **₹2,100–5,300** | **₹0–149/mo** |

**Effort:** 1 hour to set up. 24h for SIM activation via Aadhaar eKYC.

### Option B — Virtual Number via BSP (₹999–1,500/mo)

Indian virtual-number services (MyOperator, Exotel, TeleCMI) can give you an Indian mobile number that forwards to your existing phone, with business features like IVR, call recording, multi-agent routing.

**Why consider:**
- No second device needed
- Existing personal phone stays your primary device, business calls forward to it
- Scales to multi-agent when you hire

**Why skip for now:**
- Costs ₹1k+/mo **before you have paying customers**
- Designed for call centers — overkill for solo WhatsApp-first business
- WhatsApp requires SMS verification; most VoIP numbers are blocked by WhatsApp, so you'd still need a real SIM for WhatsApp anyway

**Best for:** After 50+ customers/week when you're hiring readers and want a call-center style setup.

**Skip Option B** until then. International VoIP numbers (Dingtone, Hushed, TextNow) don't work with WhatsApp in India at all — confirmed blocked.

### Option C — WhatsApp Business API via BSP (₹1,000–5,000/mo, scales best)

**Setup:** WhatsApp Business API is the official business version. Your personal number stays personal; API runs in a web dashboard you log into. Get a **green verified checkmark** (requires Facebook Business verification — 2–7 days).

**Indian BSPs (Business Solution Providers):**

| BSP | Cost | Notes |
|---|---|---|
| **Wati.io** | ₹1,000/mo (1,000 conv.) | Easiest onboarding, dashboard UI |
| **AiSensy** | ₹999/mo | Indian, popular, good support |
| **Interakt** | ₹1,499/mo | By Jio Haptik, good for ecommerce |
| **Twilio** | $0.005/msg | Pay-as-you-go, more setup |

**Why consider:**
- **No second phone needed** — log into web dashboard from any browser
- **Green checkmark** = instant trust ("verified business")
- **Broadcast lists** for status updates without exposing personal contacts
- **Chatbot flows** can automate the entire intake → payment → delivery funnel
- Multiple team members can manage the same inbox

**Why skip for now:**
- Costs ₹1k+/mo before you have paying customers
- Requires Facebook Business verification (business docs needed)
- Overkill for the first 10–30 customers

**Best for:** Phase when you have 30+ customers/week and want to scale without more devices.

### Option D — Telegram Bot + Instagram DM only (no phone needed)

Skip WhatsApp entirely. Use Instagram DM for intake (your personal IG), Telegram bot for delivery, email as backup.

**Why consider:**
- Zero new SIM/number needed
- Telegram bots can run the entire flow: intake form → Razorpay link → PDF delivery, automated

**Why skip:**
- Telegram is **not mainstream in India** for astrology — WhatsApp is the default expectation
- Indian customers expect WhatsApp — you'll lose **30–50% of leads** who refuse to install another app
- Loses the "personal touch" that high-LTV astrology buyers value
- Bot development takes 2–3 days vs. 1 hour for WhatsApp Business

**Best for:** International customers (US/UK diaspora) where Telegram is acceptable.

### Recommendation: Option A

For the first 30 customers, **buy the prepaid SIM**. Here's the literal 1-hour setup:

#### Step 1: Buy the SIM (20 min)
- Walk into any Airtel/Jio store
- Ask for a "new prepaid SIM with data plan" (₹100 SIM + ₹149 plan = ₹249 total)
- Bring Aadhaar card for eKYC (instant activation) or passport/voter ID (24h activation)
- Keep the SIM packet — you'll need the phone number for WhatsApp verification

#### Step 2: Set up the device (15 min)
- Use a **tablet** (recommended) or **old phone** — keep business WhatsApp off your primary phone
- Budget tablets: Realme Pad Mini (₹7k new), Samsung Tab A7 Lite (₹8k), Lenovo Tab M7 (₹5k refurbished on OLX)
- Insert SIM, connect to home WiFi (you don't need data — WhatsApp runs on WiFi)
- Install **WhatsApp Business** from Play Store (free, separate from regular WhatsApp)

#### Step 3: Register WhatsApp Business (5 min)
- Open WhatsApp Business, register with the new number
- Wait for SMS verification code (comes to the new SIM's tablet)
- Set business name: **"Korean Saju by [Your Name]"** or **"Korean Saju Readings"** — pick one, don't change later
- Set business category: **"Personal Coach"** or **"Spiritual Advisor"**
- Set business hours: e.g., **Mon–Sat, 10am–8pm IST**

#### Step 4: Configure the business profile (10 min)
- Upload your logo or profile photo (a clean headshot works)
- Write a 200-char description (use the auto-reply script from §5 as the base)
- Add business email: the new dedicated Gmail
- Add business address: optional, your city is fine
- Set the **greeting message** (sent to first-time contacts after 14 days of inactivity)
- Set the **away message** (for after-hours)

#### Step 5: Set up Quick Replies (5 min)
WhatsApp Business lets you save `/shortcuts` for common messages. Create these three:

| Shortcut | Message |
|---|---|
| `/welcome` | The full intake script from §5 (auto-sent to new contacts) |
| `/paid` | "Payment received — thank you 🙏 Your Reading is in progress. I'll send it within 24-48h via email + WhatsApp. If you have a specific question you'd like me to address, let me know now." |
| `/delivered` | "Your Reading is ready 🌙 Sent to your email just now + attached here. One free follow-up question within 30 days — just message here. Thanks for trusting me with your chart 🙏" |

Type `/welcome` in any chat, edit, send. Saves you 5 min per customer.

#### Step 6: Set up Labels (2 min)
Create these labels in WhatsApp Business to track customer status:
- 🟡 **New Inquiry** — just DMed, no details yet
- 🔵 **Awaiting Payment** — details received, payment link sent
- 🟢 **Paid** — payment received, in personalization queue
- 🟣 **Delivered** — PDF sent
- ⚪ **Follow-up** — 30-day window active
- 🔴 **Refund / Issue** — needs attention

Apply the label when you move between stages. Lets you scan your inbox in 5 seconds and know exactly where every customer is.

#### Step 7: Link everything else (5 min)

| Service | What to use |
|---|---|
| **Instagram bio** | Add `https://wa.me/91XXXXXXXXXX` (replace X's with new number) |
| **Razorpay** | Use new business number as contact on Payment Link |
| **Gmail** | Create `yourname.saju@gmail.com` (or `readings.yourname@gmail.com`) |
| **Google Calendar** | Create new calendar "Saju Delivery" — set 48h deadlines for each paid customer |
| **Google Sheets** | Customer tracking sheet uses the business email for sign-in |

### What stays personal vs. what goes business

| Channel | Personal | Business |
|---|---|---|
| Phone number | ✓ | — |
| WhatsApp | — | ✓ (separate number, business app) |
| WhatsApp Status | ✓ (private life) | — (use Broadcast Lists in business app instead) |
| Instagram account | ✓ (your existing IG) | — (or create separate business IG after 50 customers) |
| Gmail | ✓ (existing) | ✓ (new dedicated account) |
| Calendar | ✓ (existing) | ✓ (new "Saju Delivery" calendar) |
| Razorpay account | — | ✓ (your existing business account, separate from personal UPI) |
| Bank account | ✓ (existing personal) | ✓ (current account — required for Razorpay anyway) |

### Decision on Instagram: personal vs. business account

| Approach | Pros | Cons |
|---|---|---|
| **Use existing personal IG** | Faster start, existing followers see content | Customers see personal posts mixed with business |
| **Create separate business IG** | Clean separation, professional, privacy | Starts from 0 followers |

**Recommendation for first 30 customers:** Use your existing personal IG. Your existing followers trust you — that trust converts faster than a fresh account's aesthetic separation. **After 50 customers**, consider a dedicated business IG.

### Replacing WhatsApp Status with Broadcast Lists

You mentioned not wanting to use personal WhatsApp Status. The right business equivalent is **Broadcast Lists** in WhatsApp Business:

| Feature | Personal WhatsApp Status | WhatsApp Business Broadcast List |
|---|---|---|
| Visibility | All your contacts | Only the customers you add |
| Reach | Anyone in your contacts | Only people who have YOUR number saved |
| Frequency | Limited (24h expiry, 1/day for engagement) | Unlimited |
| Targeting | None — broadcast to all | Per-list segmentation (pilots, paid, dormant) |
| Privacy | Personal contacts see it | Your number isn't visible to non-customers |

**How to use:**
1. After every 5 customers, create a Broadcast List
2. Name it: "Active Customers — June 2026" or "Pilots Only"
3. Add customers who opted in (mention this in your first auto-reply: "You'll receive occasional updates on favorable elements, year-ahead forecasts, and Reading slots")
4. Send monthly updates: new Reel teasers, Day Master spotlights, year-end offers
5. **Never** spam — 1 broadcast/month is the ceiling

**Customers never see each other** — it's one-to-many, not a group chat. They just get a regular message from your business number.

### Total cost of privacy

| Option | One-time | Monthly | Time to setup |
|---|---|---|---|
| **A — Dedicated SIM** | ₹2,100–5,300 | ₹0–149 | 1 hour |
| B — Virtual number | ₹0 | ₹999–1,500 | 1 day |
| C — WhatsApp Business API | ₹0 | ₹1,000–5,000 | 1 week (FB verification) |
| D — Telegram bot | ₹0 | ₹0 | 2–3 days |

### Quick action plan (1 hour total today)

1. Walk into Airtel/Jio store → buy prepaid SIM + ₹149 plan (~₹249 total, 20 min)
2. Activate SIM on tablet or old phone with WhatsApp Business (15 min)
3. Set up the auto-reply, quick replies, labels (15 min)
4. Update Instagram bio with the new wa.me link (2 min)
5. Create the dedicated Gmail `yourname.saju@gmail.com` (3 min)
6. Create Google Calendar "Saju Delivery" (2 min)
7. Update Razorpay Payment Link to use new number (5 min)

**Total cost: ₹150 one-time + ₹149/mo** (and only if you actually use SMS/calling — WhatsApp runs on WiFi).

---

## 16. The Landing Page Path — Carrd + Razorpay + Google Form (recommended primary)

**The thesis:** A simple landing page with testimonials, sample reports, intake form, and payment link is the **cleanest path from Instagram Reel to paid customer** — better than Instagram DM, comparable to WhatsApp, with **full privacy** (your personal number and WhatsApp stay untouched).

### Why this beats Instagram DM and WhatsApp for your situation

| Factor | Instagram DM | WhatsApp Business | **Landing page** |
|---|---|---|---|
| Customer effort | High (DM → wait → back-and-forth) | Medium (DM → wait) | **Low (form + pay)** |
| Time to intake | 15+ min of DM ping-pong | 5–10 min | **2 min (form)** |
| Conversion (cold visitor) | 5–15% | 15–25% | **20–35%** |
| Looks professional | Medium | Low (just a chat) | **High** |
| SEO (Google ranks it) | ❌ | ❌ | ✅ |
| Works without you online | ❌ (needs your reply) | ❌ (needs your reply) | ✅ (form works at 3am) |
| Personal number exposed | ❌ | ❌ | **❌ (never collected)** |
| Personal WhatsApp exposed | ❌ | ❌ | **❌ (never collected)** |
| Set-up time | 0 | 1 hr | **4–8 hrs first time** |
| Set-up cost | ₹0 | ₹150 + tablet | **₹500–1,500** |

**The killer feature:** A landing page + Razorpay means **a customer can buy at 11pm on a Sunday without you being awake.** Instagram DMs require your reply. WhatsApp requires your reply. Landing page = zero you-time per sale.

### Why this solves the privacy problem completely

With a landing page + Razorpay, **you never need to give out your number.** The full flow:
1. Customer → landing page (public, anonymous)
2. Customer → Razorpay (Razorpay handles payment, you see no card details)
3. Customer → Google Form (your dedicated Gmail receives the intake)
4. You → send PDF (from your dedicated Gmail, to customer's email)

Personal number and personal WhatsApp stay 100% private. This is the cleanest privacy solution short of building a full web app.

### What the page actually contains (4 sections, no fluff)

#### Section 1: Hero

```
[Your photo, warm lighting, looking at camera]

Korean Saju (사주) Reading
Classical tradition · 경락고요 · 적천수

A 12-page personal reading of your
birth chart — your Day Master, your
favorable element, your next decade.

→ Get your Reading · ₹1,499
```

#### Section 2: What's inside (the 9 sections)

- ✦ **Day Master Portrait** — who you are at your core, beyond sun signs
- ✦ **Career & Wealth** — where your energy naturally compounds
- ✦ **Relationships** — how you love, who you click with
- ✦ **Health & Vitality** — element-based tendencies to watch
- ✦ **Major Luck Periods** — your next 10-20 years, mapped
- ✦ **Practical Guidance** — colors, directions, foods, timing
- ✦ **Closing Note** — what I'd tell you if we met for coffee

Delivered as a 12-page PDF in 24-48 hours.

#### Section 3: Sample (the magic ingredient)

This is the **single most important section**. A real sample preview is the difference between "interesting" and "I trust this person with my birth chart."

Show a screenshot of page 1 + 2 of a real Reading (anonymize the name). Or embed a 3-page PDF preview using a `<embed>` tag.

> This is Priya's chart. Her Day Master is 壬 (The Ocean). Notice how her career chapter connects to her element balance. The full version has 12 pages.

#### Section 4: Testimonials + Buy

3+ testimonials with name, age, city, star rating:

> "Priya's Reading was eerily accurate about my career timing. The major luck periods mapped perfectly to my actual job changes." — Ananya, 32, Bangalore ★★★★★

> "I've had Vedic and Western readings before. This was different — more grounded, more practical. The favorable element advice actually worked." — Rahul, 41, Mumbai ★★★★★

**Buy button** (links to Razorpay Payment Link):

```
Get your Korean Saju Reading
₹1,499 · 12 pages · 24-48h delivery
→ Pay with Razorpay
```

**Below the buy button:**

```
What happens after you pay:

1. You fill the intake form (name, DOB, time, location) — 2 minutes
2. I run the chart through a classical-tradition engine
3. I personalize each section based on your specifics
4. PDF delivered to your email within 48 hours
5. One free follow-up question within 30 days

[7-day refund policy · No questions asked]
```

### The tech stack: Carrd.co (₹750/yr, ship in 1 day)

**What it is:** Simple landing-page builder. Drag-and-drop, mobile-responsive, custom domain support.

| Carrd feature | Why it matters for you |
|---|---|
| Mobile-perfect automatically | 80%+ of your traffic is mobile |
| Custom domain support | Use `cosmicsaju.com/saju` or `getmyreading.in` |
| Form integration | Connects to Google Forms / Razorpay |
| No code, no hosting | You focus on copy, not infrastructure |
| Free SSL | Looks trustworthy (HTTPS, padlock icon) |
| Looks modern | Better than most hand-coded pages |

**Limitations to know:**
- Limited to 1 page (~10 sections) — fine for landing page, not for full web app
- No blog (you can add a separate blog later if needed)
- Limited analytics (basic visitor counts only)
- Doesn't scale to a full web app — you'll rebuild on Next.js if you cross 200+ customers

**Alternatives if Carrd feels too limited:**

| Tool | Cost | When to use |
|---|---|---|
| **Carrd.co** | ₹750/yr | Recommended for first 200 customers |
| Framer.com | ₹3,500/yr | If you want more design freedom + a blog |
| WordPress.com | ₹3,000/yr | If you want a blog from day 1 |
| Next.js + Vercel | ₹0–25k setup + 12 weeks | After you validate demand |

### Step-by-step setup (1 day, ₹1,500 total)

#### Step 1: Buy domain (₹10, 10 min)

Buy on Cloudflare Registrar or any registrar:

| Option | Cost | Notes |
|---|---|---|
| `cosmicsaju.com` (or `saju.cosmicsaju.com` subdomain) | ₹0 (subdomain) or ₹800/yr (full) | You already own `cosmic-id` brand |
| `koreansaju.in` | ₹600/yr | Clear, India-focused |
| `getmyreading.com` | ₹800/yr | Action-oriented |
| `yourname.saju.com` | varies | Personal brand |

For your first 30 customers, **a subdomain is fine**. You can always upgrade to a full domain later.

#### Step 2: Sign up for Carrd (₹750, 5 min)

- Go to carrd.co → Pro plan ($9/yr ≈ ₹750)
- Connect your custom domain (CNAME setup, Carrd walks you through it)
- Free SSL automatically enabled

#### Step 3: Build the page (3 hours)

Use the **"Landing"** template. Customize with the 4 sections above:
- Upload your photo (warm, real, not stock)
- Paste the hero copy
- Add the 9 sections list
- Embed the sample chart screenshot
- Add 3 testimonials (start with your 5 pilot readings)
- Add the buy button linking to Razorpay Payment Link

#### Step 4: Create Razorpay Payment Link (10 min)

In Razorpay dashboard:
- Create Payment Link for **₹1,499**
- Title: "Korean Saju Reading by [Your Name]"
- Description: "12-page PDF reading delivered within 48 hours"
- After successful payment: redirect to `https://yourdomain.com/thank-you`
- Save the link URL — this is what the buy button points to

#### Step 5: Create the "Thank You" page (15 min)

A second Carrd page at `/thank-you`:

```
Thank you 🙏

Your payment is confirmed.

To begin your Reading, please fill this 2-minute form:

[Link to Google Form: name, DOB, time, location, gender, email]

You'll receive your 12-page PDF within 24-48 hours.

If you have any questions, email readings@yourdomain.com.
```

#### Step 6: Create the Google Form intake (15 min)

Already covered in §5 of this doc. Fields:
- Full name
- Date of birth (DD/MM/YYYY)
- Birth time (HH:MM)
- Birth city
- Gender
- Email address
- Relationship status (optional)
- "What's your main question for the Reading?" (text area)

Form auto-saves to Google Sheets. You get notification on submit.

#### Step 7: Update Instagram bio (2 min)

Replace the wa.me link with `https://yourdomain.com`:

```
🌙 Korean Saju (사주) Readings
📜 Classical tradition · 경락고요 · 적천수
✨ Get your Reading → link below
```

Add the domain URL to the bio (use Linktree if you need a second link).

### The full customer journey

```
Customer sees your Reel
        │
        ▼
Clicks bio link → opens cosmicsaju.com/saju
        │
        ▼
Reads hero, scrolls to sample chart
        │
        ▼
Sees 3 testimonials
        │
        ▼
Clicks "Get your Reading · ₹1,499"
        │
        ▼
Razorpay opens in new tab
        │
        ▼
Pays via UPI / Card / Net Banking
        │
        ▼
Razorpay redirects to your /thank-you page
        │
        ▼
Customer fills Google Form (2 min)
        │
        ▼
You get email: "Payment received + form filled"
        │
        ▼
You run engine commands (1 min)
        │
        ▼
You personalize (15-20 min)
        │
        ▼
You email PDF
        │
        ▼
You ask for testimonial (optional)
```

**Your time per customer: ~20 min.** Down from 25–30 min with WhatsApp because:
- No back-and-forth intake (form is pre-filled)
- No payment link to generate (link is static)
- No "are you ready to pay?" follow-ups

### When this beats each alternative

**Landing page beats Instagram DM when:**
- Customer came from a Reel (warm traffic, ready to buy)
- Customer is 28+ (prefers paper trail, doesn't want to DM)
- You're not online 24/7 (DM requires your reply, page doesn't)
- Customer wants to think before buying (page sits in browser tab, DM disappears)
- Customer is from Google search (SEO over time)

**Landing page beats WhatsApp when:**
- You don't want to install WhatsApp Business
- You don't want a second device
- Customer is a stranger (WhatsApp feels invasive for cold contact)
- You want SEO (Google ranks pages, never WhatsApp)
- You want to look professional (page > chat for ₹1,500 purchase)

**When WhatsApp or Instagram DM still wins:**
- Customer insists on WhatsApp (some won't convert without it)
- Customer wants instant Q&A before paying
- You're doing cold outreach (but you shouldn't be)
- Customer is 35+ Indian and WhatsApp-native

**Realistic loss rate:** 20–40% of leads may not convert because they expected WhatsApp. Build that into your conversion math. If you expect 50 Reel viewers clicking your bio, plan for 10–17 conversions, not 17–25.

### What about WhatsApp as a *follow-up* channel?

You can add WhatsApp Business later, **but as a customer-success channel, not the intake channel:**

- Customer pays via landing page → Razorpay → form
- They receive PDF via email
- They have questions → email reply (your dedicated Gmail)
- For high-LTV customers (Full Map at ₹3,499) → offer a 15-min voice call (dedicated SIM, optional)
- For the 10–20% who really want WhatsApp → add a WhatsApp Business number later

This way WhatsApp is a **value-add**, not a requirement. Most customers won't need it.

### Cost summary

| Component | Cost |
|---|---|
| Domain (`cosmicsaju.com` subdomain or `koreansaju.in`) | ₹0–800/yr |
| Carrd Pro plan | ₹750/yr |
| Razorpay (per transaction only) | 2% per sale |
| **Total Year 1** | **~₹1,500 + 2% per sale** |

Compare to:
- WhatsApp Business (dedicated SIM): ₹150 one-time + ₹149/mo = ₹1,938/yr (similar cost, but uses your time)
- Full architecture (Phase 5 web app): ₹45k/yr + 12 weeks of your time

**Carrd wins on cost AND on shipping speed.**

### Decision matrix: which path is right for you?

| Your situation | Recommended path |
|---|---|
| You want to ship today, willing to buy domain | **Landing page (Section 16)** ⭐ |
| You don't want to buy anything, willing to install apps | WhatsApp Business (Section 15) |
| You want zero setup, willing to lose 30% of leads | Instagram DM + Email (Section 16 alt) |
| You want email-only, targeting professionals/NRIs | Email-only (Section 16 alt) |
| You're targeting international/Telegram users | Telegram (Section 16 alt) |
| You want the eventual full web app | Defer to architecture Phase 5 |

**For a first-time solo founder willing to invest ₹1,500 and 4 hours → Landing page is the lowest-risk, highest-conversion path.**

---

## Sources

- Saju repo: [`CLAUDE.md`](../../CLAUDE.md), [`tools/saju_engine/`](../../tools/saju_engine/), [`tools/build-pdf.sh`](../../tools/build-pdf.sh)
- Architecture research: [`13-architecture-saju-web-cosmicid.md`](13-architecture-saju-web-cosmicid.md) — for the graduate path
- Market context: [`02-market-size-and-demand.md`](02-market-size-and-demand.md), [`04-feature-demand.md`](04-feature-demand.md), [`11-financial-model.md`](11-financial-model.md)
- Channel references:
  - Razorpay Payment Links: <https://razorpay.com/docs/payments/payment-links/>
  - Instagram Reels best practices: <https://business.instagram.com/reels>
  - WhatsApp Business: <https://business.whatsapp.com/>
  - WhatsApp Business API BSPs: <https://wati.io>, <https://aisensy.com>, <https://interakt.ai>
  - Indian virtual number services: <https://myoperator.com>, <https://exotel.com>
  - Carrd.co landing page builder: <https://carrd.co>
  - Framer.com landing page builder: <https://framer.com>
  - Cloudflare Registrar: <https://cloudflare.com/products/registrar>