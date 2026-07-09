"""Offline Next.js App Router skeleton (no create-next-app network required)."""

from __future__ import annotations

import json
from pathlib import Path

from scaffold.common import NEXT_GITIGNORE, merge_gitignore, write_text


def scaffold(repo: Path, product_name: str = "Halo App") -> dict:
    """Create minimal Next.js-compatible tree. Returns {created: [...], health_path}."""
    created: list[str] = []
    pkg_path = repo / "package.json"

    if pkg_path.exists():
        # Non-destructive: ensure health route
        health = repo / "app" / "api" / "health" / "route.ts"
        if not health.exists() and (repo / "app").exists():
            write_text(
                health,
                'import { NextResponse } from "next/server";\n\n'
                "export function GET() {\n"
                '  return NextResponse.json({ ok: true, service: "halo-demo0" });\n'
                "}\n",
            )
            created.append(str(health.relative_to(repo)))
        elif not health.exists():
            # pages router fallback
            api = repo / "pages" / "api" / "health.ts"
            if (repo / "pages").exists():
                write_text(
                    api,
                    'import type { NextApiRequest, NextApiResponse } from "next";\n\n'
                    "export default function handler(_req: NextApiRequest, res: NextApiResponse) {\n"
                    '  res.status(200).json({ ok: true, service: "halo-demo0" });\n'
                    "}\n",
                )
                created.append(str(api.relative_to(repo)))
        merge_gitignore(repo, NEXT_GITIGNORE)
        return {
            "profile": "nextjs-saas",
            "mode": "existing",
            "created": created,
            "health_path": "/api/health",
            "dev_cmd": ["npm", "run", "dev", "--", "-p", "3456"],
            "dev_url": "http://127.0.0.1:3456/api/health",
            "install_cmd": ["npm", "install"],
        }

    # Fresh minimal app
    files: dict[str, str] = {
        "package.json": json.dumps(
            {
                "name": product_name.lower().replace(" ", "-")[:64] or "halo-app",
                "version": "0.1.0",
                "private": True,
                "scripts": {
                    "dev": "next dev",
                    "build": "next build",
                    "start": "next start",
                    "test": "node --test tests/health.test.mjs",
                    "lint": "echo 'no lint configured'",
                },
                "dependencies": {
                    "next": "^15.1.0",
                    "react": "^19.0.0",
                    "react-dom": "^19.0.0",
                },
                "devDependencies": {
                    "typescript": "^5.7.0",
                    "@types/node": "^22.0.0",
                    "@types/react": "^19.0.0",
                    "@types/react-dom": "^19.0.0",
                },
            },
            indent=2,
        )
        + "\n",
        "tsconfig.json": json.dumps(
            {
                "compilerOptions": {
                    "target": "ES2017",
                    "lib": ["dom", "dom.iterable", "esnext"],
                    "allowJs": True,
                    "skipLibCheck": True,
                    "strict": True,
                    "noEmit": True,
                    "esModuleInterop": True,
                    "module": "esnext",
                    "moduleResolution": "bundler",
                    "resolveJsonModule": True,
                    "isolatedModules": True,
                    "jsx": "preserve",
                    "incremental": True,
                    "plugins": [{"name": "next"}],
                    "paths": {"@/*": ["./*"]},
                },
                "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
                "exclude": ["node_modules"],
            },
            indent=2,
        )
        + "\n",
        "next.config.ts": 'import type { NextConfig } from "next";\n\n'
        "const nextConfig: NextConfig = {};\n\nexport default nextConfig;\n",
        "next-env.d.ts": '/// <reference types="next" />\n/// <reference types="next/image-types/global" />\n',
        "app/layout.tsx": "export const metadata = { title: "
        + json.dumps(product_name)
        + ", description: 'Scaffolded by Halo' };\n\n"
        "export default function RootLayout({ children }: { children: React.ReactNode }) {\n"
        "  return (\n"
        '    <html lang="en">\n'
        "      <body style={{ fontFamily: 'system-ui, sans-serif', margin: 0 }}>{children}</body>\n"
        "    </html>\n"
        "  );\n"
        "}\n",
        "app/page.tsx": "export default function Home() {\n"
        "  return (\n"
        '    <main style={{ padding: "3rem", maxWidth: 720, margin: "0 auto" }}>\n'
        f"      <h1>{product_name}</h1>\n"
        "      <p>Demo 0 — scaffolded by Halo. Build loop ships real features next.</p>\n"
        '      <p><a href="/api/health">Health check</a></p>\n'
        "    </main>\n"
        "  );\n"
        "}\n",
        "app/api/health/route.ts": 'import { NextResponse } from "next/server";\n\n'
        "export function GET() {\n"
        '  return NextResponse.json({ ok: true, service: "halo-demo0" });\n'
        "}\n",
        "tests/health.test.mjs": "import test from 'node:test';\nimport assert from 'node:assert/strict';\n\n"
        "test('scaffold marker', () => {\n"
        "  assert.equal(1 + 1, 2);\n"
        "});\n",
        "README.md": f"# {product_name}\n\nScaffolded by **Halo**.  \n\n```bash\nnpm install\nnpm run dev\n```\n\nHealth: `/api/health`\n",
    }

    for rel, content in files.items():
        if write_text(repo / rel, content):
            created.append(rel)

    merge_gitignore(repo, NEXT_GITIGNORE)
    return {
        "profile": "nextjs-saas",
        "mode": "fresh",
        "created": created,
        "health_path": "/api/health",
        "dev_cmd": ["npm", "run", "dev", "--", "-p", "3456"],
        "dev_url": "http://127.0.0.1:3456/api/health",
        "install_cmd": ["npm", "install"],
    }
