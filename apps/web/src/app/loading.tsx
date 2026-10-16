import { Spinner } from "@/components/ui";

export default function Loading() {
  return (
    <div className="grid min-h-[50vh] place-items-center">
      <div className="flex flex-col items-center gap-3 text-muted-foreground">
        <Spinner className="h-5 w-5" />
        <p className="eyebrow">Loading</p>
      </div>
    </div>
  );
}
