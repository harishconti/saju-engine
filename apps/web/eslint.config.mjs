import nextCoreWebVitals from "eslint-config-next/core-web-vitals";
import nextTypescript from "eslint-config-next/typescript";

const eslintConfig = [
  ...nextCoreWebVitals,
  ...nextTypescript,
  {
    rules: {
      "@typescript-eslint/no-explicit-any": "off",
      "@typescript-eslint/no-unused-vars": "off",
      "@typescript-eslint/no-non-null-assertion": "off",
      "react/no-unescaped-entities": "off",
      "react-hooks/exhaustive-deps": "off",
      // Server Components legitimately read request-scoped time (e.g. "age of the oldest item in
      // the review queue"). The rule cannot tell RSC render from a client render.
      "react-hooks/purity": "off",
      // Fonts are loaded with a <link> in the App Router root layout on purpose: next/font/google
      // fetches at BUILD time, which would make `next build` depend on network reachability.
      "@next/next/no-page-custom-font": "off",
      "@next/next/no-img-element": "off",
      "no-empty": "off",
      "prefer-const": "off",
    },
  },
  {
    ignores: ["node_modules/**", ".next/**", "out/**", "build/**", "next-env.d.ts"],
  },
];

export default eslintConfig;
