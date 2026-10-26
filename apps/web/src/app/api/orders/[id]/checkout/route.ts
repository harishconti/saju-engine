import { ApiError, handle, json } from "@/lib/api";
import { requireUser } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { rateLimit, WINDOW } from "@/lib/ratelimit";
import { requireActiveServiceConsent } from "@/lib/consent";
import { createCheckout, isDodoConfigured } from "@/lib/dodo";

export const dynamic = "force-dynamic";

type Ctx = { params: Promise<{ id: string }> };

/** Re-issue a hosted checkout for an unpaid order (e.g. the user abandoned the first attempt). */
export const POST = handle(async (_req, ctx: Ctx) => {
  const user = await requireUser();
  const { id } = await ctx.params;
  await rateLimit(`checkout:${user.id}`, 20, WINDOW.hour);

  const order = await prisma.order.findFirst({ where: { id, userId: user.id } });
  if (!order) throw ApiError.notFound("Order not found");

  if (order.status === "PAID") {
    throw ApiError.conflict("This order is already paid", "ALREADY_PAID");
  }
  if (order.status === "REFUNDED" || order.status === "CANCELLED") {
    throw ApiError.conflict("This order is closed", "ORDER_CLOSED");
  }

  // Owner decision D11 (2026-10-26): withdrawal gates payment for an order that has not been paid
  // yet — taking payment now would start processing after the withdrawal. A PAID order was answered
  // above and never reaches this guard; in-flight paid work is deliberately not gated
  // (`lib/fulfilment.ts::runDispatchTick`). Placed after `rateLimit` and before any write.
  await requireActiveServiceConsent(user.id);

  if (order.priceCents === 0) {
    return json({ checkoutUrl: null, message: "This order is free and needs no payment." });
  }
  if (!isDodoConfigured()) {
    throw ApiError.unavailable("Payments are not configured yet", "PAYMENTS_UNAVAILABLE");
  }

  const checkout = await createCheckout(
    { id: order.id, userId: user.id, tier: order.tier, kind: order.kind, priceCents: order.priceCents, currency: "USD" },
    user.email,
  );

  await prisma.order.update({
    where: { id: order.id },
    data: { provider: "dodo", providerCheckoutId: checkout.sessionId },
  });

  return json({ checkoutUrl: checkout.url });
});
