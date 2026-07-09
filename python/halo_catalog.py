#!/usr/bin/env python3
"""Known integrations + lifecycle defaults for readiness foresight. Stdlib only."""

from __future__ import annotations

from typing import Any

# Baseline always considered for a shippable web product unless stack says otherwise.
LIFECYCLE_BASELINE: list[dict[str, Any]] = [
    {
        "id": "git",
        "purpose": "version control",
        "provider": "git",
        "blocking": True,
        "credentials": [],
        "cli": ["git"],
        "cli_auth": [],
        "required_for_milestones": ["all"],
    },
    {
        "id": "github",
        "purpose": "remote hosting + PRs",
        "provider": "GitHub",
        "blocking": False,
        "credentials": ["GH_TOKEN"],
        "cli": ["gh"],
        "cli_auth": ["gh auth status"],
        "required_for_milestones": ["all"],
    },
    {
        "id": "node",
        "purpose": "JS toolchain (if web/node stack)",
        "provider": "Node.js",
        "blocking": False,
        "stack_profiles": ["web-saas", "api-ui", "nextjs", "vite", "node"],
        "credentials": [],
        "cli": ["node", "npm"],
        "cli_auth": [],
        "required_for_milestones": ["all"],
    },
    {
        "id": "python",
        "purpose": "Python runtime (if python stack)",
        "provider": "Python",
        "blocking": False,
        "stack_profiles": ["api-ui", "fastapi", "python-agent", "python"],
        "credentials": [],
        "cli": ["python3"],
        "cli_auth": [],
        "required_for_milestones": ["all"],
    },
    {
        "id": "vercel",
        "purpose": "preview / production hosting",
        "provider": "Vercel",
        "blocking": True,
        "stack_profiles": ["web-saas", "nextjs", "vite"],
        "credentials": ["VERCEL_TOKEN"],
        "cli": ["vercel"],
        "cli_auth": ["vercel whoami"],
        "required_for_milestones": ["all"],
        "human_action": "Create Vercel account; install CLI; vercel login; link project",
    },
    {
        "id": "database",
        "purpose": "persistent data store",
        "provider": "Postgres (Neon/Supabase/etc)",
        "blocking": True,
        # Only required for full-stack SaaS profiles — not factory dogfood / existing CLI / pure agent
        "stack_profiles": ["web-saas", "nextjs", "nextjs-saas", "vite", "api-ui", "fastapi"],
        "credentials": ["DATABASE_URL"],
        "cli": [],
        "cli_auth": [],
        "required_for_milestones": ["all"],
        "human_action": "Provision Postgres; set DATABASE_URL in .env",
    },
    {
        "id": "auth",
        "purpose": "user authentication",
        "provider": "Clerk",
        "blocking": True,
        "aliases": ["clerk", "authjs", "supabase-auth", "nextauth"],
        "stack_profiles": ["web-saas", "nextjs", "nextjs-saas", "vite", "api-ui"],
        "credentials": ["CLERK_SECRET_KEY", "CLERK_PUBLISHABLE_KEY", "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY"],
        "cli": [],
        "cli_auth": [],
        "required_for_milestones": ["all"],
        "human_action": "Create Clerk app; copy publishable + secret keys to .env",
    },
    {
        "id": "sentry",
        "purpose": "error monitoring (whole lifecycle)",
        "provider": "Sentry",
        "blocking": False,
        "credentials": ["SENTRY_DSN"],
        "cli": [],
        "cli_auth": [],
        "required_for_milestones": ["all"],
        "human_action": "Create Sentry project; set SENTRY_DSN",
    },
    {
        "id": "email",
        "purpose": "transactional email",
        "provider": "Resend",
        "blocking": False,
        "aliases": ["resend", "postmark", "sendgrid"],
        "credentials": ["RESEND_API_KEY"],
        "cli": [],
        "cli_auth": [],
        "required_for_milestones": [],
        "human_action": "Create Resend account; set RESEND_API_KEY",
    },
    {
        "id": "stripe",
        "purpose": "payments",
        "provider": "Stripe",
        "blocking": False,
        "aliases": ["stripe", "payments"],
        "credentials": ["STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET", "NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY"],
        "cli": ["stripe"],
        "cli_auth": [],
        "required_for_milestones": [],
        "human_action": "Create Stripe account; set secret + publishable keys; webhook secret for deploy",
    },
    {
        "id": "openai",
        "purpose": "AI provider",
        "provider": "OpenAI",
        "blocking": False,
        "aliases": ["openai", "anthropic", "xai", "grok"],
        "credentials": ["OPENAI_API_KEY"],
        "cli": [],
        "cli_auth": [],
        "required_for_milestones": [],
        "human_action": "Create API key; set OPENAI_API_KEY (or provider-specific var)",
    },
    {
        "id": "analytics",
        "purpose": "product analytics",
        "provider": "PostHog / GA4",
        "blocking": False,
        "credentials": ["NEXT_PUBLIC_POSTHOG_KEY", "NEXT_PUBLIC_GA_ID"],
        "cli": [],
        "cli_auth": [],
        "required_for_milestones": [],
        "human_action": "Optional for v1; set analytics key if in scope",
    },
]


def normalize_id(raw: str) -> str:
    s = raw.strip().lower().replace(" ", "-")
    for item in LIFECYCLE_BASELINE:
        if s == item["id"] or s in item.get("aliases", []):
            return item["id"]
        if s in item.get("provider", "").lower():
            return item["id"]
    return s


def merge_integrations(
    intake_integrations: list[dict[str, Any]] | None,
    stack_profile: str | None,
) -> list[dict[str, Any]]:
    """Union baseline + intake; mark stack-irrelevant node/python as non-blocking skip."""
    by_id: dict[str, dict[str, Any]] = {}
    profile = (stack_profile or "").lower()

    for base in LIFECYCLE_BASELINE:
        item = dict(base)
        profiles = item.get("stack_profiles")
        if profiles and profile:
            if not any(p in profile for p in profiles):
                item["skip_reason"] = f"stack profile '{profile}' does not need this"
                item["blocking"] = False
                item["optional_skip"] = True
        by_id[item["id"]] = item

    for raw in intake_integrations or []:
        rid = normalize_id(str(raw.get("id") or raw.get("provider") or raw.get("name") or "custom"))
        if rid in by_id:
            dest = by_id[rid]
            # intake can force provider + credentials + blocking
            if raw.get("provider"):
                dest["provider"] = raw["provider"]
            if raw.get("credentials"):
                dest["credentials"] = list(dict.fromkeys(list(dest.get("credentials") or []) + list(raw["credentials"])))
            if raw.get("blocking") is True:
                dest["blocking"] = True
            if raw.get("required_for_milestones"):
                dest["required_for_milestones"] = raw["required_for_milestones"]
            if raw.get("human_action"):
                dest["human_action"] = raw["human_action"]
            if raw.get("purpose"):
                dest["purpose"] = raw["purpose"]
            dest.pop("optional_skip", None)
            dest.pop("skip_reason", None)
        else:
            by_id[rid] = {
                "id": rid,
                "purpose": raw.get("purpose") or rid,
                "provider": raw.get("provider") or rid,
                "blocking": bool(raw.get("blocking", True)),
                "credentials": list(raw.get("credentials") or []),
                "cli": list(raw.get("cli") or raw.get("cli_or_tools") or []),
                "cli_auth": list(raw.get("cli_auth") or []),
                "required_for_milestones": raw.get("required_for_milestones") or ["all"],
                "human_action": raw.get("human_action") or f"Configure {rid} and set credentials",
            }

    # Always keep git blocking
    if "git" in by_id:
        by_id["git"]["blocking"] = True
        by_id["git"].pop("optional_skip", None)

    # Factory dogfood / pure tooling: stack "existing" or empty intake integrations
    # should not force SaaS DB/auth. stack_profiles already soft-skips when set.
    # If profile is existing/python-agent/halo with no integrations, skip saas blockers.
    light = profile in ("existing", "python-agent", "halo", "python", "cli", "")
    if light and not (intake_integrations or []):
        for sid in ("database", "auth", "vercel", "stripe", "email", "sentry", "analytics"):
            if sid in by_id and by_id[sid].get("blocking"):
                by_id[sid]["blocking"] = False
                by_id[sid]["optional_skip"] = True
                by_id[sid]["skip_reason"] = (
                    f"profile '{profile or 'none'}' without integrations — not required"
                )

    return list(by_id.values())
