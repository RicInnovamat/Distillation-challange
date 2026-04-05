#!/usr/bin/env python3
"""Refresh SAIR community intel: Zulip threads + contributor-network cheatsheets.

Writes into Blog_data/ with the following layout:

    Blog_data/
    ├── README.md                           (written by this script)
    ├── cheatsheets/
    │   ├── INDEX.md                        (written by this script)
    │   ├── _network_snapshot.json          (graph snapshot)
    │   └── EQT01-*.json                    (one file per public cheatsheet)
    └── zulip/
        ├── INDEX.md                        (written by this script)
        ├── math_distillation_challenge/    (stream 13)
        ├── general/                        (stream 9)
        └── prime_scales/                   (stream 18)

Sources:
- Zulip:   https://zulip.sair.foundation (requires ZULIP_EMAIL + ZULIP_API_KEY)
- SAIR:    https://server-9527.sair.foundation (public, no auth)

Usage:
    # Local (reads .env at repo root):
    python scripts/refresh_sair_intel.py

    # GitHub Actions (env vars from secrets):
    ZULIP_EMAIL=... ZULIP_API_KEY=... python scripts/refresh_sair_intel.py

Files are written with indent=2 JSON for human-reviewable diffs.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
BLOG_DATA_DIR = REPO_ROOT / "Blog_data"
CHEATSHEETS_DIR = BLOG_DATA_DIR / "cheatsheets"
ZULIP_DIR = BLOG_DATA_DIR / "zulip"

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

ZULIP_REALM = "https://zulip.sair.foundation"
SAIR_API = "https://server-9527.sair.foundation"
SAIR_GRAPH_URL = f"{SAIR_API}/api/contributor-network/graph"
SAIR_BY_CODE_URL = f"{SAIR_API}/api/contributor-network/by-code"
COMPETITION_ID = "mathematics-distillation-challenge-equational-theories-stage1"

# Streams the generic bot (SAIR_project_v02) can read without subscription —
# all three are realm-public (invite_only: false).
STREAMS: dict[int, tuple[str, str]] = {
    # channel_id: (channel_name, subdirectory_slug)
    13: ("Math Distillation Challenge - equational theories", "math_distillation_challenge"),
    9:  ("general", "general"),
    18: ("17 Prime Scales are the Science of Intelligence", "prime_scales"),
}

RETRY_DELAYS = [2, 5, 15]
FETCH_WINDOW = 200  # num_before per topic message fetch
API_DELAY = 0.25    # polite pause between requests (seconds)


# ──────────────────────────── HTTP plumbing ────────────────────────────

def _request(method: str, url: str, **kwargs) -> dict:
    """HTTP request with retries on 429/5xx (mirrors eval_harness.py retry shape)."""
    headers = kwargs.pop("headers", {}) or {}
    headers.setdefault("User-Agent", UA)
    kwargs.setdefault("timeout", 60)
    last_exc: Exception | None = None
    for attempt in range(len(RETRY_DELAYS) + 1):
        try:
            r = requests.request(method, url, headers=headers, **kwargs)
            if r.status_code in (429, 500, 502, 503, 504) and attempt < len(RETRY_DELAYS):
                delay = RETRY_DELAYS[attempt]
                print(f"  retry: HTTP {r.status_code}, waiting {delay}s", file=sys.stderr)
                time.sleep(delay)
                continue
            r.raise_for_status()
            return r.json()
        except requests.RequestException as exc:
            last_exc = exc
            if attempt < len(RETRY_DELAYS):
                delay = RETRY_DELAYS[attempt]
                print(f"  retry: {exc}, waiting {delay}s", file=sys.stderr)
                time.sleep(delay)
            else:
                raise
    raise RuntimeError(f"request failed after retries: {last_exc}")


# ──────────────────────────── Filesystem helpers ────────────────────────────

def topic_to_filename(topic: str) -> str:
    """Convert 'Hard2 dataset' -> 'Hard2_dataset.json' (matches existing convention)."""
    safe = re.sub(r"[^\w\s-]", "", topic).strip()
    safe = re.sub(r"\s+", "_", safe)
    if not safe:
        safe = "untitled"
    return f"{safe}.json"


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
        if not content.endswith("\n"):
            f.write("\n")


def load_existing_max_timestamp(file_path: Path) -> int:
    if not file_path.exists():
        return 0
    try:
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"  warning: could not read {file_path.name}: {exc}", file=sys.stderr)
        return 0
    return max((m.get("timestamp", 0) for m in data.get("messages", [])), default=0)


# ──────────────────────────── SAIR contributor-network ────────────────────────────

def _canonical_graph(data: dict) -> dict:
    """Return graph data with server-side volatile fields stripped (meta.generatedAt)."""
    out = {k: v for k, v in data.items() if k != "meta"}
    if "meta" in data and isinstance(data["meta"], dict):
        out["meta"] = {k: v for k, v in data["meta"].items() if k != "generatedAt"}
    return out


def refresh_sair_graph() -> dict | None:
    """Fetch the SAIR contributor-network graph snapshot. Returns the `data` dict
    on success (whether changed or not), or None on failure."""
    print("=== SAIR contributor-network graph ===")
    response = _request("GET", SAIR_GRAPH_URL, params={"competition": COMPETITION_ID}, timeout=30)
    new_data = response.get("data", {})
    out_path = CHEATSHEETS_DIR / "_network_snapshot.json"

    changed = True
    if out_path.exists():
        try:
            with open(out_path, encoding="utf-8") as f:
                existing = json.load(f)
            if _canonical_graph(existing.get("data", {})) == _canonical_graph(new_data):
                changed = False
        except (OSError, json.JSONDecodeError):
            pass

    if changed:
        write_json(out_path, {
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "source_url": f"{SAIR_GRAPH_URL}?competition={COMPETITION_ID}",
            "data": new_data,
        })
        print(f"  updated: {len(new_data.get('entities', []))} entities, "
              f"{len(new_data.get('items', []))} items, "
              f"{len(new_data.get('relations', []))} relations")
    else:
        print("  no changes")
    return new_data


def refresh_cheatsheet_contents(graph_data: dict) -> int:
    """Fetch full content for each public cheatsheet. Returns count updated/new."""
    items = graph_data.get("items", [])
    public_items = [it for it in items if it.get("publicCode")]
    hidden_items = [it for it in items if not it.get("publicCode")]
    print(f"=== Cheatsheet contents: {len(public_items)} public, {len(hidden_items)} hidden ===")

    updated = 0
    for item in public_items:
        code = item["publicCode"]
        time.sleep(API_DELAY)
        try:
            resp = _request("GET", f"{SAIR_BY_CODE_URL}/{code}", timeout=30)
        except requests.RequestException as exc:
            print(f"  skip {code}: {exc}", file=sys.stderr)
            continue
        cs = resp.get("data", {})

        out_path = CHEATSHEETS_DIR / f"{code}.json"
        # Compare stable fields (ignore comment/favorite counts that change often)
        if out_path.exists():
            try:
                with open(out_path, encoding="utf-8") as f:
                    existing = json.load(f).get("data", {})
                if (existing.get("cheatsheetContent") == cs.get("cheatsheetContent")
                    and existing.get("cheatsheetTitle") == cs.get("cheatsheetTitle")
                    and existing.get("remark") == cs.get("remark")):
                    continue
            except (OSError, json.JSONDecodeError):
                pass

        write_json(out_path, {
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "publicCode": code,
            "source_url": f"{SAIR_BY_CODE_URL}/{code}",
            "data": cs,
        })
        updated += 1
        title = cs.get("cheatsheetTitle", "?")
        author = cs.get("entityName", "?")
        print(f"  + {code}: {title!r} by {author}")
    return updated


# ──────────────────────────── Zulip ────────────────────────────

def refresh_zulip_stream(
    stream_id: int, stream_name: str, subdir: str, auth: tuple[str, str]
) -> int:
    print(f"=== Zulip stream {stream_id} ({stream_name}) ===")
    topics_resp = _request(
        "GET", f"{ZULIP_REALM}/api/v1/users/me/{stream_id}/topics",
        auth=auth, timeout=30,
    )
    topics = topics_resp.get("topics", [])
    print(f"  {len(topics)} topics")
    stream_dir = ZULIP_DIR / subdir

    new_count = 0
    for topic_obj in topics:
        topic_name = topic_obj["name"]
        file_path = stream_dir / topic_to_filename(topic_name)
        max_ts = load_existing_max_timestamp(file_path)

        time.sleep(API_DELAY)
        narrow = json.dumps([
            {"operator": "stream", "operand": stream_id},
            {"operator": "topic", "operand": topic_name},
        ])
        try:
            msgs_resp = _request(
                "GET", f"{ZULIP_REALM}/api/v1/messages",
                auth=auth,
                params={
                    "anchor": "newest",
                    "num_before": FETCH_WINDOW,
                    "num_after": 0,
                    "narrow": narrow,
                },
                timeout=60,
            )
        except requests.RequestException as exc:
            print(f"  skip {topic_name!r}: {exc}", file=sys.stderr)
            continue

        new_msgs = [m for m in msgs_resp.get("messages", []) if m.get("timestamp", 0) > max_ts]
        if not new_msgs:
            continue
        new_msgs.sort(key=lambda m: m.get("timestamp", 0))
        new_msgs = [_enrich_message(m) for m in new_msgs]

        if file_path.exists():
            try:
                with open(file_path, encoding="utf-8") as f:
                    data = json.load(f)
            except (OSError, json.JSONDecodeError) as exc:
                print(f"  skip {topic_name!r}: cannot parse existing file: {exc}", file=sys.stderr)
                continue
            data.setdefault("messages", []).extend(new_msgs)
            data["message_count"] = len(data["messages"])
        else:
            data = {
                "channel": stream_name,
                "channel_id": stream_id,
                "topic": topic_name,
                "message_count": len(new_msgs),
                "messages": new_msgs,
            }
        write_json(file_path, data)
        new_count += len(new_msgs)
        print(f"  + {len(new_msgs)} new in {subdir}/{file_path.name} ({topic_name!r})")
    return new_count


# ──────────────────────────── Navigation indexes ────────────────────────────

def _fmt_ts(iso: str | None) -> str:
    if not iso:
        return "—"
    # truncate to date only
    return iso.split("T")[0]


def _count_messages(file_path: Path) -> int:
    try:
        with open(file_path, encoding="utf-8") as f:
            return len(json.load(f).get("messages", []))
    except (OSError, json.JSONDecodeError):
        return 0


def _latest_ts_in_file(file_path: Path) -> str:
    try:
        with open(file_path, encoding="utf-8") as f:
            msgs = json.load(f).get("messages", [])
        if not msgs:
            return "—"
        latest_ts = max((m.get("timestamp", 0) for m in msgs), default=0)
        if not latest_ts:
            return "—"
        return datetime.fromtimestamp(latest_ts, tz=timezone.utc).strftime("%Y-%m-%d")
    except (OSError, json.JSONDecodeError):
        return "—"


def _enrich_message(msg: dict) -> dict:
    """Derive a `date` field from `timestamp` for consistency with legacy files."""
    if "date" not in msg and "timestamp" in msg:
        ts = msg["timestamp"]
        msg["date"] = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    return msg


def regenerate_cheatsheet_index() -> None:
    """Write Blog_data/cheatsheets/INDEX.md from the snapshot + content files."""
    snapshot_file = CHEATSHEETS_DIR / "_network_snapshot.json"
    if not snapshot_file.exists():
        return
    with open(snapshot_file, encoding="utf-8") as f:
        snapshot = json.load(f)
    data = snapshot.get("data", {})
    items = data.get("items", [])
    entities = {e["id"]: e.get("name", "?") for e in data.get("entities", [])}

    public = [it for it in items if it.get("publicCode")]
    public.sort(key=lambda x: (-x.get("favoriteCount", 0), -x.get("referencedCount", 0),
                               x.get("publishedAt", "")))

    lines = [
        "# Community Cheatsheets — Index",
        "",
        f"_Generated from `_network_snapshot.json` (fetched {_fmt_ts(snapshot.get('fetched_at'))}). "
        f"{len(public)} public + {len(items) - len(public)} hidden = {len(items)} total._",
        "",
        f"Source: <https://competition.sair.foundation/contributor-network?competition={COMPETITION_ID}>",
        "",
        "| Public Code | Title | Author | ⭐ | Refs | Published | Content |",
        "|---|---|---|---|---|---|---|",
    ]
    for it in public:
        code = it["publicCode"]
        title = it.get("cheatsheetTitle", "?")
        author = entities.get(it.get("entityId", ""), "?")
        favs = it.get("favoriteCount", 0)
        refs = it.get("referencedCount", 0)
        pub = _fmt_ts(it.get("publishedAt"))
        content_file = f"{code}.json"
        has_file = "✓" if (CHEATSHEETS_DIR / content_file).exists() else "—"
        lines.append(f"| `{code}` | {title} | {author} | {favs} | {refs} | {pub} | "
                     f"[{has_file}]({content_file}) |")
    lines.append("")
    write_text(CHEATSHEETS_DIR / "INDEX.md", "\n".join(lines))


def regenerate_zulip_index() -> None:
    """Write Blog_data/zulip/INDEX.md listing all topics grouped by stream."""
    lines = ["# Zulip Threads — Index", "",
             f"_Generated by `scripts/refresh_sair_intel.py` "
             f"({datetime.now(timezone.utc).strftime('%Y-%m-%d')})._", ""]
    for stream_id, (stream_name, subdir) in STREAMS.items():
        stream_dir = ZULIP_DIR / subdir
        files = sorted(stream_dir.glob("*.json")) if stream_dir.exists() else []
        lines.append(f"## `{subdir}/` — stream {stream_id}: {stream_name}")
        lines.append("")
        if not files:
            lines.append("_(no topics yet)_")
            lines.append("")
            continue
        lines.append("| Topic file | Messages | Latest |")
        lines.append("|---|---|---|")
        for fp in files:
            n = _count_messages(fp)
            latest = _latest_ts_in_file(fp)
            lines.append(f"| [`{fp.name}`]({subdir}/{fp.name}) | {n} | {latest} |")
        lines.append("")
    write_text(ZULIP_DIR / "INDEX.md", "\n".join(lines))


def write_blog_data_readme() -> None:
    readme = """# Blog_data/

Community intelligence for the SAIR Mathematics Distillation Challenge (Stage 1,
Equational Theories). Populated by `scripts/refresh_sair_intel.py` and by the
`SAIR intel refresh` GitHub Actions workflow.

## Layout

```
Blog_data/
├── README.md                       # this file
├── cheatsheets/                    # community cheatsheets (from SAIR contributor network)
│   ├── INDEX.md                    # navigable table of cheatsheets
│   ├── _network_snapshot.json      # graph snapshot (entities, items, relations)
│   └── EQT01-*.json                # full content per public cheatsheet
└── zulip/                          # Zulip thread message dumps
    ├── INDEX.md                    # navigable table of topics
    ├── math_distillation_challenge/  # stream 13
    ├── general/                      # stream  9
    └── prime_scales/                 # stream 18
```

## Sources

- **Contributor network** (public JSON API, no auth):
  `GET https://server-9527.sair.foundation/api/contributor-network/graph?competition=...`
  `GET https://server-9527.sair.foundation/api/contributor-network/by-code/{publicCode}`
- **Zulip** (requires API key; generic bot `SAIR_project_v02`):
  `GET https://zulip.sair.foundation/api/v1/{streams,messages,...}`

## Regenerating

```bash
python scripts/refresh_sair_intel.py
```

Reads `ZULIP_EMAIL` + `ZULIP_API_KEY` from `.env` at the repo root. Idempotent:
new Zulip messages are appended (anchored on `max(timestamp)` per topic file);
cheatsheet content is only rewritten if `cheatsheetContent`/`cheatsheetTitle`/
`remark` differ.
"""
    write_text(BLOG_DATA_DIR / "README.md", readme)


# ──────────────────────────── Main ────────────────────────────

def main() -> int:
    load_dotenv(REPO_ROOT / ".env")
    email = os.environ.get("ZULIP_EMAIL")
    key = os.environ.get("ZULIP_API_KEY")
    if not (email and key):
        print("ERROR: ZULIP_EMAIL and ZULIP_API_KEY must be set (.env or env vars)",
              file=sys.stderr)
        return 1
    auth = (email, key)

    try:
        graph_data = refresh_sair_graph()
    except requests.RequestException as exc:
        print(f"ERROR: SAIR graph fetch failed: {exc}", file=sys.stderr)
        return 1

    cheatsheets_updated = 0
    if graph_data is not None:
        try:
            cheatsheets_updated = refresh_cheatsheet_contents(graph_data)
        except requests.RequestException as exc:
            print(f"ERROR: cheatsheet content fetch failed: {exc}", file=sys.stderr)
            return 1

    total_new_msgs = 0
    for stream_id, (stream_name, subdir) in STREAMS.items():
        try:
            total_new_msgs += refresh_zulip_stream(stream_id, stream_name, subdir, auth)
        except requests.RequestException as exc:
            print(f"ERROR: stream {stream_id} failed: {exc}", file=sys.stderr)
            return 1

    regenerate_cheatsheet_index()
    regenerate_zulip_index()
    write_blog_data_readme()

    print()
    print(f"Total: {cheatsheets_updated} cheatsheets updated, "
          f"{total_new_msgs} new Zulip messages across {len(STREAMS)} streams")
    return 0


if __name__ == "__main__":
    sys.exit(main())
