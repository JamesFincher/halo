# Integrations (lifecycle foresight)

For each in-scope feature, list external services needed. Also add **platform defaults** for a serious v1 ship:

Always consider:

- Hosting / preview deploys (e.g. Vercel, Fly, Railway)
- Auth (Clerk, Auth.js, Supabase Auth, …)
- Database hosted (Neon, Supabase, RDS, …)
- Errors/monitoring (Sentry)
- Email (Resend, Postmark)
- Payments if in scope (Stripe)
- AI providers if in scope
- Analytics if in scope

For each integration:

1. Plain-language what it does
2. Default provider + one-line why
3. Confirm / switch
4. Credentials the human must obtain later (name the env vars conceptually: `SENTRY_DSN`, `CLERK_SECRET_KEY`, …)

**Do not store secret values in git.** Only inventory names.

Lock: `intake.integrations[]` =

```json
{
  "id": "sentry",
  "purpose": "error monitoring",
  "provider": "Sentry",
  "required_for_milestones": ["all"],
  "credentials": ["SENTRY_DSN"],
  "cli_or_tools": [],
  "status": "planned"
}
```

If user refuses a needed integration → either move feature OOS or accept degraded path documented in readiness.
