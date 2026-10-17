"use client";

import { useEffect, useSyncExternalStore } from "react";
import { isCityIndexLoaded, loadCityIndex, subscribeCityIndex } from "./cities";

/**
 * Whether the world place index has loaded, re-rendering the caller when it arrives.
 *
 * The index starts as the curated 156 entries, so the picker is usable on the first keystroke and stays
 * usable offline; this hook fetches the rest in the background and reports when the searchable set has
 * grown. Callers must include the returned flag in their `useMemo` dependencies — the search functions
 * read a module-level index, so nothing re-runs on its own.
 *
 * Mounting this is also what triggers the fetch, and it belongs on the two screens that *must* resolve a
 * birthplace: `/sample` and the profile form. Prefetching the field a visitor has to fill in is not
 * speculative work.
 *
 * A subscription rather than `useState` in an effect: the index is an external store, and reading it
 * through `useSyncExternalStore` is what keeps the first render (and the server render) consistent
 * instead of flashing a flag that changes immediately afterwards.
 */
export function useCityIndex(): boolean {
  const ready = useSyncExternalStore(
    subscribeCityIndex,
    isCityIndexLoaded,
    // Server snapshot: the curated table is all that exists off the client, and saying otherwise would
    // produce a hydration mismatch.
    () => false,
  );

  useEffect(() => {
    void loadCityIndex();
  }, []);

  return ready;
}
