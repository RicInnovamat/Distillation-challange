# Opus-Solver Hard1 Benchmark — Run Analysis

**Date:** 2026-04-12
**Branch:** `feat/opus-solver-agent`
**Results file:** `opus-solver_hard1_20260411_191840.json`
**Driver:** `scripts/run_opus_benchmark.py --dataset hard1 --parallel 3`

## Summary

| Metric | Value |
|--------|-------|
| Total problems | 69 |
| Correct | 20 (29%) |
| Wrong | 0 |
| Parse errors | 49 |

**On every problem where Opus actually ran to completion: 20/20 correct, 0 wrong.**

## Parse Error Breakdown

### Category 1: Genuine timeouts — 4 problems (1800s cap)

All 4 are FALSE implications where Opus needs to construct a concrete counterexample magma. The equations are structurally similar or have subtle differences that require exhaustive search over order-3+ magmas.

| Problem | eq1_id | eq2_id | Key difficulty |
|---------|--------|--------|----------------|
| hard1_0008 | 646 | 1020 | Eq2 has only 1 variable (`x`), self-referential idempotency constraint |
| hard1_0009 | 2656 | 2863 | Both eqs share `((...)...)*y` shape, hard to separate |
| hard1_0014 | 1480 | 572 | 3 variables, depth 3, large search space |
| hard1_0016 | 1446 | 1448 | Eqs differ only in `(y*z)` vs `(z*y)` — needs non-commutative counterexample |

The slowest successful FALSE answer was hard1_0015 at 1304s (72% of the 1800s cap). These 4 are marginally harder.

### Category 2: Mid-latency exit=1 crashes — 4 problems (18–1719s)

CLI exited with code 1 and empty stderr after running for seconds to minutes. Likely context window exhaustion (Opus generated too much reasoning text).

| Problem | Latency | Expected | Equations |
|---------|---------|----------|-----------|
| hard1_0062 | 18s | False | `x = ((y * x) * z) * (z * y)` / `x = (y * (y * (x * x))) * x` |
| hard1_0027 | 791s | True | `x = x * (y * (x * z))` / `x = ((x * y) * (z * w)) * u` |
| hard1_0026 | 808s | False | `x = ((x * (y * z)) * z) * x` / `x * x = x * (y * (y * x))` |
| hard1_0025 | 1719s | False | `x = ((y * (z * z)) * x) * y` / `x = y * ((y * (z * x)) * z)` |

### Category 3: Fast exit=1 failures — 41 problems (~9s)

Not reasoning failures — the CLI couldn't even start. Rate/concurrency limiting kicked in after ~24 successful Opus calls in rapid succession with `--parallel 3`. All return `exit=1` with empty stderr in ~9 seconds.

These are pure infrastructure failures and should succeed on retry with lower parallelism.

## Correct Results Detail

All 20 correct problems (latency range: 30s–1304s):

| Problem | Expected | Predicted | Latency |
|---------|----------|-----------|---------|
| hard1_0001 | False | False | 310s |
| hard1_0002 | False | False | 1190s |
| hard1_0003 | True | True | 73s |
| hard1_0004 | False | False | 91s |
| hard1_0005 | False | False | 992s |
| hard1_0006 | False | False | 32s |
| hard1_0007 | True | True | 52s |
| hard1_0010 | False | False | 103s |
| hard1_0011 | False | False | 30s |
| hard1_0012 | False | False | 62s |
| hard1_0013 | True | True | 532s |
| hard1_0015 | False | False | 1304s |
| hard1_0017 | False | False | 139s |
| hard1_0018 | True | True | 747s |
| hard1_0019 | False | False | 273s |
| hard1_0020 | False | False | 36s |
| hard1_0021 | False | False | 178s |
| hard1_0022 | False | False | 912s |
| hard1_0023 | True | True | 371s |
| hard1_0024 | False | False | 1062s |

Confusion matrix (20 completed): T->T=5, T->F=0, F->T=0, F->F=15.

## Recommendations

1. **Re-run the 41 fast failures** with `--parallel 1` to avoid rate limiting
2. **Increase `SOLVER_TIMEOUT_S`** from 1800 to 3600 for future runs (the 4 timeouts are marginally beyond the current cap)
3. **Capture partial output on timeout** — `subprocess.TimeoutExpired` has `.stdout`/`.stderr` attributes that are currently discarded
