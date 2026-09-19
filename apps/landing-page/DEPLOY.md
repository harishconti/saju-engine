# Deploying Cosmic Saju Landing Page on Vercel

This Next.js 16 application is configured for deployment to Vercel from the `apps/landing-page` directory.

## Project settings

In the Vercel dashboard create/import the project and set the following:

| Setting | Value |
|---|---|
| Framework preset | Next.js |
| Root directory | `apps/landing-page` |
| Build command | `next build` |
| Output directory | `.next` |
| Install command | `npm install` |

`vercel.json` already pins these values so they will be picked up automatically:

```json
{
  "framework": "nextjs",
  "buildCommand": "next build",
  "outputDirectory": ".next",
  "installCommand": "npm install"
}
```

## Environment variables

Set these in **Project Settings → Environment Variables**:

| Variable | Environment | Purpose |
|---|---|---|
| `SAJU_ALLOWED_ORIGINS` | Production | Comma-separated allowed origins, e.g. `https://cosmicsaju.com,https://www.cosmicsaju.com` |
| `UPSTASH_REDIS_REST_URL` | Production | Upstash Redis REST URL for shared rate limiting |
| `UPSTASH_REDIS_REST_TOKEN` | Production | Upstash Redis REST token |
| `SMTP_USER` | Production | Gmail / SMTP sender address |
| `SMTP_PASS` | Production | App-specific password or SMTP credential |
| `TO_EMAIL` | Production | Destination inbox for report requests (defaults to `cosmicsaju@gmail.com`) |
| `NEXT_PUBLIC_*` | All | Any public-facing variables used by the client |

`SAJU_ALLOWED_ORIGINS` is optional; when omitted the allowlist falls back to `cosmicsaju.com` and `.vercel.app` on preview. `localhost` is only allowed when neither `VERCEL_ENV` nor `NODE_ENV=production` is set.

## Pre-deployment checks

From inside `apps/landing-page`:

```bash
npm install
npm run lint
npm run build
npm test
RUN_API_TESTS=1 BASE=http://localhost:3001 npm run test:api  # after starting dev server
```

## Turbopack root pinning

`next.config.ts` pins the Turbopack root to the project directory to prevent Next.js from climbing to a parent workspace that may contain a stray lockfile:

```ts
turbopack: {
  root: path.resolve(process.cwd()),
}
```

## Security notes

- The edge proxy (`src/proxy.ts`) enforces CSP nonces, security headers, origin checks, and blocks common exploit paths.
- API routes are protected by origin allowlist + rate limiting (in-memory fallback or Upstash Redis).
- `poweredByHeader: false` removes the `X-Powered-By` header.

## Useful links

- Vercel project dashboard: https://vercel.com/dashboard
- Vercel docs for Next.js: https://vercel.com/docs/frameworks/nextjs
