/**
 * Stub for the `server-only` marker package under Vitest.
 *
 * The real package throws unless the bundler resolves the `react-server` export condition,
 * which Next does at build time but Vitest does not. Importing it here would make every test
 * that touches a server-only module fail for a reason that has nothing to do with the code.
 */
export {};
