# 07 · App Platform Decision — Web vs Android vs iOS vs Hybrid

**Date:** 2026-06-26
**Scope:** Which app surface (web app, Android, iOS, PWA, hybrid) is the right primary delivery vehicle for the Saju product, given the audience, the existing codebase, the cost of building, and the platform economics.

---

## 1. The question, sharply

Given the existing toolchain (Python engine + FastAPI self-service app + reportlab/Playwright PDF backends + intake form) and the target audience (India + Korean diaspora + global Hallyu-curious), **what is the right primary product surface for the next 12 months**?

The options on the table:

| Option | Description | Initial cost | Time to launch | Maintenance |
|---|---|---|---|---|
| **A. Web app only (responsive)** | Improve the existing FastAPI app into a full SaaS web app | ₹50k–1.5L | 4–8 weeks | Low |
| **B. PWA (Progressive Web App)** | Responsive web app + manifest + offline + push | ₹1–3L | 6–10 weeks | Low |
| **C. PWA + Capacitor wrap → Android Play Store** | Web app wrapped as Android app | ₹2–4L | 8–12 weeks | Low-medium |
| **D. Native Android (Kotlin/Java)** | Custom Android app | ₹5–15L | 12–20 weeks | Medium |
| **E. Native iOS (Swift)** | Custom iOS app | ₹8–20L | 12–20 weeks | Medium |
| **F. React Native + Expo (single codebase, both platforms)** | JS/TS cross-platform | ₹3–8L | 10–16 weeks | Medium |
| **G. Flutter** | Dart cross-platform | ₹3–8L | 12–18 weeks | Medium |

## 2. The audience signals

The audience (from `05-audience-demographics.md`) gives a clear answer about device preference:

| Market | Primary device | Notes |
|---|---|---|
| India Tier-1 | **Android (80%+)** | Android phone first, laptop second. iPhone is premium-segment. ~70–75% of Indian smartphone shipments are Android. |
| India Tier-2/3 | **Android (90%+)** | Budget Android dominates. |
| Korean diaspora US | iPhone (~60–65%) | Higher iPhone penetration than India. Korean-American income skews high. |
| Korean diaspora CA/AU/UK | iPhone (~55–65%) | Similar to US. |
| Global Hallyu-curious Gen Z | Mixed (Android 50/50) | Roughly even split; Android stronger in SEA, iPhone stronger in West. |
| Older Korean diaspora (50+) | iPhone + desktop | Less mobile-app engagement; email + desktop preferred. |

**Implication:** if we ship Android first, we capture India (the largest market by volume) and ~50% of Hallyu-curious Gen Z. If we ship iOS first, we capture Korean diaspora (the highest-LTV market). **The right answer is "both eventually, but Android first" — because India is the volume play and Korean diaspora is reachable on web + email even without an iOS app.**

## 3. Cost & ROI analysis (realistic, India-based)

### Option A: Web app only (responsive)

**Initial cost:** ₹50k–1.5L (existing FastAPI app + responsive CSS + payment integration + user accounts)

**Time to launch:** 4–8 weeks

**Strengths:**
- Reuses existing Python codebase (engine, PDF generation, intake).
- One codebase, accessible everywhere.
- SEO-friendly (organic Google traffic is huge for astrology content).
- No app store friction (no review, no 30% cut).
- Razorpay / Stripe work directly without IAP fees.

**Weaknesses:**
- No app store presence (no discovery via Play Store search).
- No push notifications (web push is limited, requires permission).
- Lower perceived "app-ness" — Indian users associate paid astrology with apps.

**Verdict:** The right **starting point**. Ship a polished web app first; the app store can come later.

### Option B: PWA

**Additional cost over web app:** ₹50k–2L (manifest, service worker, offline cache, install banner, push setup).

**Strengths:**
- Same as web app, but installable (adds to home screen).
- Push notifications work in modern browsers.
- Slightly better retention than pure web.

**Weaknesses:**
- Push notifications are limited vs. native (Safari support is patchy).
- App store discovery still absent.
- Play Store now accepts PWAs but with caveats.

**Verdict:** A small upgrade to Option A. Worth doing.

### Option C: PWA + Capacitor wrap → Android Play Store

**Additional cost over Option B:** ₹1–2L (Capacitor setup, signing key, store listing, Play Console account).

**Time to launch:** 8–12 weeks (after web app is solid).

**Strengths:**
- Real Android app in Play Store.
- Same codebase as web app — single engineering effort.
- Lower cost than native (60–80% cheaper per multiple sources).
- Play Store discoverability for India + global.

**Weaknesses:**
- Apple sometimes flags WebView apps as "just a wrapped website" and rejects from App Store.
- Performance is slightly worse than native.
- Plugin ecosystem covers ~80% of native APIs.

**Verdict:** **The recommended Year-1 Android strategy.** Cheap, fast, real Play Store presence.

### Option D: Native Android (Kotlin)

**Initial cost:** ₹5–15L (full native build).

**Time to launch:** 12–20 weeks.

**Strengths:**
- Best Android performance and UX.
- Best integration with Android-specific features.
- Most flexible for future native features.

**Weaknesses:**
- Expensive for solo founder.
- Long time to launch.
- India-specific Android dev talent is available but expensive for senior level.
- Most features in the Saju product don't need native performance.

**Verdict:** **Skip for Year 1.** Reconsider in Year 2 if PWA-Capacitor shows performance issues.

### Option E: Native iOS (Swift)

**Initial cost:** ₹8–20L.

**Time to launch:** 12–20 weeks.

**Strengths:**
- iPhone-only audience (Korean diaspora) feels premium.
- Apple ecosystem is friendlier to subscription apps.

**Weaknesses:**
- Most expensive platform.
- Smallest addressable audience (iPhone-skewing).
- Cannot reuse Python codebase.

**Verdict:** **Defer until Year 2 minimum.** The addressable Korean-diaspora iOS audience (~250k addressable) does not justify ₹8–20L Year 1 spend.

### Option F: React Native + Expo

**Initial cost:** ₹3–8L.

**Time to launch:** 10–16 weeks.

**Strengths:**
- Single codebase for iOS + Android.
- Expo managed workflow gets to TestFlight in 48 hours.
- Free OTA updates via Expo Updates.
- Largest India dev talent pool (~50k+) for hiring.
- RevenueCat integration is straightforward.
- Razorpay SDK has React Native wrappers.

**Weaknesses:**
- Native feel slightly lower than Swift/Kotlin.
- Performance ceiling below native.
- Slight learning curve for someone coming from web.
- App Store commission on subscriptions (15–30%) is unavoidable.

**Verdict:** **Best Year-2+ option if iOS becomes necessary.** For Year 1, Capacitor is cheaper.

### Option G: Flutter

**Initial cost:** ₹3–8L.

**Time to launch:** 12–18 weeks.

**Strengths:**
- Highest cross-platform consistency (pixel-perfect).
- Best animation performance.
- Strong typing via Dart.

**Weaknesses:**
- Smallest India dev pool (~15–20k).
- Higher dev replacement risk if founder hires and they leave.
- No OTA updates.
- Dart learning curve.

**Verdict:** **Skip.** The Saju product is content-heavy, not animation-heavy. Flutter's strengths don't apply here.

## 4. Recommended phased rollout

### Phase 1 — Months 1–4: Web app + PWA
**Ship:** A polished responsive web app at a custom domain. Convert the existing FastAPI self-service calculator (`tools/client_intake_app.py`) into a full SaaS product with:
- Landing page (SEO-optimized for "Korean Saju reading" keywords).
- Pricing page (three tiers + future Companion).
- Intake form (already exists at `tools/client_intake_app.html`).
- Payment via Razorpay (India) + Stripe (international).
- User accounts (email + passwordless magic link).
- Spark self-service automated end-to-end.
- Reading and Full Map: hand-delivered by the founder with 48–72 hour SLA.

**Cost:** ₹50k–1.5L. **Time:** 4–8 weeks.

### Phase 2 — Months 5–8: Compatibility + Companion scaffolding
**Ship:**
- Compatibility (궁합) product — paid add-on.
- Daily-content engine (free daily horoscope email + push via web push).
- "Year ahead" reminder email each December.
- Companion subscription infrastructure (accounts + billing).

**Cost:** ₹1.5–3L (mostly engineering time).

### Phase 3 — Months 9–12: Capacitor wrap → Android Play Store
**Ship:**
- Android app on Play Store, built by wrapping the PWA via Capacitor.
- Play Store listing optimized with screenshots, Korean + English description, ASO.
- App rating / review system.

**Cost:** ₹1–2L. **Time:** 4–6 weeks.

### Phase 4 — Year 2: iOS via Capacitor (or React Native)
**Decision point:** evaluate Android metrics. If Android has 10k+ installs and 4★+ rating, wrap for iOS via Capacitor. If Android is below threshold, defer iOS to Year 3.

**Cost:** ₹2–4L (additional). **Time:** 8–12 weeks.

## 5. Why NOT React Native or Flutter for Year 1

1. **Existing Python codebase.** The Saju engine is Python. Wrapping a web app via Capacitor reuses the Python backend as-is. Switching to React Native or Flutter means rewriting the entire frontend in a new stack.
2. **Solo founder economics.** A solo founder needs to ship in weeks, not months. Capacitor + web app is the fastest path to a real app store presence.
3. **The product is content-heavy, not animation-heavy.** Flutter's main advantage (animation, pixel-perfect consistency) doesn't apply. React Native's main advantage (native UI components) doesn't apply either — the Saju product is mostly text + chart + table.
4. **India dev pool is largest for React Native** (50k+) but the founder is solo — they aren't hiring Year 1.

## 6. The app store commission question

Google Play and Apple App Store take **15–30%** of digital subscription revenue. This is the single biggest reason to launch as a web app first.

| Monetization | Web (Razorpay/Stripe) | Play Store | App Store |
|---|---|---|---|
| One-time report (Spark ₹499) | **2% fee** | 15% fee on IAP, 0% on web-purchased subscription | 15% fee on IAP, 0% on web-purchased subscription |
| Reading / Full Map one-time | **2% fee** | 15% fee on IAP | 15% fee on IAP |
| Subscription (Companion ₹799/mo) | **2% fee** | 15% (year 1) → 30% (renewal, after first year) | 15% (year 1) → 30% (renewal) |

**Apple's "reader app" carve-out** allows web-purchased subscriptions to bypass IAP — but Apple has been tightening this and is hostile to "app that exists only to push users to web."

**Recommended approach:** sell on the web app for the first 12 months. The Android app on Play Store should sell the same products, with the 15% fee absorbed as cost-of-acquisition. Don't sell on iOS until the audience justifies the 30% commission.

## 7. Specific technology picks

| Layer | Pick | Why |
|---|---|---|
| **Frontend framework** | **Next.js 14+ (React, App Router)** | Already JS-friendly, SEO-friendly, PWA support built-in, Capacitor-wrap-ready. |
| **Styling** | **Tailwind CSS + shadcn/ui** | Modern, accessible, fast to iterate. |
| **Backend** | **FastAPI (existing Python)** | Already running. |
| **Auth** | **Clerk or Supabase Auth** | Magic-link + social login out of the box; minimal code. |
| **Payment (India)** | **Razorpay** | Indian market standard. UPI + cards + netbanking + wallets. |
| **Payment (international)** | **Stripe** | Standard global. |
| **Email** | **Resend or Postmark** | Transactional + marketing. |
| **Push notifications** | **Firebase Cloud Messaging (FCM)** | Free, works on web + Android. |
| **File storage** | **AWS S3 or Cloudflare R2** | For PDF storage. |
| **Hosting** | **Railway / Render / Fly.io** | Cheap, FastAPI-friendly. |
| **DB** | **PostgreSQL** | Standard. |
| **Capacitor plugins** | **@capacitor/push-notifications, @capacitor/in-app-browser, @capacitor/preferences** | For Android wrap. |
| **Analytics** | **Plausible or PostHog** | Privacy-friendly. |

## 8. The "should we build a native app from Day 1" trap

Many first-time founders believe they need a native app. The data says otherwise for content-heavy spiritual products:

- **Co-Star launched in 2017 as iOS only.** They didn't launch Android until 2020.
- **AstroTalk launched as Android-first in 2017.** They have an iOS app too, but Android is the dominant platform.
- **The Pattern, Sanctuary, Chani** all launched iOS-first; Android was added later.
- **AstroSage** is Android-first with a relatively weak iOS app.

**The pattern is clear:** no competitor launched both platforms on Day 1. All started with one platform, validated, then expanded.

## 9. The decision

**Recommendation: Web app + PWA first (Phase 1 + 2), then Capacitor-wrap for Android (Phase 3).**

- This minimizes Year 1 spend (₹50k–1.5L for web + ₹1–2L for Android wrap = ₹1.5–3.5L total).
- Reuses the existing Python engine and FastAPI self-service calculator.
- Captures the Indian Tier-1 audience (the largest market) on the web, and the rest of the audience via web + email.
- Delays iOS until Year 2+ when the audience justifies the spend.

**Do NOT:**
- Build a native iOS or Android app in Year 1.
- Use Flutter or React Native for Year 1.
- Use Capacitor without first having a solid PWA underneath.

## 10. Sources

- [Raft Labs: How to Build an Astrology App](https://www.raftlabs.com/blog/how-to-build-astrology-app)
- [The Debuggers: Flutter vs React Native vs Capacitor 2026](https://thedebuggersitsolutions.com/blog/cross-platform-app-2026-flutter-react-native-capacitor)
- [Bret Cameron: React Native vs Capacitor](https://levelup.gitconnected.com/react-native-vs-capacitor-a52aa9778e3b)
- [VibeReference: Mobile App Frameworks](https://www.vibereference.com/frontend/mobile-app-frameworks)
- [Ravi Rai: Flutter vs React Native India 2026](https://www.buildbyravirai.com/blog/flutter-vs-react-native-indian-startups-2026/)
- [NextNative: Capacitor vs React Native 2025](https://nextnative.dev/blog/capacitor-vs-react-native)
- [CB Insights: Co-Star financials](https://www.cbinsights.com/company/co-star-astrology-society/financials)
- [Rev.now: Co-Star revenue](https://rev.now/app/ios/co-star-personalized-astrology-82561/)
- [Indian Express: Gen Z + astrology apps](https://preprod.indianexpress.com/article/lifestyle/why-gen-z-is-turning-to-astrology-apps-to-find-solutions-to-life-problems-10031516/)
- Existing project: [tools/client_intake_app.py](../../tools/client_intake_app.py)
- Existing project: [pyproject.toml](../../pyproject.toml)