import { SiteFooter, SiteHeader } from "@/components/site";
import { SampleFlow } from "@/components/sample-flow";
import { getCurrentUser } from "@/lib/auth";
import { isEngineConfigured } from "@/lib/engine";

export const dynamic = "force-dynamic";
export const metadata = {
  title: "Free chart snapshot",
  description:
    "Get your Korean Saju four pillars, element balance, and Day Master free — no account needed.",
};

export default async function SamplePage() {
  const user = await getCurrentUser();

  return (
    <>
      <SiteHeader user={user} cta={false} />
      <main className="grid-noise">
        <div className="mx-auto max-w-3xl space-y-8 px-4 py-12 sm:px-6">
          <header className="space-y-3 text-center">
            <p className="eyebrow">Free · no account needed</p>
            <h1 className="h1 text-3xl sm:text-4xl">Your free chart snapshot</h1>
            <p className="lede">
              Give us the birth details and we&apos;ll derive your four pillars, element balance, and Day
              Master. One page, instantly, before you spend anything.
            </p>
          </header>

          <SampleFlow signedIn={Boolean(user)} engineReady={isEngineConfigured()} />
        </div>
      </main>
      <SiteFooter />
    </>
  );
}
