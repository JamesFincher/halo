#!/usr/bin/env python3
'''Write .halo/spec/* from intake JSON in state. Stdlib only. Used by halo-spec-pack agents + CI.

This version generates an intentionally excessive, verbose spec pack. The goal is to
describe as much as possible up front so the build loop has minimal ambiguity. Docs are
written from `state.intake` and, where fields are missing, derived from the brief or left
as explicit placeholders for the agent to fill later.
'''

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_state(repo: Path) -> dict[str, Any]:
    p = repo / ".halo" / "state.json"
    if not p.exists():
        raise SystemExit(f"missing {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def bullets(items: list[Any], key: str | None = None) -> str:
    if not items:
        return "- (none)\n"
    lines = []
    for it in items:
        if isinstance(it, dict):
            title = it.get(key or "title") or it.get("name") or it.get("id") or str(it)
            extra = it.get("one_liner") or it.get("scope") or it.get("purpose") or ""
            lines.append(f"- **{title}**" + (f" — {extra}" if extra else ""))
        else:
            lines.append(f"- {it}")
    return "\n".join(lines) + "\n"


def _table(rows: list[list[str]]) -> str:
    '''Render a simple Markdown table from rows.'''
    if not rows:
        return "\n"
    widths = [max(len(str(r[i])) for r in rows) for i in range(len(rows[0]))]
    out = []
    out.append("| " + " | ".join(str(rows[0][i]).ljust(widths[i]) for i in range(len(rows[0]))) + " |")
    out.append("| " + " | ".join("-" * widths[i] for i in range(len(rows[0]))) + " |")
    for r in rows[1:]:
        out.append("| " + " | ".join(str(r[i]).ljust(widths[i]) for i in range(len(r))) + " |")
    return "\n".join(out) + "\n"


def _coerce_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return [value]
    return []


def _coerce_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _feature_titles(features: Any) -> list[str]:
    return [
        f.get("title") if isinstance(f, dict) else str(f)
        for f in _coerce_list(features)
    ]


def _entities(data_model: Any) -> list[dict[str, Any]]:
    dm = _coerce_dict(data_model)
    if isinstance(dm.get("entities"), list):
        return [e for e in dm["entities"] if isinstance(e, dict)]
    if isinstance(dm.get("models"), list):
        return [m for m in dm["models"] if isinstance(m, dict)]
    return []


def _api_endpoints(intake: dict[str, Any]) -> list[dict[str, Any]]:
    '''Derive API endpoints from intake.api or from data_model entities (CRUD guess).'''
    api = _coerce_dict(intake.get("api"))
    endpoints = _coerce_list(api.get("endpoints"))
    if endpoints:
        return endpoints
    for entity in _entities(intake.get("data_model")):
        name = entity.get("name", "Item")
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "items"
        endpoints.extend([
            {"method": "GET", "path": f"/api/v1/{slug}", "response": f"{name}[]", "description": f"List all {name}s"},
            {"method": "POST", "path": f"/api/v1/{slug}", "body": f"Create{name}Input", "response": name, "description": f"Create a new {name}"},
            {"method": "GET", "path": f"/api/v1/{slug}/{{id}}", "response": name, "description": f"Get a single {name}"},
            {"method": "PATCH", "path": f"/api/v1/{slug}/{{id}}", "body": f"Update{name}Input", "response": name, "description": f"Update a {name}"},
            {"method": "DELETE", "path": f"/api/v1/{slug}/{{id}}", "response": "void", "description": f"Delete a {name}"},
        ])
    return endpoints


def _user_flows(intake: dict[str, Any]) -> list[dict[str, Any]]:
    flows = _coerce_list(_coerce_dict(intake.get("user_flows")).get("flows"))
    if flows:
        return flows
    for feat in _feature_titles(intake.get("features")):
        flows.append({"name": feat, "steps": ["Open app", f"Complete: {feat}", "Verify result"]})
    return flows


def _sequences(intake: dict[str, Any]) -> list[dict[str, Any]]:
    seqs = _coerce_list(_coerce_dict(intake.get("sequences")).get("sequences"))
    if seqs:
        return seqs
    for flow in _user_flows(intake):
        name = flow.get("name") if isinstance(flow, dict) else str(flow)
        seqs.append({"name": name, "actors": ["User", "App", "API"], "steps": [f"User initiates {name}", "App validates input", "API processes request", "App shows result"]})
    return seqs


def _states(intake: dict[str, Any]) -> list[dict[str, Any]]:
    states = _coerce_list(_coerce_dict(intake.get("states")).get("machines"))
    if states:
        return states
    for feat in _feature_titles(intake.get("features")):
        states.append({"name": f"{feat} state", "states": ["idle", "active", "complete", "error"], "transitions": ["idle -> active", "active -> complete", "active -> error", "error -> idle"]})
    return states


def _decisions(intake: dict[str, Any]) -> list[dict[str, Any]]:
    decisions = _coerce_list(_coerce_dict(intake.get("decisions")).get("records"))
    if decisions:
        return decisions
    stack = _coerce_dict(intake.get("stack"))
    if stack:
        decisions.append({
            "id": "ADR-001",
            "title": f"Stack: {stack.get('language', 'unknown')} + {stack.get('framework', 'unknown')}",
            "context": "Chosen during intake to match the project brief and team constraints.",
            "decision": f"Use {stack.get('language', 'unknown')} with {stack.get('framework', 'unknown')}.",
            "consequences": "Impacts hiring, hosting, testing, and deployment choices.",
        })
    return decisions


def _personas(intake: dict[str, Any]) -> list[dict[str, Any]]:
    users = intake.get("users")
    if isinstance(users, list):
        return [u for u in users if isinstance(u, dict)]
    if isinstance(users, dict):
        return [{"name": k, "description": v} for k, v in users.items() if isinstance(v, str)]
    return [{"name": "Primary user", "description": "The main user of the product"}]


def _integrations(intake: dict[str, Any]) -> list[dict[str, Any]]:
    return _coerce_list(intake.get("integrations"))


def _mermaid_flow(name: str, steps: list[str]) -> str:
    lines = ["flowchart TD"]
    for i, step in enumerate(steps):
        safe = re.sub(r"[^a-zA-Z0-9\s\-]", "", step)
        node_id = f"N{i}"
        lines.append(f"    {node_id}[\"{safe}\"]")
        if i > 0:
            lines.append(f"    N{i-1} --> {node_id}")
    return "\n".join(lines)


def _mermaid_sequence(name: str, actors: list[str], steps: list[str]) -> str:
    lines = ["sequenceDiagram"]
    for actor in actors:
        lines.append(f"    participant {actor}")
    for step in steps:
        parts = step.split(" -> ", 1)
        if len(parts) == 2:
            lines.append(f"    {parts[0]}->>{parts[1]}:")
        else:
            lines.append(f"    Note over {actors[0]}: {step}")
    return "\n".join(lines)


def _mermaid_state(name: str, states: list[str], transitions: list[str]) -> str:
    lines = ["stateDiagram-v2"]
    for state in states:
        lines.append(f"    {state}")
    for t in transitions:
        parts = t.split(" -> ")
        if len(parts) == 2:
            lines.append(f"    {parts[0]} --> {parts[1]}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Renderers for each spec document
# ---------------------------------------------------------------------------


def _render_prd(name: str, intake: dict[str, Any]) -> str:
    purpose = intake.get("purpose") or intake.get("core_purpose") or ""
    if isinstance(purpose, dict):
        purpose = purpose.get("text") or purpose.get("purpose") or json.dumps(purpose)
    features = _coerce_list(intake.get("features"))
    oos = _coerce_list(intake.get("out_of_scope"))
    users = intake.get("users") or {}
    success = intake.get("success_metric") or ""
    integrations = _integrations(intake)
    milestones = _coerce_list(intake.get("milestones"))
    risks = _coerce_list(_coerce_dict(intake.get("risks")).get("items"))
    assumptions = _coerce_list(intake.get("assumptions"))
    constraints = _coerce_list(intake.get("constraints"))

    return f'''# {name}

> Generated by Halo {utc_now()}. Edit freely; re-lock when happy.

## 1. Product overview

### What we're building

{purpose or "(describe the product in one or two paragraphs)"}

### Why this matters

(draft the user pain, the opportunity, and the unique value proposition)

### Who it's for

{json.dumps(users, indent=2) if not isinstance(users, str) else users}

### User personas

{_bullets_personas(_personas(intake))}

## 2. Goals and success

### Success metrics

{success or "(define measurable outcomes)"}

### Goals

- Deliver the primary user job end-to-end.
- Provide a reliable, secure, and observable system.
- Ship Demo 0 before the first build cycle.

### Non-goals

{''}
{bullets(oos) if oos else "- (none defined yet)"}

## 3. Scope

### In scope

{bullets(features)}

### Out of scope

{bullets(oos)}

### Assumptions

{''}
{bullets(assumptions) if assumptions else "- (none yet)"}

### Constraints

{''}
{bullets(constraints) if constraints else "- (none yet)"}

## 4. Integrations (summary)

{bullets(integrations, key="id")}

## 5. Milestones (summary)

{bullets(milestones, key="name")}

## 6. Risks and mitigations

{''}
{bullets(risks, key="title") if risks else "- (none yet)"}

## 7. Open questions

- (add during review)
- (what data is needed?)
- (what must be true before launch?)
'''


def _render_stack(name: str, intake: dict[str, Any]) -> str:
    stack = _coerce_dict(intake.get("stack"))
    return f'''# Stack — {name}

## Chosen stack

```json
{json.dumps(stack, indent=2)}
```

## Language and runtime

- **Language**: {stack.get("language", "(choose)")}
- **Runtime**: {stack.get("runtime", "(choose)")}
- **Framework**: {stack.get("framework", "(choose)")}
- **Build system**: {stack.get("build_system", "(choose)")}
- **Package manager**: {stack.get("package_manager", "(choose)")}
- **Output type**: {stack.get("output_type", "(web app / cli / library / mobile)")}

## Hosting and deployment

- **Hosting guess**: {stack.get("hosting_guess") or "preview host TBD (Vercel default for web)"}
- **Deploy target**: {stack.get("deploy", "(none)")}
- **CI/CD**: {stack.get("ci_cd", "GitHub Actions (default)")}

## Key libraries and services

- Auth: {stack.get("auth", "(none)")}
- Database: {stack.get("database", "(none)")}
- Storage: {stack.get("storage", "(none)")}
- Email: {stack.get("email", "(none)")}
- Monitoring: {stack.get("monitoring", "(none)")}

## Repo layout target

Document expected top-level dirs after scaffold.

```
/{name.lower().replace(" ", "-")}
├── src/ or app/           # application code
├── tests/                 # unit, integration, e2e
├── docs/                  # additional docs
├── .halo/                 # halo state
├── .env.example
└── README.md
```

## Conventions

- Code style, linting, formatting, and branch strategy.
- Environment variable naming and secret handling.
- Test and evidence requirements.
'''


def _render_data_model(name: str, intake: dict[str, Any]) -> str:
    data_model = _coerce_dict(intake.get("data_model"))
    entities = _entities(data_model)
    out = [f"# Data model — {name}", "", "Conceptual data model. Not SQL."]
    if entities:
        for entity in entities:
            ename = entity.get("name", "Entity")
            out.append(f"\n## {ename}")
            fields = _coerce_list(entity.get("fields"))
            if fields:
                rows = [["Field", "Type", "Required", "Notes"]]
                for f in fields:
                    if isinstance(f, dict):
                        rows.append([f.get("name", ""), f.get("type", ""), "Yes" if f.get("required") else "", f.get("notes", "")])
                    else:
                        rows.append([str(f), "", "", ""])
                out.append(_table(rows))
            else:
                out.append("- (no fields defined)")
    else:
        out.append("\n- (no entities defined; derive from PRD features)")
    out.append("\n## Relationships")
    out.append(data_model.get("relationships") or "(describe relationships during review)")
    out.append("\n## Indexes and constraints")
    out.append("- (list unique constraints, foreign keys, and performance indexes)")
    out.append("\n## Migrations")
    out.append("- Initial migration creates the entities above.")
    out.append("- Future migrations follow the naming convention `YYYYMMDD_HHMMSS_description.sql`.")
    out.append("\n## Seed data")
    out.append("- (describe demo accounts, fixtures, and sample data for local dev)")
    return "\n".join(out)


def _render_design(name: str, intake: dict[str, Any]) -> str:
    design = _coerce_dict(intake.get("design"))
    return f'''# Design — {name}

## Design principles

- (list 3-5 principles that guide UI/UX)
- Clear, fast, accessible.

## Style and brand

```json
{json.dumps(design, indent=2)}
```

- **Primary color**: {design.get("primary_color", "(choose)")}
- **Secondary color**: {design.get("secondary_color", "(choose)")}
- **Typography**: {design.get("typography", "(choose)")}
- **Tone**: {design.get("tone", "(choose)")}

## Screens (draft)

Derive from features during review.

1. **Landing / auth**
2. **Dashboard / home**
3. **Primary feature screens**
4. **Settings / profile**

## Components (draft)

- Header / navigation
- Empty state
- Loading skeleton
- Error boundary
- Form inputs and validation

## UX patterns

- Navigation, feedback, error handling, empty states.
- Loading states and optimistic updates.

## Accessibility

- WCAG 2.1 AA target.
- Keyboard navigation, focus management, alt text, color contrast.
'''


def _render_architecture(name: str, intake: dict[str, Any]) -> str:
    stack = _coerce_dict(intake.get("stack"))
    return f'''# Architecture — {name}

## Boundaries

- Client UI
- API / server
- Data store
- Background workers (if any)
- External providers (see INTEGRATIONS.md)

## Component diagram

```mermaid
flowchart TD
    User[User] --> UI[Client UI]
    UI --> API[API / Server]
    API --> DB[(Data Store)]
    API --> Ext[External Services]
```

## Data flow

1. User action in UI.
2. UI calls API (REST/GraphQL/tRPC).
3. API validates auth and input.
4. API reads/writes data store.
5. External services called as needed.
6. Response returns to UI.

## Deploy topology

- Dev / preview: per STACK hosting
- Prod: human promote only

## Technology boundaries

- **Frontend**: {stack.get("framework", "(choose)")}
- **Backend**: {stack.get("backend", "(choose)")}
- **Database**: {stack.get("database", "(choose)")}
- **Auth**: {stack.get("auth", "(choose)")}
- **Hosting**: {stack.get("hosting_guess", "(choose)")}

## Non-goals

See PRD out of scope.
'''


def _render_integrations(name: str, intake: dict[str, Any]) -> str:
    integrations = _integrations(intake)
    lines = ["# Integrations — " + name, ""]
    for it in integrations:
        if isinstance(it, dict):
            lines.append(f"## {it.get('id') or it.get('provider')}")
            lines.append(f"- **Purpose**: {it.get('purpose')}")
            lines.append(f"- **Provider**: {it.get('provider')}")
            lines.append(f"- **Credentials**: {', '.join(it.get('credentials') or []) or '—'}")
            lines.append(f"- **Environment variables**: {', '.join(it.get('env') or []) or '—'}")
            lines.append(f"- **Required for milestones**: {it.get('required_for_milestones')}")
            lines.append(f"- **Fallback if unavailable**: {it.get('fallback') or '—'}")
            lines.append("")
    if len(lines) == 2:
        lines.append("(none locked — readiness will still apply lifecycle baseline)")
    return "\n".join(lines)


def _bullets_personas(personas: list[dict[str, Any]]) -> str:
    if not personas:
        return "- (none defined yet)\n"
    lines = []
    for p in personas:
        name = p.get("name", "User")
        desc = p.get("description", "")
        needs = p.get("needs", "")
        lines.append(f"- **{name}** — {desc}{f' (needs: {needs})' if needs else ''}")
    return "\n".join(lines) + "\n"


def _render_stories(name: str, intake: dict[str, Any]) -> str:
    features = _coerce_list(intake.get("features"))
    lines = [f"# Stories — {name}", ""]
    n = 1
    for feat in features:
        title = feat.get("title") if isinstance(feat, dict) else str(feat)
        one_liner = feat.get("one_liner") if isinstance(feat, dict) else ""
        priority = feat.get("priority") if isinstance(feat, dict) else "high"
        sid = f"S{n:03d}"
        lines.extend([
            f"### {sid} — {title}",
            f"- **Status**: pending",
            f"- **Priority**: {priority}",
            f"- **Milestone**: M1",
            "",
            "#### Description",
            f"{one_liner or title}",
            "",
            "#### Acceptance criteria",
            f"  - [ ] User can complete primary flow for: {title}",
            f"  - [ ] Edge cases are handled (invalid input, empty state, auth failure)",
            f"  - [ ] Covered by automated test or documented manual probe",
            "",
            "#### Edge cases",
            f"- Invalid/missing input for: {title}",
            "- Network or service failure",
            "- Unauthorized access",
            "",
            "#### UI/UX",
            "- Screen and component references (see DESIGN.md).",
            "",
            "#### API / data",
            "- Related endpoints and entities (see API.md and DATA-MODEL.md).",
            "",
            "#### Tests",
            "- Unit test for core logic.",
            "- Integration test for API endpoint.",
            "- E2E or manual probe for user flow.",
            "",
        ])
        n += 1
    if n == 1:
        return f"# Stories — {name}\n\n(none yet)\n"
    return "\n".join(lines)


def _render_milestones(name: str, intake: dict[str, Any]) -> str:
    milestones = _coerce_list(intake.get("milestones"))
    lines = [f"# Milestones — {name}", ""]
    for m in milestones:
        if not isinstance(m, dict):
            continue
        n = m.get("n", "?")
        mname = m.get("name", "Milestone")
        lines.extend([
            f"## M{n} — {mname}",
            f"- **Slug**: `{m.get('slug')}`",
            f"- **Scope**: {m.get('scope')}",
            f"- **Done when**: {m.get('done_when_draft') or m.get('done_when') or 'TBD'}",
            f"- **Depends on**: {m.get('depends_on')}",
            f"- **Release notes**: (summarize user-visible changes)",
            f"- **Demo URL**: (live probe after scaffold)",
            "",
            "### Features in this milestone",
            "- (map stories here)",
            "",
            "### Acceptance",
            "- All stories pass with evidence.",
            "- Doctor smoke exits 0.",
            "",
        ])
    if len(lines) == 2:
        lines.append("(define milestones in intake)")
    return "\n".join(lines)


def _render_readiness(name: str, intake: dict[str, Any]) -> str:
    return f'''# Readiness — {name}

Run after lock:

```bash
python3 <HALO_SYSTEM>/python/halo_readiness.py --repo . --write
```

This file is overwritten by the readiness tool with the live checklist.

## Pre-readiness items

- [ ] All required CLIs installed (node, python, docker, etc.)
- [ ] All required auth completed (grok, clerk, vercel, etc.)
- [ ] All required secrets in `.env.local`
- [ ] All integrations verified with test commands
- [ ] Stack and scaffold profile confirmed
'''


def _render_api(name: str, intake: dict[str, Any]) -> str:
    endpoints = _api_endpoints(intake)
    api = _coerce_dict(intake.get("api"))
    schemas = _coerce_dict(api.get("schemas"))
    out = [f"# API — {name}", ""]
    out.append("## Overview")
    out.append(f"- Base path: {api.get('base_path', '/api/v1')}")
    out.append(f"- Auth: {api.get('auth', 'Bearer token or session cookie')}")
    out.append(f"- Rate limiting: {api.get('rate_limit', 'TBD')}")
    out.append(f"- Versioning: {api.get('versioning', 'URL path versioning')}")
    out.append("")
    out.append("## Schemas")
    if schemas:
        for sname, sdef in schemas.items():
            out.append(f"\n### {sname}")
            out.append(f"```json\n{json.dumps(sdef, indent=2)}\n```")
    else:
        out.append("- (derive from DATA-MODEL.md)")
    out.append("")
    out.append("## Endpoints")
    if endpoints:
        rows = [["Method", "Path", "Request", "Response", "Description"]]
        for ep in endpoints:
            rows.append([
                ep.get("method", ""),
                ep.get("path", ""),
                ep.get("body", ""),
                ep.get("response", ""),
                ep.get("description", ""),
            ])
        out.append(_table(rows))
    else:
        out.append("- (none defined)")
    out.append("")
    out.append("## Error handling")
    out.append("- 400 Bad Request: validation errors")
    out.append("- 401 Unauthorized: missing or invalid auth")
    out.append("- 403 Forbidden: insufficient permissions")
    out.append("- 404 Not Found: resource missing")
    out.append("- 500 Internal Server Error: unexpected failure")
    out.append("")
    out.append("## Webhooks")
    out.append("- (list webhooks if any)")
    out.append("")
    out.append("## SDK / clients")
    out.append("- (describe generated client or manual fetch wrappers)")
    return "\n".join(out)


def _render_user_flows(name: str, intake: dict[str, Any]) -> str:
    flows = _user_flows(intake)
    out = [f"# User Flows — {name}", ""]
    if not flows:
        out.append("- (derive from PRD features)")
        return "\n".join(out)
    for flow in flows:
        fname = flow.get("name") if isinstance(flow, dict) else str(flow)
        steps = _coerce_list(flow.get("steps")) if isinstance(flow, dict) else []
        out.append(f"## {fname}")
        out.append("\n```mermaid")
        out.append(_mermaid_flow(fname, steps or ["Start", "Action", "End"]))
        out.append("```\n")
        out.append("### Steps")
        for i, step in enumerate(steps or [], 1):
            out.append(f"{i}. {step}")
        out.append("\n### Edge cases")
        out.append("- Invalid input")
        out.append("- Auth failure")
        out.append("- External service error")
        out.append("")
    return "\n".join(out)


def _render_adrs(name: str, intake: dict[str, Any]) -> str:
    decisions = _decisions(intake)
    out = [f"# Architecture Decisions — {name}", ""]
    if not decisions:
        out.append("- (derive from stack and design choices during review)")
        return "\n".join(out)
    for d in decisions:
        out.append(f"## {d.get('id', 'ADR-000')}: {d.get('title', '')}")
        out.append(f"- **Context**: {d.get('context', '')}")
        out.append(f"- **Decision**: {d.get('decision', '')}")
        out.append(f"- **Consequences**: {d.get('consequences', '')}")
        out.append("")
    return "\n".join(out)


def _render_sequence(name: str, intake: dict[str, Any]) -> str:
    seqs = _sequences(intake)
    out = [f"# Sequence Diagrams — {name}", ""]
    if not seqs:
        out.append("- (derive from user flows)")
        return "\n".join(out)
    for s in seqs:
        sname = s.get("name") if isinstance(s, dict) else str(s)
        actors = _coerce_list(s.get("actors")) if isinstance(s, dict) else ["User", "App", "API"]
        steps = _coerce_list(s.get("steps")) if isinstance(s, dict) else []
        out.append(f"## {sname}")
        out.append("\n```mermaid")
        out.append(_mermaid_sequence(sname, actors, steps or ["User -> App: action", "App -> API: request", "API -> App: response"]))
        out.append("```\n")
    return "\n".join(out)


def _render_state(name: str, intake: dict[str, Any]) -> str:
    machines = _states(intake)
    out = [f"# State Machines — {name}", ""]
    if not machines:
        out.append("- (derive from features with status transitions)")
        return "\n".join(out)
    for m in machines:
        mname = m.get("name") if isinstance(m, dict) else str(m)
        states = _coerce_list(m.get("states")) if isinstance(m, dict) else []
        transitions = _coerce_list(m.get("transitions")) if isinstance(m, dict) else []
        out.append(f"## {mname}")
        out.append("\n```mermaid")
        out.append(_mermaid_state(mname, states, transitions))
        out.append("```\n")
    return "\n".join(out)


def _render_security(name: str, intake: dict[str, Any]) -> str:
    services = _coerce_dict(intake.get("services"))
    stack = _coerce_dict(intake.get("stack"))
    security = _coerce_dict(intake.get("security"))
    return f'''# Security — {name}

## Threat model

- What are the highest-value assets?
- What are the likely attack vectors?
- What are the trust boundaries?

## Authentication

- **Provider**: {services.get("auth", stack.get("auth", "(none)"))}
- **Method**: {security.get('auth_method', 'OAuth / passwordless / API key')}
- **Session strategy**: {security.get('session_strategy', 'JWT or session cookie')}

## Authorization

- {security.get('authorization', 'Role-based access control (RBAC) or resource-based access control')}

## Secrets

- Store secrets in environment variables or a secrets manager.
- Never commit secrets.
- Rotate keys on a schedule.

## Data protection

- Encryption at rest: {security.get('encryption_at_rest', 'TDB')}
- Encryption in transit: {security.get('encryption_in_transit', 'TLS 1.3')}
- PII handling: {security.get('pii', 'Minimize collection; mask in logs')}

## Compliance

- {security.get('compliance', 'GDPR, SOC2, HIPAA as needed')}

## Audit

- Log auth events and sensitive actions.
- Retain logs per compliance requirement.
'''


def _render_test_plan(name: str, intake: dict[str, Any]) -> str:
    features = _coerce_list(intake.get("features"))
    out = [f"# Test Plan — {name}", ""]
    out.append("## Strategy")
    out.append("- Unit tests for pure functions and business logic.")
    out.append("- Integration tests for API endpoints and database layers.")
    out.append("- E2E tests for critical user flows.")
    out.append("- Manual smoke tests for demo and deploy.")
    out.append("")
    out.append("## Test cases by story")
    n = 1
    for feat in features:
        title = feat.get("title") if isinstance(feat, dict) else str(feat)
        out.append(f"\n### S{n:03d} — {title}")
        out.append("- **Unit**: core logic and validation")
        out.append("- **Integration**: API request/response")
        out.append("- **E2E**: complete user flow")
        out.append("- **Edge**: invalid input, auth failure, network error")
        n += 1
    out.append("")
    out.append("## Fixtures and mocks")
    out.append("- (describe test fixtures, mock providers, and seed data)")
    out.append("")
    out.append("## CI/CD gates")
    out.append("- All tests green before merge.")
    out.append("- Doctor smoke exits 0.")
    out.append("- Test coverage does not decrease.")
    return "\n".join(out)


def _render_frontend(name: str, intake: dict[str, Any]) -> str:
    stack = _coerce_dict(intake.get("stack"))
    design = _coerce_dict(intake.get("design"))
    return f'''# Frontend — {name}

## Tech

- **Framework**: {stack.get("framework", "(choose)")}
- **UI library**: {stack.get("ui", "(choose)")}
- **State management**: {stack.get("state_management", "(choose)")}
- **Routing**: {stack.get("routing", "(choose)")}
- **Forms**: {stack.get("forms", "(choose)")}

## Routes

- `/` — landing or dashboard
- `/login` — auth
- `/app` — primary feature area
- `/settings` — profile and config

## Components

- Layout, navigation, header, footer
- Page shells and error boundaries
- Feature-specific components
- Shared design-system components

## State and data fetching

- (describe server state, client state, caching, and mutation patterns)

## Forms and validation

- (describe validation library, error display, and submit handling)

## Error and loading states

- Global error boundary
- Per-route loading skeletons
- Toast / notification system

## Accessibility

- Focus management, keyboard nav, ARIA labels, color contrast.

## Style system

```json
{json.dumps(design, indent=2)}
```
'''


def _render_backend(name: str, intake: dict[str, Any]) -> str:
    stack = _coerce_dict(intake.get("stack"))
    return f'''# Backend — {name}

## Tech

- **Runtime**: {stack.get("runtime", "(choose)")}
- **Framework**: {stack.get("backend", stack.get("framework", "(choose)"))}
- **Database**: {stack.get("database", "(choose)")}
- **Cache**: {stack.get("cache", "(none)")}
- **Queue**: {stack.get("queue", "(none)")}

## Services

- (describe service layer, e.g., `UserService`, `HabitService`)

## Handlers / routes

- (map routes from API.md)

## Data access

- (describe repository / ORM patterns)

## Background workers

- (list jobs, schedules, and retry policies)

## Caching and rate limiting

- (describe cache keys, TTL, and rate limits)

## Logging and observability

- (structured logging, tracing, metrics)
'''


def _render_mobile(name: str, intake: dict[str, Any]) -> str:
    stack = _coerce_dict(intake.get("stack"))
    if stack.get("output_type") not in ("mobile", "mobile app"):
        return f'''# Mobile — {name}

Mobile is not the primary output type for this project ({stack.get("output_type", "not specified")}).
This document can be skipped or expanded later if mobile becomes a target.
'''
    return f'''# Mobile — {name}

## Platforms

- iOS and Android
- (or PWA if cross-platform)

## Tech

- **Framework**: {stack.get("framework", "(choose)")}
- **State**: {stack.get("state_management", "(choose)")}

## Platform specifics

- Push notifications
- Offline support
- App store submission
- Deep linking
- Camera / location / contacts permissions (if needed)
'''


def _render_deployment(name: str, intake: dict[str, Any]) -> str:
    stack = _coerce_dict(intake.get("stack"))
    return f'''# Deployment — {name}

## Environments

- **Local**: `localhost` with `.env.local`
- **Preview**: per-branch or per-PR deploy
- **Staging**: production-like, safe for demos
- **Production**: human-promoted only

## Hosting

- **Provider**: {stack.get("deploy", stack.get("hosting_guess", "(choose)"))}
- **Region**: {stack.get("region", "(choose)")}

## CI/CD pipeline

1. Lint and type-check
2. Unit tests
3. Build
4. Deploy preview
5. Integration tests
6. Human approval for prod

## Infrastructure

- (describe databases, caches, queues, object storage, CDNs)

## Feature flags

- (list feature flags and rollout strategy)

## Rollback

- Keep previous deploy ready.
- Roll back on error rate or alert.

## Monitoring

- (health checks, logs, metrics, alerting)
'''


def _render_runbook(name: str, intake: dict[str, Any]) -> str:
    integrations = _integrations(intake)
    out = [f"# Runbook — {name}", ""]
    out.append("## Operations")
    out.append("- Daily: check health dashboards and error rates.")
    out.append("- Weekly: review metrics and costs.")
    out.append("- Monthly: rotate secrets and review access.")
    out.append("")
    out.append("## Alerts")
    out.append("- High error rate")
    out.append("- High latency")
    out.append("- Failed deploy")
    out.append("- Integration outage")
    out.append("")
    out.append("## Incident response")
    out.append("1. Identify scope and blast radius.")
    out.append("2. Mitigate user impact.")
    out.append("3. Debug and fix.")
    out.append("4. Verify with probes and tests.")
    out.append("5. Post-incident review.")
    out.append("")
    out.append("## Backup and restore")
    out.append("- (describe backup schedule, retention, and restore procedure)")
    out.append("")
    out.append("## Third-party escalations")
    for it in integrations:
        if isinstance(it, dict):
            out.append(f"- {it.get('provider', '')}: {it.get('status_page', 'status page TBD')}")
    return "\n".join(out)


def _render_metrics(name: str, intake: dict[str, Any]) -> str:
    success = intake.get("success_metric") or ""
    features = _feature_titles(intake.get("features"))
    return f'''# Metrics — {name}

## Success metrics

{success or "(define measurable outcomes)"}

## Product metrics

- Activation rate
- Retention (D1, D7, D30)
- Feature usage
- Conversion / goal completion

## Technical metrics

- Latency (p50, p95, p99)
- Error rate
- Throughput
- Availability / uptime

## Analytics events

{''}
{bullets([f"`{f.lower().replace(' ', '_')}_completed`" for f in features]) if features else "- (none defined)"}

## Dashboards

- Product dashboard
- Infrastructure dashboard
- Error and alert dashboard

## SLOs

- Availability: 99.9%
- P95 latency: < 500ms
- Error rate: < 0.1%
'''


def _render_prompts(name: str, intake: dict[str, Any]) -> str:
    features = _feature_titles(intake.get("features"))
    prompts = _coerce_list(_coerce_dict(intake.get("prompts")).get("items"))
    out = [f"# Prompts — {name}", ""]
    out.append("## Model selection")
    out.append("- Default model: (choose based on task)")
    out.append("- Fallback model: (cheaper / faster)")
    out.append("- Evaluation model: (for judge / eval)")
    out.append("")
    out.append("## Prompts")
    if prompts:
        for p in prompts:
            p = _coerce_dict(p)
            out.append(f"\n### {p.get('name', 'Prompt')}")
            out.append(f"**System**: {p.get('system', '')}")
            out.append(f"**User template**: {p.get('template', '')}")
            out.append(f"**Guardrails**: {p.get('guardrails', '')}")
    else:
        out.append("- (derive from AI features if any)")
    out.append("")
    out.append("## Evals")
    out.append("- (describe evaluation dataset and pass criteria)")
    out.append("")
    out.append("## Feature prompt hooks")
    for f in features:
        out.append(f"- `{f.lower().replace(' ', '_')}_prompt` — (describe prompt for: {f})")
    return "\n".join(out)


def _render_glossary(name: str, intake: dict[str, Any]) -> str:
    features = _feature_titles(intake.get("features"))
    entities = [e.get("name", "") for e in _entities(intake.get("data_model"))]
    terms = _coerce_dict(intake.get("glossary"))
    out = [f"# Glossary — {name}", ""]
    if terms:
        for t, d in terms.items():
            out.append(f"- **{t}**: {d}")
    else:
        out.append("- **Domain terms**:")
        for f in features:
            out.append(f"  - {f}: user-facing feature")
        for e in entities:
            out.append(f"  - {e}: core entity")
    out.append("")
    out.append("## Abbreviations")
    out.append("- API: Application Programming Interface")
    out.append("- CI/CD: Continuous Integration / Continuous Deployment")
    out.append("- E2E: End-to-End")
    out.append("- PII: Personally Identifiable Information")
    out.append("- SLO: Service Level Objective")
    return "\n".join(out)


def _render_risks(name: str, intake: dict[str, Any]) -> str:
    risks = _coerce_list(_coerce_dict(intake.get("risks")).get("items"))
    integrations = _integrations(intake)
    out = [f"# Risks — {name}", ""]
    if risks:
        for r in risks:
            r = _coerce_dict(r)
            out.append(f"## {r.get('title', 'Risk')}")
            out.append(f"- **Likelihood**: {r.get('likelihood', 'medium')}")
            out.append(f"- **Impact**: {r.get('impact', 'medium')}")
            out.append(f"- **Mitigation**: {r.get('mitigation', '')}")
            out.append("")
    else:
        out.append("## Known risks")
        out.append("- Integration outages (Clerk, Vercel, etc.)")
        out.append("- Scope creep beyond PRD")
        out.append("- Secrets leakage or misconfiguration")
        out.append("- Performance issues under load")
        out.append("- Low test coverage leading to regressions")
        out.append("")
    if integrations:
        out.append("## Integration risks")
        for it in integrations:
            if isinstance(it, dict):
                out.append(f"- {it.get('provider', '')}: {it.get('risk', 'availability / billing / API changes')}")
    return "\n".join(out)


def _render_personas(name: str, intake: dict[str, Any]) -> str:
    personas = _personas(intake)
    out = [f"# Personas — {name}", ""]
    for p in personas:
        pname = p.get("name", "User")
        out.append(f"## {pname}")
        out.append(f"- **Description**: {p.get('description', '')}")
        out.append(f"- **Needs**: {p.get('needs', '')}")
        out.append(f"- **Pain points**: {p.get('pain_points', '')}")
        out.append(f"- **Jobs-to-be-done**: {p.get('jobs', '')}")
        out.append("")
    return "\n".join(out)


def _render_seed(name: str, intake: dict[str, Any]) -> str:
    entities = _entities(intake.get("data_model"))
    out = [f"# Seed Data — {name}", ""]
    out.append("## Local development")
    out.append("- (list demo accounts, organizations, and sample data)")
    out.append("")
    out.append("## Entities")
    for entity in entities:
        ename = entity.get("name", "Entity")
        out.append(f"- **{ename}**: 2-3 sample records for manual testing")
    out.append("")
    out.append("## Fixtures")
    out.append("- Unit test fixtures")
    out.append("- Integration test fixtures")
    out.append("- E2E seed script")
    return "\n".join(out)


def _render_changelog(name: str, intake: dict[str, Any]) -> str:
    milestones = _coerce_list(intake.get("milestones"))
    out = [f"# Changelog — {name}", ""]
    out.append("## Unreleased")
    out.append("- (current work in progress)")
    out.append("")
    for m in milestones:
        if not isinstance(m, dict):
            continue
        out.append(f"## {m.get('name', 'Release')}")
        out.append(f"- {m.get('scope', '')}")
        out.append("")
    return "\n".join(out)


def _render_contributing(name: str, intake: dict[str, Any]) -> str:
    stack = _coerce_dict(intake.get("stack"))
    return f'''# Contributing — {name}

## Conventions

- Branch naming: `feat/Sxxx-short-desc`, `fix/Sxxx-short-desc`
- Commit messages: reference story ID, keep scope small
- Code review: at least one approval before merge
- Tests: no PR without covering test or documented manual probe

## Setup

```bash
# Install dependencies
# e.g., npm install, pip install, etc.

# Copy environment
# cp .env.example .env.local

# Run dev server
# e.g., npm run dev
```

## Lint and format

- {stack.get('linter', '(choose linter)')}
- {stack.get('formatter', '(choose formatter)')}

## Tests

```bash
# Unit tests
# npm test

# Integration tests
# npm run test:integration

# E2E tests
# npm run test:e2e
```

## Evidence

- Every story must have a `.halo/evidence/Sxxx-green.json` cert before mark passes.
'''


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------


def write_specs(repo: Path) -> list[str]:
    state = load_state(repo)
    intake = state.get("intake") or {}
    name = state.get("product_name") or intake.get("product_name") or "Product"

    spec = repo / ".halo" / "spec"
    spec.mkdir(parents=True, exist_ok=True)
    written: list[str] = []

    def w(fname: str, body: str) -> None:
        path = spec / fname
        path.write_text(body.strip() + "\n", encoding="utf-8")
        written.append(str(path.relative_to(repo)))

    # Core spec pack
    w("PRD.md", _render_prd(name, intake))
    w("STACK.md", _render_stack(name, intake))
    w("DATA-MODEL.md", _render_data_model(name, intake))
    w("DESIGN.md", _render_design(name, intake))
    w("ARCHITECTURE.md", _render_architecture(name, intake))
    w("INTEGRATIONS.md", _render_integrations(name, intake))
    w("STORIES.md", _render_stories(name, intake))
    w("MILESTONES.md", _render_milestones(name, intake))
    w("READINESS.md", _render_readiness(name, intake))

    # Expanded spec pack
    w("API.md", _render_api(name, intake))
    w("USER-FLOWS.md", _render_user_flows(name, intake))
    w("ARCHITECTURE-DECISIONS.md", _render_adrs(name, intake))
    w("SEQUENCE.md", _render_sequence(name, intake))
    w("STATE.md", _render_state(name, intake))
    w("SECURITY.md", _render_security(name, intake))
    w("TEST-PLAN.md", _render_test_plan(name, intake))
    w("FRONTEND.md", _render_frontend(name, intake))
    w("BACKEND.md", _render_backend(name, intake))
    w("MOBILE.md", _render_mobile(name, intake))
    w("DEPLOYMENT.md", _render_deployment(name, intake))
    w("RUNBOOK.md", _render_runbook(name, intake))
    w("METRICS.md", _render_metrics(name, intake))
    w("PROMPTS.md", _render_prompts(name, intake))
    w("GLOSSARY.md", _render_glossary(name, intake))
    w("RISKS.md", _render_risks(name, intake))
    w("PERSONAS.md", _render_personas(name, intake))
    w("SEED.md", _render_seed(name, intake))
    w("CHANGELOG.md", _render_changelog(name, intake))
    w("CONTRIBUTING.md", _render_contributing(name, intake))

    # mark drafting and bump spec pack version so gates know the expanded pack was generated
    state["spec_pack_version"] = 2
    state["spec_status"] = state.get("spec_status") if state.get("spec_status") == "locked" else "ready_for_review"
    if state.get("phase") not in ("readiness", "scaffold", "build"):
        state["phase"] = "spec_review"
    state["updated_at"] = utc_now()
    (repo / ".halo" / "state.json").write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    (repo / ".halo" / "baton.md").write_text(
        "# Baton\n- Phase: spec_review\n- Next: human reviews .halo/spec/; then "
        "`python3 …/halo_state.py lock-specs --repo .` then readiness\n",
        encoding="utf-8",
    )
    # machine feature list (done tracking)
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from halo_features import sync_from_stories
        from halo_progress import append as progress_append

        sync_from_stories(repo)
        progress_append(repo, "spec_pack_written", {"files": len(written)})
    except Exception:
        pass
    return written


def main() -> None:
    p = argparse.ArgumentParser(prog="halo_spec_write")
    p.add_argument("--repo", default=".")
    args = p.parse_args()
    written = write_specs(Path(args.repo).resolve())
    print(json.dumps({"ok": True, "files": written}, indent=2))


if __name__ == "__main__":
    main()
