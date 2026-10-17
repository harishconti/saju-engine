import { ApiError, handle, json, parseJson } from "@/lib/api";
import { requireUser } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { rateLimit, WINDOW } from "@/lib/ratelimit";
import { writeAudit } from "@/lib/audit";
import { withIdempotency } from "@/lib/idempotency";
import { getTierById } from "@/lib/tiers";
import { createCheckout, isDodoConfigured } from "@/lib/dodo";
import { orderSchema } from "@/lib/validation/schemas";

export const dynamic = "force-dynamic";

/** The caller's orders. */
export const GET = handle(async () => {
  const user = await requireUser();
  const orders = await prisma.order.findMany({
    where: { userId: user.id },
    orderBy: { createdAt: "desc" },
    include: { reports: { orderBy: { version: "desc" }, select: { id: true, status: true, version: true } } },
  });
  return json({ orders });
});

/**
 * Create an order.
 *
 * Price is resolved SERVER-SIDE from the tier map; any price the client sent is discarded.
 * Compat tiers require two distinct profiles, both owned by the caller.
 */
export const POST = handle(async (req) => {
  const user = await requireUser();
  await rateLimit(`order:${user.id}`, 10, WINDOW.hour);

  const input = await parseJson(req, orderSchema);
  const idempotencyKey = req.headers.get("idempotency-key") ?? input.idempotencyKey ?? null;

  const tier = getTierById(input.tier);
  if (!tier) throw ApiError.unprocessable(`Unknown reading type "${input.tier}"`, "UNKNOWN_TIER");

  // The free snapshot has a dedicated synchronous path (`POST /api/sample`) that needs no
  // account, no Order and no job. Ordering it here would duplicate that machinery and put a
  // free report through the paid flow.
  if (tier.priceCents === 0) {
    // 422, like the other tier-validation failures (UNKNOWN_TIER, TIER_PROFILE_MISMATCH).
    throw ApiError.unprocessable(
      "The free snapshot is requested from /sample and needs no account.",
      "TIER_NOT_ORDERABLE",
    );
  }

  const compat = tier.kind === "COMPAT";
  if (compat && !input.profileBId) {
    throw ApiError.unprocessable("A compatibility reading needs two people", "TIER_PROFILE_MISMATCH");
  }
  if (compat && input.profileBId === input.profileAId) {
    throw ApiError.unprocessable("Pick two different people", "TIER_PROFILE_MISMATCH");
  }

  // Ownership check before anything is written.
  const profiles = await prisma.profile.findMany({
    where: { id: { in: [input.profileAId, ...(input.profileBId ? [input.profileBId] : [])] }, userId: user.id, deletedAt: null },
    select: { id: true },
  });
  const owned = new Set(profiles.map((p) => p.id));
  if (!owned.has(input.profileAId) || (input.profileBId && !owned.has(input.profileBId))) {
    throw ApiError.notFound("Profile not found");
  }

  const { data: order } = await withIdempotency(
    { userId: user.id, key: idempotencyKey, body: { tier: tier.id, a: input.profileAId, b: input.profileBId ?? null } },
    async (tx) => {
      const created = await tx.order.create({
        data: {
          userId: user.id,
          kind: tier.kind,
          tier: tier.engineTier, // stored as the ENGINE tier; `kind` disambiguates
          status: tier.priceCents === 0 ? "PAID" : "AWAITING_PAYMENT",
          priceCents: tier.priceCents,
          currency: tier.currency,
          profileAId: input.profileAId,
          profileBId: input.profileBId ?? null,
          idempotencyKey,
          ...(tier.priceCents === 0 ? { provider: "free", paidAt: new Date() } : {}),
        },
      });

      if (tier.priceCents === 0) {
        await tx.job.create({ data: { orderId: created.id, kind: "GENERATE", state: "QUEUED" } });
      }

      await writeAudit(tx, {
        entity: "order",
        entityId: created.id,
        action: "create",
        actorId: user.id,
        after: {
          tier: created.tier,
          kind: created.kind,
          priceCents: created.priceCents,
          // Recorded explicitly: the buyer affirmed 18+ at this moment, and `orderSchema` will not
          // accept an order without it. This row is the evidence (there is no separate record, as
          // the affirmation is not a reusable consent like ConsentRecord).
          adultConfirmed: true,
        },
      });

      return {
        id: created.id,
        kind: created.kind,
        tier: created.tier,
        status: created.status,
        priceCents: created.priceCents,
        currency: created.currency,
      };
    },
  );

  // Free tier: already queued.
  if (order.priceCents === 0) {
    return json({ order, checkoutUrl: null, queued: true }, 201);
  }

  if (order.status === "PAID") {
    return json({ order, checkoutUrl: null, queued: true }, 200);
  }

  if (!isDodoConfigured()) {
    return json(
      {
        order,
        checkoutUrl: null,
        message:
          "Your order is saved but payments are not configured yet, so nothing has been charged. We'll email you a payment link.",
      },
      201,
    );
  }

  const checkout = await createCheckout(
    { id: order.id, userId: user.id, tier: order.tier, kind: order.kind, priceCents: order.priceCents, currency: "USD" },
    user.email,
  );

  await prisma.order.update({
    where: { id: order.id },
    data: { provider: "dodo", providerCheckoutId: checkout.sessionId },
  });

  return json({ order, checkoutUrl: checkout.url }, 201);
});
