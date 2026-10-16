import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * UI primitives. Deliberately dependency-light (no Radix here) and usable from both Server and
 * Client Components — none of these use hooks or browser APIs.
 *
 * Rules: semantic tokens only, never a raw hex; ≥44px touch targets; focus visible everywhere.
 */

// ─────────────────────────────── Button ───────────────────────────────

export type ButtonVariant = "primary" | "secondary" | "outline" | "ghost" | "danger";
export type ButtonSize = "sm" | "md" | "lg";

const VARIANT: Record<ButtonVariant, string> = {
  primary:
    "bg-primary text-primary-foreground hover:brightness-110 active:brightness-95 border border-transparent font-semibold",
  secondary:
    "bg-muted text-foreground hover:bg-muted/70 border border-border",
  outline:
    "bg-transparent text-foreground hover:bg-muted/60 border border-border",
  ghost: "bg-transparent text-muted-foreground hover:text-foreground hover:bg-muted/50 border border-transparent",
  danger:
    "bg-destructive text-white hover:brightness-110 border border-transparent font-semibold",
};

const SIZE: Record<ButtonSize, string> = {
  sm: "h-9 px-3 text-sm rounded-md",
  md: "h-11 px-4 text-sm rounded-md",
  lg: "h-12 px-6 text-base rounded-lg",
};

export function buttonClasses(variant: ButtonVariant = "primary", size: ButtonSize = "md", extra?: string) {
  return cn(
    "inline-flex items-center justify-center gap-2 whitespace-nowrap transition-colors disabled:opacity-50 disabled:pointer-events-none",
    VARIANT[variant],
    SIZE[size],
    extra,
  );
}

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { className, variant = "primary", size = "md", loading, children, disabled, ...props },
  ref,
) {
  return (
    <button
      ref={ref}
      className={buttonClasses(variant, size, className)}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...props}
    >
      {loading ? <Spinner className="h-4 w-4" /> : null}
      {children}
    </button>
  );
});

export function Spinner({ className }: { className?: string }) {
  return (
    <span
      className={cn("inline-block animate-spin rounded-full border-2 border-current border-t-transparent", className)}
      aria-hidden
    />
  );
}

// ─────────────────────────────── Layout ───────────────────────────────

export function Card({ className, children, ...rest }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("card-surface", className)} {...rest}>
      {children}
    </div>
  );
}

export function CardHeader({ className, children }: { className?: string; children: React.ReactNode }) {
  return <div className={cn("px-5 py-4 border-b border-border", className)}>{children}</div>;
}

export function CardTitle({ className, children }: { className?: string; children: React.ReactNode }) {
  return <h3 className={cn("font-display text-xl leading-tight", className)}>{children}</h3>;
}

export function CardContent({ className, children }: { className?: string; children: React.ReactNode }) {
  return <div className={cn("px-5 py-4", className)}>{children}</div>;
}

export function CardFooter({ className, children }: { className?: string; children: React.ReactNode }) {
  return <div className={cn("px-5 py-4 border-t border-border", className)}>{children}</div>;
}

export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
}: {
  eyebrow?: string;
  title: string;
  description?: React.ReactNode;
  actions?: React.ReactNode;
}) {
  return (
    <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between pb-6 border-b border-border">
      <div className="space-y-1.5">
        {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
        <h1 className="h2">{title}</h1>
        {description ? <p className="lede max-w-2xl text-base">{description}</p> : null}
      </div>
      {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
    </header>
  );
}

export function SectionHeading({
  eyebrow,
  title,
  description,
  align = "left",
}: {
  eyebrow?: string;
  title: React.ReactNode;
  description?: React.ReactNode;
  align?: "left" | "center";
}) {
  return (
    <div className={cn("space-y-3", align === "center" && "text-center mx-auto max-w-3xl")}>
      {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
      <h2 className="h2">{title}</h2>
      {description ? <p className="lede">{description}</p> : null}
      <div className={cn("el-rule max-w-24", align === "center" && "mx-auto")} />
    </div>
  );
}

// ─────────────────────────────── Badge ───────────────────────────────

export type BadgeTone = "neutral" | "primary" | "success" | "warning" | "danger" | "muted";

const BADGE_TONE: Record<BadgeTone, string> = {
  neutral: "border-border text-foreground",
  primary: "border-primary/50 text-primary",
  success: "border-success/50 text-success",
  warning: "border-warning/50 text-warning",
  danger: "border-destructive/50 text-destructive",
  muted: "border-border text-muted-foreground",
};

export function Badge({
  tone = "neutral",
  className,
  children,
}: {
  tone?: BadgeTone;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium",
        BADGE_TONE[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}

// ─────────────────────────────── Alert ───────────────────────────────

export function Alert({
  tone = "neutral",
  title,
  children,
  className,
}: {
  tone?: "neutral" | "success" | "warning" | "danger" | "primary";
  title?: string;
  children?: React.ReactNode;
  className?: string;
}) {
  const tones: Record<string, string> = {
    neutral: "border-border bg-muted/40",
    primary: "border-primary/40 bg-primary/5",
    success: "border-success/40 bg-success/5",
    warning: "border-warning/40 bg-warning/5",
    danger: "border-destructive/40 bg-destructive/5",
  };
  return (
    <div role="status" className={cn("rounded-lg border px-4 py-3 text-sm", tones[tone], className)}>
      {title ? <p className="font-medium">{title}</p> : null}
      {children ? <div className={cn(title && "mt-1", "text-muted-foreground")}>{children}</div> : null}
    </div>
  );
}

// ─────────────────────────────── Empty state ───────────────────────────────

export function EmptyState({
  title,
  description,
  action,
  icon,
}: {
  title: string;
  description?: React.ReactNode;
  action?: React.ReactNode;
  icon?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-border px-6 py-12 text-center">
      {icon ? <div className="text-muted-foreground">{icon}</div> : null}
      <h3 className="font-display text-lg">{title}</h3>
      {description ? <p className="max-w-md text-sm text-muted-foreground">{description}</p> : null}
      {action ? <div className="pt-1">{action}</div> : null}
    </div>
  );
}

// ─────────────────────────────── Form fields ───────────────────────────────

export function Field({
  label,
  hint,
  error,
  htmlFor,
  children,
  optional,
}: {
  label: string;
  hint?: React.ReactNode;
  error?: string | null;
  htmlFor?: string;
  children: React.ReactNode;
  optional?: boolean;
}) {
  return (
    <div className="space-y-1.5">
      <label htmlFor={htmlFor} className="flex items-baseline gap-2 text-sm font-medium">
        {label}
        {optional ? <span className="text-xs font-normal text-muted-foreground">optional</span> : null}
      </label>
      {children}
      {error ? (
        <p className="text-xs text-destructive">{error}</p>
      ) : hint ? (
        <p className="text-xs text-muted-foreground">{hint}</p>
      ) : null}
    </div>
  );
}

const controlBase =
  "w-full rounded-md border border-input bg-surface px-3 py-2.5 text-sm text-foreground placeholder:text-muted-foreground/70 focus:border-ring focus:outline-none disabled:opacity-50";

export const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  function Input({ className, ...props }, ref) {
    return <input ref={ref} className={cn(controlBase, "h-11", className)} {...props} />;
  },
);

export const Textarea = React.forwardRef<HTMLTextAreaElement, React.TextareaHTMLAttributes<HTMLTextAreaElement>>(
  function Textarea({ className, ...props }, ref) {
    return <textarea ref={ref} className={cn(controlBase, "min-h-28 resize-y", className)} {...props} />;
  },
);

export const Select = React.forwardRef<HTMLSelectElement, React.SelectHTMLAttributes<HTMLSelectElement>>(
  function Select({ className, children, ...props }, ref) {
    return (
      <select ref={ref} className={cn(controlBase, "h-11 appearance-none pr-8", className)} {...props}>
        {children}
      </select>
    );
  },
);

// ─────────────────────────────── Data display ───────────────────────────────

export function Stat({
  label,
  value,
  hint,
  tone,
}: {
  label: string;
  value: React.ReactNode;
  hint?: React.ReactNode;
  tone?: "default" | "warning" | "danger" | "success";
}) {
  const toneClass =
    tone === "warning"
      ? "text-warning"
      : tone === "danger"
        ? "text-destructive"
        : tone === "success"
          ? "text-success"
          : "";
  return (
    <div className="card-surface px-4 py-3.5">
      <p className="eyebrow">{label}</p>
      <p className={cn("mt-1 font-display text-2xl leading-none", toneClass)}>{value}</p>
      {hint ? <p className="mt-1 text-xs text-muted-foreground">{hint}</p> : null}
    </div>
  );
}

export function KeyValue({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-4 py-2 border-b border-border last:border-0">
      <dt className="text-sm text-muted-foreground">{label}</dt>
      <dd className="text-right text-sm font-medium">{value}</dd>
    </div>
  );
}

export function Steps({ steps, current }: { steps: string[]; current: number }) {  return (
    <ol className="flex flex-wrap items-center gap-x-3 gap-y-1.5 text-xs" aria-label="Progress">
      {steps.map((s, i) => {
        const done = i < current;
        const active = i === current;
        return (
          <li key={s} className="flex items-center gap-2">
            <span
              className={cn(
                "grid h-5 w-5 place-items-center rounded-full border text-[10px] font-semibold",
                done && "border-success text-success",
                active && "border-primary text-primary",
                !done && !active && "border-border text-muted-foreground",
              )}
              aria-current={active ? "step" : undefined}
            >
              {done ? "✓" : i + 1}
            </span>
            <span className={cn(active ? "text-foreground" : "text-muted-foreground")}>{s}</span>
            {i < steps.length - 1 ? <span className="text-border" aria-hidden>·</span> : null}
          </li>
        );
      })}
    </ol>
  );
}

// ─────────────────────────────── Status helpers ───────────────────────────────

/** Order status → badge tone. Kept next to Badge so the vocabulary stays in one place. */
export function badgeToneForOrder(status: string): BadgeTone {
  switch (status) {
    case "PAID":
      return "success";
    case "AWAITING_PAYMENT":
      return "warning";
    case "REFUNDED":
    case "CANCELLED":
      return "muted";
    default:
      return "neutral";
  }
}
