"use client";

import { createAuthClient } from "@neondatabase/auth/next";

/**
 * Browser auth client.
 *
 * Takes no arguments on purpose: it talks to the same-origin proxy mounted at
 * `/api/auth/[...path]`, which forwards to Neon Auth. That keeps the browser on our own origin
 * (no CORS, no third-party cookies).
 */
export const authClient = createAuthClient();
