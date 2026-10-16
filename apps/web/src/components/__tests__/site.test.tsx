import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { SiteHeader } from "../site";

/**
 * The reported bug: after signing up, the landing page still invited you to sign in.
 *
 * It could not do anything else. `SiteHeader` hardcoded "Sign in", and `/` was statically prerendered,
 * so the HTML a signed-in visitor received was baked at build time and had no way to know. The header
 * now takes the session as a prop and every caller reads it; these tests pin the two variants so the
 * regression cannot come back.
 */
describe("SiteHeader", () => {
  it("invites a signed-out visitor to sign in", () => {
    render(<SiteHeader />);
    expect(screen.getByText("Sign in")).toBeTruthy();
    expect(screen.queryByText("Dashboard")).toBeNull();
  });

  it("offers the dashboard instead, once signed in", () => {
    render(<SiteHeader user={{ name: "Harish" }} />);
    expect(screen.queryByText("Sign in")).toBeNull();
    expect(screen.getByText("Dashboard")).toBeTruthy();
  });

  it("keeps the free snapshot reachable when signed in, as the secondary action", () => {
    render(<SiteHeader user={{ name: "Harish" }} />);
    const snapshot = screen.getByText("Free chart snapshot");
    expect(snapshot).toBeTruthy();
    // It must no longer be the *primary* (filled) button, which now belongs to the dashboard.
    expect(snapshot.className).not.toContain("bg-primary");
  });

  it("still hides the snapshot CTA where the page asks for no call to action", () => {
    render(<SiteHeader cta={false} />);
    expect(screen.queryByText("Free chart snapshot")).toBeNull();
  });

  it("treats a user with no name as signed in all the same", () => {
    render(<SiteHeader user={{}} />);
    expect(screen.getByText("Dashboard")).toBeTruthy();
    expect(screen.queryByText("Sign in")).toBeNull();
  });
});
