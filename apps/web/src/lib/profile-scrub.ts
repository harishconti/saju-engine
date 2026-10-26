import { Prisma } from "@prisma/client";

/**
 * What is left of a profile once the person behind it is gone.
 *
 * AU-27 (2026-10-26 audit): two paths must destroy birth data — account erasure (Task 4) and the
 * soft delete of a single profile — and they had better destroy *exactly* the same fields. Keeping
 * one definition means a field added to the model can never be scrubbed on one path and leak on the
 * other.
 *
 * `birthDate`, `birthTime`, `city` and `country` are NOT NULL in the schema, so they get
 * placeholders rather than null. `gender` is also required, but is deliberately left as-is: it is
 * an enum with no neutral member, the row is anonymised and unreachable after `deletedAt`, and
 * rewriting it would invent a fact about a person whose data we are destroying.
 *
 * Typed against `ProfileUpdateManyMutationInput`; its scalars are also valid for
 * `ProfileUpdateInput`, so a single-profile update can spread it unchanged.
 */
export const SCRUBBED_PROFILE = {
  label: "Deleted profile",
  fullName: "Deleted profile",
  birthDate: new Date(0),
  birthTime: "00:00",
  timezone: null,
  utcOffset: null,
  city: "Deleted",
  country: "Deleted",
  latitude: null,
  longitude: null,
  timeKnown: false,
  chartJson: Prisma.DbNull,
  chartComputedAt: null,
} satisfies Prisma.ProfileUpdateManyMutationInput;
