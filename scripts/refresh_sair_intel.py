#!/usr/bin/env python3
"""Refresh SAIR community intel: Zulip message dumps + contributor-network snapshot.

Fetches from zulip.sair.foundation (requires ZULIP_EMAIL + ZULIP_API_KEY) and
server-9527.sair.foundation (public API), appends new Zulip messages to
Blog_data/*.json preserving schema, and writes the SAIR graph snapshot to
cheatsheets/sair_contributor_network_snapshot.json.

Usage:
    # Local (reads .env at repo root):
    python scripts/refresh_sair_intel.py

    # GitHub Actions (env vars injected from secrets):
    ZULIP_EMAIL=... ZULIP_API_KEY=... python scripts/refresh_sair_intel.py

Note: files are (re)written with indent=2 JSON. The first run will reformat
existing Blog_data/*.json files from their historical compact layout; after
that, only actual message additions will diff.
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
CHEATSHEETS_DIR = REPO_ROOT / "cheatsheets"

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

ZULIP_REALM = "https://zulip.sair.foundation"
SAIR_GRAPH_URL = "https://server-9527.sair.foundation/api/contributor-network/graph"
COMPETITION_ID = "mathematics-distillation-challenge-equational-theories-stage1"

# Streams the generic bot (SAIR_project_v02) can read without subscription —
# all three are realm-public (invite_only: false).
STREAMS: dict[int, str] = {
    13: "Math Distillation Challenge - equational theories",
    9: "general",
    18: "17 Prime Scales are the Science of Intelligence",
}

RETRY_DELAYS = [2, 5, 15]
FETCH_WINDOW = 200  # num_before per topic message fetch


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


def topic_to_filename(topic: str) -> str:
    """Convert 'Hard2 dataset' -> 'Hard2_dataset.json' (matches existing convention)."""
    safe = re.sub(r"[^\w\s-]", "", topic).strip()
    safe = re.sub(r"\s+", "_", safe)
    if not safe:
        safe = "untitled"
    return f"{safe}.json"


def load_existing_max_timestamp(file_path: Path) -> int:
    if not file_path.exists():
        return 0
    try:
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"  warning: could not read {file_path.name}: {exc}", file=sys.stderr)
        return 0
    msgs = data.get("messages", [])
    return max((m.get("timestamp", 0) for m in msgs), default=0)


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def refresh_sair_graph() -> bool:
    """Fetch the SAIR contributor-network graph snapshot. Return True if changed."""
    print("=== SAIR contributor-network graph ===")
    response = _request(
        "GET", SAIR_GRAPH_URL,
        params={"competition": COMPETITION_ID},
        timeout=30,
    )
    new_data = response.get("data", {})
    out_path = CHEATSHEETS_DIR / "sair_contributor_network_snapshot.json"

    # Structural diff: ignore fetched_at, compare `data` field
    changed = True
    if out_path.exists():
        try:
            with open(out_path, encoding="utf-8") as f:
                existing = json.load(f)
            if existing.get("data") == new_data:
                changed = False
        except (OSError, json.JSONDecodeError):
            pass

    if changed:
        snapshot = {
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "source_url": f"{SAIR_GRAPH_URL}?competition={COMPETITION_ID}",
            "data": new_data,
        }
        write_json(out_path, snapshot)
        n_entities = len(new_data.get("entities", []))
        n_items = len(new_data.get("items", []))
        n_relations = len(new_data.get("relations", []))
        print(f"  updated: {n_entities} entities, {n_items} items, {n_relations} relations")
    else:
        print("  no changes")
    return changed


def refresh_zulip_stream(
    stream_id: int, stream_name: str, auth: tuple[str, str]
) -> int:
    """Return count of new messages written for this stream."""
    print(f"=== Zulip stream {stream_id} ({stream_name}) ===")
    topics_resp = _request(
        "GET", f"{ZULIP_REALM}/api/v1/users/me/{stream_id}/topics",
        auth=auth, timeout=30,
    )
    topics = topics_resp.get("topics", [])
    print(f"  {len(topics)} topics")

    new_count = 0
    for topic_obj in topics:
        topic_name = topic_obj["name"]
        file_path = BLOG_DATA_DIR / topic_to_filename(topic_name)
        max_ts = load_existing_max_timestamp(file_path)

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

        all_msgs = msgs_resp.get("messages", [])
        new_msgs = [m for m in all_msgs if m.get("timestamp", 0) > max_ts]
        if not new_msgs:
            continue

        new_msgs.sort(key=lambda m: m.get("timestamp", 0))

        if file_path.exists():
            try:
                with open(file_path, encoding="utf-8") as f:
                    data = json.load(f)
            except (OSError, json.JSONDecodeError) as exc:
                print(f"  skip {topic_name!r}: cannot parse existing file: {exc}", file=sys.stderr)
                continue
            data.setdefault("messages", []).extend(new_msgs)
            data["message_count"] = len(data["messages"])
            # Preserve channel/channel_id/topic from existing file
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
        print(f"  + {len(new_msgs)} new in {file_path.name} ({topic_name!r})")

    return new_count


def main() -> int:
    load_dotenv(REPO_ROOT / ".env")
    email = os.environ.get("ZULIP_EMAIL")
    key = os.environ.get("ZULIP_API_KEY")
    if not (email and key):
        print("ERROR: ZULIP_EMAIL and ZULIP_API_KEY must be set (.env or env vars)", file=sys.stderr)
        return 1

    auth = (email, key)

    try:
        refresh_sair_graph()
    except requests.RequestException as exc:
        print(f"ERROR: SAIR graph fetch failed: {exc}", file=sys.stderr)
        return 1

    total_new = 0
    for stream_id, stream_name in STREAMS.items():
        try:
            total_new += refresh_zulip_stream(stream_id, stream_name, auth)
        except requests.RequestException as exc:
            print(f"ERROR: stream {stream_id} failed: {exc}", file=sys.stderr)
            return 1

    print(f"\nTotal: {total_new} new Zulip messages across {len(STREAMS)} streams")
    return 0


if __name__ == "__main__":
    sys.exit(main())
