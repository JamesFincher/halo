# Stack choice

**Detect first** (if TARGET has code): package.json, pyproject, Gemfile, go.mod, etc. Summarize.

**If greenfield / ambiguous**, propose default with reason. Halo does not force one stack forever — pick best for idea:

Common defaults to propose (choose one set):

| Profile | When |
|---------|------|
| **Web app SaaS** | Next.js + TS + Tailwind + Postgres | Auth + multi-page product |
| **API + simple UI** | FastAPI + React/Vite | Heavy backend / ML |
| **Python agent tool** | Python package + CLI | Internal agent tooling |
| **Existing** | Detected stack | Always prefer if real code present |

AskUserQuestion with 3–4 options tailored to idea.  
Lock: `intake.stack` = `{profile, language, framework, ui, db, hosting_guess, notes}`.

Explain each technical term in one line if user non-technical.
