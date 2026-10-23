import { defineConfig } from "vitest/config";
import path from "path";

const alias = {
  "@": path.resolve(import.meta.dirname, "./src"),
  // `import "server-only"` is resolved by Next itself at build time; under Vitest there is no
  // react-server condition, so the real package would throw on import. Point it at an empty
  // module — the guard still bites in the app build, where it matters.
  "server-only": path.resolve(import.meta.dirname, "./src/test/server-only-stub.ts"),
};

export default defineConfig({
  test: {
    projects: [
      {
        resolve: { alias },
        test: {
          name: "node",
          environment: "node",
          include: ["src/**/*.test.ts"],
        },
      },
      {
        resolve: { alias },
        test: {
          name: "browser",
          environment: "happy-dom",
          include: ["src/**/*.test.tsx"],
          setupFiles: ["./src/test-setup.ts"],
        },
      },
    ],
  },
});
