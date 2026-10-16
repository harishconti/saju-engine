import Link from "next/link";
import { buttonClasses } from "@/components/ui";
import { ElementalRule, SealMark } from "@/components/viz";

export default function NotFound() {
  return (
    <main className="grid-noise grid min-h-screen place-items-center px-4">
      <div className="flex max-w-md flex-col items-center gap-5 text-center">
        <SealMark char="無" />
        <p className="eyebrow">404</p>
        <h1 className="h2">This page doesn&apos;t exist</h1>
        <p className="text-sm text-muted-foreground">
          The link may be old, or the report may have been deleted. Nothing is broken on your side.
        </p>
        <ElementalRule className="max-w-24" />
        <div className="flex flex-wrap justify-center gap-3">
          <Link href="/" className={buttonClasses("primary", "md")}>
            Back to the site
          </Link>
          <Link href="/dashboard" className={buttonClasses("outline", "md")}>
            Go to your dashboard
          </Link>
        </div>
      </div>
    </main>
  );
}
