# Blog_data/

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
