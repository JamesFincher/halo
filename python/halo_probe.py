#!/usr/bin/env python3
"""Live deploy probe — never share a URL that fails this check."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from typing import Any


def probe(url: str, timeout: float, expect_substring: str | None) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        method="GET",
        headers={"User-Agent": "halo-probe/0.1"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            code = resp.getcode()
            body = resp.read(64_000)
            text = body.decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        code = e.code
        text = e.read(64_000).decode("utf-8", errors="replace") if e.fp else ""
    except Exception as e:  # noqa: BLE001 — probe must never raise to caller
        return {
            "ok": False,
            "url": url,
            "error": str(e),
            "http_code": None,
        }

    ok_code = code in (200, 201, 204, 301, 302, 303, 307, 308)
    ok_sub = True
    if expect_substring:
        ok_sub = expect_substring in text

    return {
        "ok": bool(ok_code and ok_sub),
        "url": url,
        "http_code": code,
        "expect_substring": expect_substring,
        "substring_found": ok_sub if expect_substring else None,
    }


def main() -> None:
    p = argparse.ArgumentParser(prog="halo_probe")
    p.add_argument("--url", required=True)
    p.add_argument("--timeout", type=float, default=15.0)
    p.add_argument("--expect", default=None, help="optional body substring")
    p.add_argument("--json", action="store_true", help="machine output")
    args = p.parse_args()

    result = probe(args.url, args.timeout, args.expect)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        status = "PASS" if result["ok"] else "FAIL"
        print(f"{status} {result.get('http_code')} {args.url}")
        if not result["ok"] and result.get("error"):
            print(result["error"], file=sys.stderr)

    sys.exit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
