import { cn } from "@/lib/utils";

/**
 * In-house SVG visual system. Theme-aware (colors come from the 오방색 CSS tokens), responsive, and
 * prefers-reduced-motion-safe. No chart library, no client JS — these are pure components.
 */

export type ElementName = "Wood" | "Fire" | "Earth" | "Metal" | "Water";

export const ELEMENTS: ElementName[] = ["Wood", "Fire", "Earth", "Metal", "Water"];

export const ELEMENT_VAR: Record<ElementName, string> = {
  Wood: "var(--el-wood)",
  Fire: "var(--el-fire)",
  Earth: "var(--el-earth)",
  Metal: "var(--el-metal)",
  Water: "var(--el-water)",
};

export const ELEMENT_HANJA: Record<ElementName, string> = {
  Wood: "木",
  Fire: "火",
  Earth: "土",
  Metal: "金",
  Water: "水",
};

export type ElementCounts = Partial<Record<ElementName, number>>;

// ───────────────────────────── Four pillars ─────────────────────────────

export interface PillarCell {
  /** Hanja for the heavenly stem, e.g. 辛 */
  stem: string;
  /** Hanja for the earthly branch, e.g. 丑 */
  branch: string;
  /** "Year" | "Month" | "Day" | "Hour" */
  label: string;
}

/**
 * The four pillars (四柱). Mono typeface keeps the glyph columns aligned; the day pillar is marked
 * because it carries the Day Master.
 */
export function FourPillarsChart({
  pillars,
  className,
  animate = true,
}: {
  pillars: PillarCell[];
  className?: string;
  animate?: boolean;
}) {
  return (
    <div className={cn("grid grid-cols-4 gap-2 sm:gap-3", className)}>
      {pillars.map((p, i) => {
        const isDay = p.label.toLowerCase() === "day";
        return (
          <div
            key={`${p.label}-${i}`}
            className={cn(
              "relative flex flex-col items-center gap-2 rounded-lg border px-2 py-3 text-center",
              isDay ? "border-primary/60 bg-primary/5" : "border-border bg-muted/30",
              animate && "animate-stamp",
            )}
            style={animate ? { animationDelay: `${i * 70}ms` } : undefined}
          >
            <span className="eyebrow text-[10px]">{p.label}</span>
            <span className="pillar text-3xl leading-none sm:text-4xl">{p.stem}</span>
            <span className="h-px w-6 bg-border" aria-hidden />
            <span className="pillar text-3xl leading-none sm:text-4xl">{p.branch}</span>
            {isDay ? (
              <span className="absolute -bottom-2 rounded-full border border-primary/50 bg-background px-1.5 text-[9px] uppercase tracking-wider text-primary">
                day master
              </span>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}

// ───────────────────────────── Day Master ─────────────────────────────

export function DayMasterBadge({
  char,
  element,
  polarity,
  className,
}: {
  char: string;
  element?: ElementName | string | null;
  polarity?: string | null;
  className?: string;
}) {
  const color = element && element in ELEMENT_VAR ? ELEMENT_VAR[element as ElementName] : "var(--primary)";
  return (
    <div className={cn("flex items-center gap-3", className)}>
      <span
        className="grid h-14 w-14 shrink-0 place-items-center rounded-lg border text-2xl"
        style={{ borderColor: color, color }}
        aria-hidden
      >
        <span className="font-display">{char}</span>
      </span>
      <div className="min-w-0">
        <p className="eyebrow">Day Master</p>
        <p className="truncate font-display text-lg leading-tight">
          {char}
          {element ? ` ${element}` : ""}
          {polarity ? ` · ${polarity}` : ""}
        </p>
      </div>
    </div>
  );
}

// ───────────────────────────── Element balance ─────────────────────────────

export function ElementBalanceBars({ counts, className }: { counts: ElementCounts; className?: string }) {
  const total = ELEMENTS.reduce((sum, e) => sum + (counts[e] ?? 0), 0) || 1;
  return (
    <ul className={cn("space-y-2", className)}>
      {ELEMENTS.map((el) => {
        const value = counts[el] ?? 0;
        const pct = Math.round((value / total) * 100);
        return (
          <li key={el} className="flex items-center gap-3">
            <span className="flex w-24 shrink-0 items-center gap-1.5 text-xs">
              <span aria-hidden className="text-sm" style={{ color: ELEMENT_VAR[el] }}>
                {ELEMENT_HANJA[el]}
              </span>
              <span className="text-muted-foreground">{el}</span>
            </span>
            <span className="h-2 flex-1 overflow-hidden rounded-full bg-muted" role="img" aria-label={`${el}: ${pct}%`}>
              <span
                className="block h-full rounded-full"
                style={{ width: `${pct}%`, backgroundColor: ELEMENT_VAR[el] }}
              />
            </span>
            <span className="w-10 shrink-0 text-right font-mono text-xs tabular-nums text-muted-foreground">{pct}%</span>
          </li>
        );
      })}
    </ul>
  );
}

/**
 * Donut wheel of the five elements. Segments are stroke-dasharray on a circle so no path maths and
 * no JS are needed.
 */
export function ElementBalanceWheel({
  counts,
  size = 168,
  className,
}: {
  counts: ElementCounts;
  size?: number;
  className?: string;
}) {
  const stroke = 16;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const total = ELEMENTS.reduce((sum, e) => sum + (counts[e] ?? 0), 0);

  let offset = 0;
  const segments = ELEMENTS.map((el) => {
    const value = counts[el] ?? 0;
    const fraction = total > 0 ? value / total : 0;
    const length = fraction * c;
    const seg = { el, length, offset, value };
    offset += length;
    return seg;
  });

  return (
    <svg
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
      className={className}
      role="img"
      aria-label="Element balance wheel"
    >
      <circle
        cx={size / 2}
        cy={size / 2}
        r={r}
        fill="none"
        stroke="var(--muted)"
        strokeWidth={stroke}
      />
      {total > 0
        ? segments.map((s) => (
            <circle
              key={s.el}
              cx={size / 2}
              cy={size / 2}
              r={r}
              fill="none"
              stroke={ELEMENT_VAR[s.el]}
              strokeWidth={stroke}
              strokeDasharray={`${s.length} ${c - s.length}`}
              strokeDashoffset={-s.offset}
              transform={`rotate(-90 ${size / 2} ${size / 2})`}
            />
          ))
        : null}
      <text
        x="50%"
        y="47%"
        textAnchor="middle"
        dominantBaseline="middle"
        fill="var(--foreground)"
        fontSize={size * 0.16}
        fontFamily="var(--font-display)"
      >
        五行
      </text>
      <text
        x="50%"
        y="62%"
        textAnchor="middle"
        dominantBaseline="middle"
        fill="var(--muted-foreground)"
        fontSize={size * 0.073}
        fontFamily="var(--font-mono)"
        letterSpacing="0.14em"
      >
        ELEMENTS
      </text>
    </svg>
  );
}

// ───────────────────────────── Luck timeline ─────────────────────────────

export interface LuckPeriod {
  label: string;
  startAge: number;
  favorable?: boolean | null;
}

/** Major-luck (대운) sequence as a horizontal band. */
export function LuckTimeline({ periods, className }: { periods: LuckPeriod[]; className?: string }) {
  if (periods.length === 0) return null;
  return (
    <div className={cn("space-y-2", className)}>
      <div className="flex gap-1.5 overflow-x-auto pb-1">
        {periods.map((p) => (
          <div
            key={`${p.startAge}-${p.label}`}
            className={cn(
              "flex min-w-[64px] flex-col items-center gap-1 rounded-md border px-2 py-2",
              p.favorable === true && "border-success/50 bg-success/5",
              p.favorable === false && "border-destructive/40 bg-destructive/5",
              p.favorable == null && "border-border bg-muted/30",
            )}
            title={`From age ${p.startAge}${p.favorable == null ? "" : p.favorable ? " · favorable" : " · mixed"}`}
          >
            <span className="pillar text-lg leading-none">{p.label}</span>
            <span className="font-mono text-[10px] text-muted-foreground">age {p.startAge}</span>
          </div>
        ))}
      </div>
      <p className="text-xs text-muted-foreground">
        Major-luck periods. Green reads favorable for this chart; red warns of a harder decade — both are
        tendencies, not outcomes.
      </p>
    </div>
  );
}

// ───────────────────────────── Motifs ─────────────────────────────

export function KoreanWatermark({ char = "四柱" }: { char?: string }) {
  return (
    <span className="kr-watermark" aria-hidden>
      {char}
    </span>
  );
}

export function SealMark({ char = "印" }: { char?: string }) {
  return (
    <span className="seal-mark" aria-hidden>
      {char}
    </span>
  );
}

export function ElementalRule({ className }: { className?: string }) {
  return <div className={cn("el-rule", className)} aria-hidden />;
}

/** Compact element legend for report cards. */
export function ElementLegend({ counts }: { counts: ElementCounts }) {
  return (
    <ul className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
      {ELEMENTS.map((el) => (
        <li key={el} className="flex items-center gap-1.5">
          <span
            aria-hidden
            className="inline-block h-2 w-2 rounded-full"
            style={{ backgroundColor: ELEMENT_VAR[el] }}
          />
          {el} {counts[el] ?? 0}
        </li>
      ))}
    </ul>
  );
}
