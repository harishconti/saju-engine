-- Owner decision D9 (2026-10-26): a durable "this account is still used" signal.
--
-- The 24-month inactivity sweep keyed activity on `Profile.updatedAt` and on referencing orders and
-- reports. That covers a customer who orders, but not one who signs in to re-read a report that
-- already exists: `mirrorUser` returns early for an unchanged account and no read route writes the
-- profile, so a regular visitor and a two-year-absent one looked identical. `lastSeenAt` is the
-- missing signal, written by `getCurrentUser` at most once every 24 hours.
--
-- Nullable on purpose: existing accounts have no history. The sweep treats
-- COALESCE(lastSeenAt, createdAt) as the activity date, so an account is measured from its creation
-- until its first authenticated request after this deploys.
--
-- Additive and nullable, so it is safe to apply BEFORE the code that writes it.
--
-- NOT APPLIED as part of this change — there is no database access in the change that adds it.
-- Applying it is a deploy step: `npx prisma migrate deploy` (over DIRECT_URL), after backup.
ALTER TABLE "User" ADD COLUMN "lastSeenAt" TIMESTAMP(3);

-- The "recently seen" side of the retention filter and any future activity query. The sweep's
-- COALESCE predicate cannot use an index for the null rows; those fall back to `createdAt`.
CREATE INDEX "User_lastSeenAt_idx" ON "User"("lastSeenAt");
