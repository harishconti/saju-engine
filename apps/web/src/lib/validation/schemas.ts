import { z } from "zod";
import { ROLES } from "@/lib/roles";

/**
 * Shared zod schemas. Enums are mirrored in three places on purpose: here, the Prisma schema, and
 * the DB CHECK constraint (docs/webapp/02-data-model.md).
 */

export const ELEMENTS = ["Wood", "Fire", "Earth", "Metal", "Water"] as const;
export const elementSchema = z.enum(ELEMENTS);

export const genderSchema = z.enum(["M", "F"]);

const dateString = z
  .string()
  .trim()
  .regex(/^\d{4}-\d{2}-\d{2}$/, "Use YYYY-MM-DD");

const timeString = z
  .string()
  .trim()
  .regex(/^([01]\d|2[0-3]):[0-5]\d$/, "Use HH:MM on a 24-hour clock");

/** Birth data. Shared by profile creation, the sample flow, and admin corrections. */
export const birthDataSchema = z.object({
  fullName: z.string().trim().min(1, "Please give a name").max(80),
  gender: genderSchema,
  birthDate: dateString,
  birthTime: timeString,
  timeKnown: z.boolean().optional().default(true),
  timezone: z.string().trim().max(64).nullable().optional(),
  city: z.string().trim().min(1, "Pick a birthplace").max(120),
  countryCode: z.string().trim().length(2).optional(),
  country: z.string().trim().max(80).optional(),
});

export const profileSchema = birthDataSchema.extend({
  label: z.string().trim().min(1, "Give this profile a label").max(40),
  isDefault: z.boolean().optional(),
});

export const profileUpdateSchema = profileSchema.partial();

export const sampleRequestSchema = birthDataSchema.extend({
  idempotencyKey: z.string().trim().min(8).max(100).optional(),
  turnstileToken: z.string().trim().max(4096).optional(),
});

export const orderSchema = z
  .object({
    tier: z.string().trim().min(1),
    profileAId: z.string().trim().min(1, "Choose who this reading is for"),
    profileBId: z.string().trim().min(1).nullable().optional(),
    idempotencyKey: z.string().trim().min(8).max(100).optional(),
    /**
     * The buyer affirms they are 18 or over. Required, and required to be `true`: an absent or
     * falsy field is a refusal, not a default. Enforced here rather than only in the form, so a
     * direct `POST /api/orders` cannot skip it.
     *
     * Why: paid readings cover relationship and health content, and the Hallyu-adjacent audience
     * this product reaches skews young — see docs/webapp/10-privacy-and-compliance.md §Minors.
     */
    adultConfirmed: z.boolean().refine((v) => v === true, {
      message: "Confirm you are 18 or over — paid readings cover relationship and health content",
    }),
  })
  .refine((v) => !(v.profileBId && v.profileBId === v.profileAId), {
    message: "A compatibility reading needs two different people",
    path: ["profileBId"],
  });

/** Confirms a browser-side audio upload. The key is re-derived server-side, never trusted. */
export const audioUploadCompleteSchema = z.object({
  key: z.string().trim().min(1).max(400),
});

export const consentSchema = z.object({
  policyVersion: z.string().trim().min(1).max(40),
  purposes: z.record(z.string(), z.boolean()),
});

export const deletionRequestSchema = z.object({
  reason: z.string().trim().max(500).optional(),
});

export const contactSchema = z.object({
  name: z.string().trim().min(1).max(80),
  email: z.string().trim().toLowerCase().pipe(z.email("That email doesn't look right")),
  message: z.string().trim().min(10, "Please add a little more detail").max(4000),
  honeypot: z.string().max(0).optional(),
});

// ── Admin ──

export const overrideSchema = z.object({
  favorableOverrideA: elementSchema.nullable(),
  favorableOverrideB: elementSchema.nullable().optional(),
});

export const rejectSchema = z.object({
  reason: z.string().trim().min(3, "Give a reason — the client will see it").max(500),
});

export const markPaidSchema = z.object({
  note: z.string().trim().max(200).optional(),
});

export const roleSchema = z.enum(ROLES);

export type BirthDataInput = z.infer<typeof birthDataSchema>;
export type ProfileInput = z.infer<typeof profileSchema>;
export type OrderInput = z.infer<typeof orderSchema>;
export type SampleRequestInput = z.infer<typeof sampleRequestSchema>;
