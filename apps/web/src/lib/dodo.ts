import type { Order } from "@prisma/client";
import { ApiError } from "./api";
import { productIdForOrder } from "./tiers";

/**
 * Dodo Payments — checkout sessions.
 *
 * Dodo is the merchant of record, so we never see card data and **the webhook is the only source of
 * truth for "paid"** — the browser redirect can be missed if the customer closes the tab, and Dodo's
 * own guidance is to fulfil on `payment.succeeded`, never on the redirect.
 *
 * API: POST {base}/checkouts with `product_cart`, `customer`, `metadata`, `return_url`.
 * Docs: docs.dodopayments.com/api-reference/checkout-sessions/create
 */

function apiKey(): string {
  const key = process.env.DODO_PAYMENTS_API_KEY?.trim();
  if (!key) throw ApiError.unavailable("Payments are not configured", "PAYMENTS_UNAVAILABLE");
  return key;
}

/** test_mode → test.dodopayments.com, live_mode → live.dodopayments.com. Defaults to test. */
export function dodoBaseUrl(): string {
  const env = (process.env.DODO_PAYMENTS_ENVIRONMENT ?? "test_mode").trim().toLowerCase();
  return env === "live_mode" ? "https://live.dodopayments.com" : "https://test.dodopayments.com";
}

export function isDodoLiveMode(): boolean {
  return dodoBaseUrl().includes("live.");
}

export function isDodoConfigured(): boolean {
  return Boolean(process.env.DODO_PAYMENTS_API_KEY?.trim());
}

export function appUrl(): string {
  return (process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000").replace(/\/+$/, "");
}

interface CreateSessionResponse {
  session_id?: string;
  checkout_url?: string | null;
}

interface DodoError {
  message?: string;
  error?: { message?: string };
}

/**
 * Create a hosted checkout session and return its URL.
 *
 * `metadata.order_id` is how the webhook finds our order again — without it a payment cannot be
 * matched to a purchase. `return_url` is convenience only; fulfilment never depends on it.
 */
export async function createCheckout(
  order: Pick<Order, "id" | "userId" | "tier" | "kind" | "priceCents" | "currency">,
  email: string,
  customerName?: string,
): Promise<{ url: string; sessionId: string }> {
  // `order.tier` holds the ENGINE tier; 'deep' is ambiguous without the kind.
  const productId = productIdForOrder(order.kind, order.tier);

  if (!productId) {
    throw ApiError.unavailable(
      `No Dodo product is configured for "${order.kind}/${order.tier}". Set the DODO_PRODUCT_* environment variable.`,
      "PRODUCT_NOT_CONFIGURED",
    );
  }

  const body = {
    product_cart: [{ product_id: productId, quantity: 1 }],
    customer: { email, ...(customerName ? { name: customerName } : {}) },
    // Carried through to the payment object and the webhook payload.
    metadata: { order_id: order.id, user_id: order.userId, tier: order.tier, kind: order.kind },
    return_url: `${appUrl()}/dashboard/orders?paid=1`,
    cancel_url: `${appUrl()}/reports/new`,
    feature_flags: {
      allow_discount_code: true,
      allow_customer_editing_email: false,
      redirect_immediately: true,
    },
    customization: {
      theme: "dark" as const,
      show_order_details: true,
    },
  };

  const res = await fetch(`${dodoBaseUrl()}/checkouts`, {
    method: "POST",
    headers: {
      authorization: `Bearer ${apiKey()}`,
      "content-type": "application/json",
    },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(20_000),
  });

  const json = (await res.json().catch(() => ({}))) as CreateSessionResponse & DodoError;

  if (!res.ok || !json?.checkout_url || !json?.session_id) {
    // Never forward the provider's raw error text to a client.
    const detail = json?.error?.message ?? json?.message ?? `HTTP ${res.status}`;
    console.error("dodo checkout failed", res.status);
    throw ApiError.unavailable(
      `Could not start checkout (${detail}). Nothing has been charged.`,
      "CHECKOUT_FAILED",
    );
  }

  return { url: json.checkout_url, sessionId: json.session_id };
}

/** Order statuses Dodo can report on a one-time payment. */
export const DODO_PAYMENT_EVENTS = {
  succeeded: "payment.succeeded",
  failed: "payment.failed",
  processing: "payment.processing",
  cancelled: "payment.cancelled",
  refundSucceeded: "refund.succeeded",
  refundFailed: "refund.failed",
} as const;
