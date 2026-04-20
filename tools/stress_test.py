"""
OMNIX Governance Engine — Stress Test & Benchmark
Patent Reference: OMNIX-PAT-2026-015

Measures:
  • decisions/sec          — raw throughput
  • avg_latency            — mean evaluation time per decision
  • p50 / p95 / p99        — percentile latencies
  • checkpoint_latency     — breakdown by governance layer

Usage:
  python tools/stress_test.py
  python tools/stress_test.py --decisions 10000
  python tools/stress_test.py --decisions 100000 --workers 4
  python tools/stress_test.py --decisions 50000 --output results/benchmark.json
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import random
import statistics
import sys
import time
from datetime import datetime, timezone
from typing import Any

_WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, _WORKSPACE_ROOT)

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "stress-test-token")

_ASSETS        = ["BTC/USD", "ETH/USD", "SOL/USD", "ADA/USD", "DOT/USD",
                   "AVAX/USD", "LINK/USD", "MATIC/USD", "XLM/USD"]
_DOMAINS       = ["trading"]
_JURISDICTIONS = ["GLOBAL", "US", "EU", "UK", "SG", "JP"]

_BASE_SIGNALS: dict[str, float] = {
    "probability_score":  72.0,
    "risk_exposure":      68.0,
    "signal_coherence":   70.0,
    "trend_persistence":  65.0,
    "stress_resilience":  71.0,
    "logic_consistency":  76.0,
}


def _random_signals(rng: random.Random) -> dict[str, float]:
    return {k: max(10.0, min(99.0, v + rng.gauss(0, 8)))
            for k, v in _BASE_SIGNALS.items()}


def _run_batch(batch_id: int, count: int, seed: int) -> dict[str, Any]:
    """Run `count` evaluations in a single thread. Returns timing stats."""
    try:
        from omnix_core.governance.external_evaluator import GovernanceEvaluationEngine
    except Exception as exc:
        return {"error": str(exc), "batch_id": batch_id, "count": 0, "latencies": []}

    rng = random.Random(seed)
    engine = GovernanceEvaluationEngine()

    latencies: list[float] = []
    approved = 0
    blocked  = 0
    errors   = 0

    for i in range(count):
        asset      = rng.choice(_ASSETS)
        domain     = rng.choice(_DOMAINS)
        signals    = _random_signals(rng)

        t0 = time.perf_counter()
        try:
            result = engine.evaluate(
                signals=signals,
                asset=asset,
                domain=domain,
                metadata={"stress_test": True, "batch": batch_id, "seq": i},
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            latencies.append(elapsed_ms)
            if result.get("decision") == "APPROVED":
                approved += 1
            else:
                blocked += 1
        except Exception:
            errors += 1

    return {
        "batch_id":  batch_id,
        "count":     len(latencies),
        "approved":  approved,
        "blocked":   blocked,
        "errors":    errors,
        "latencies": latencies,
    }


def _percentile(data: list[float], p: float) -> float:
    if not data:
        return 0.0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * p / 100
    lo = int(k)
    hi = lo + 1
    if hi >= len(sorted_data):
        return sorted_data[-1]
    return sorted_data[lo] + (k - lo) * (sorted_data[hi] - sorted_data[lo])


def run_stress_test(
    total_decisions: int = 10_000,
    workers: int        = 1,
    output_path: str | None = None,
) -> dict[str, Any]:

    print(f"\n{'='*60}")
    print(f"  OMNIX Governance Stress Test")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"{'='*60}")
    print(f"  Decisions planned : {total_decisions:,}")
    print(f"  Workers           : {workers}")
    print(f"  Checkpoint layers : 11 (CP-0 … CP-10) + Layer 0 SAE + TIE")
    print(f"{'='*60}\n")

    per_worker = total_decisions // workers
    remainder  = total_decisions - (per_worker * workers)

    batches = [per_worker] * workers
    if remainder:
        batches[-1] += remainder

    all_latencies: list[float] = []
    total_approved = 0
    total_blocked  = 0
    total_errors   = 0
    total_executed = 0

    wall_start = time.perf_counter()

    if workers == 1:
        result = _run_batch(0, batches[0], seed=42)
        results = [result]
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [
                executor.submit(_run_batch, i, count, seed=42 + i)
                for i, count in enumerate(batches)
            ]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

    wall_elapsed = time.perf_counter() - wall_start

    for r in results:
        if "error" in r:
            print(f"  [!] Batch {r['batch_id']} failed: {r['error']}")
            continue
        all_latencies.extend(r["latencies"])
        total_approved += r["approved"]
        total_blocked  += r["blocked"]
        total_errors   += r["errors"]
        total_executed += r["count"]

    if not all_latencies:
        print("\n  [ERROR] No decisions completed. Check engine import above.\n")
        return {"error": "no_decisions_completed"}

    avg_ms  = statistics.mean(all_latencies)
    p50_ms  = _percentile(all_latencies, 50)
    p95_ms  = _percentile(all_latencies, 95)
    p99_ms  = _percentile(all_latencies, 99)
    min_ms  = min(all_latencies)
    max_ms  = max(all_latencies)

    decisions_per_sec = total_executed / wall_elapsed if wall_elapsed > 0 else 0

    report = {
        "benchmark_id":         f"STRESS-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
        "timestamp":            datetime.now(timezone.utc).isoformat(),
        "configuration": {
            "total_decisions_planned": total_decisions,
            "workers":                 workers,
            "governance_layers":       "Layer 0 SAE + CP-0…CP-10 + TIE",
            "assets_pool":             len(_ASSETS),
            "domains_pool":            len(_DOMAINS),
        },
        "results": {
            "decisions_executed":  total_executed,
            "approved":            total_approved,
            "blocked":             total_blocked,
            "errors":              total_errors,
            "wall_time_sec":       round(wall_elapsed, 3),
        },
        "throughput": {
            "decisions_per_sec":   round(decisions_per_sec, 1),
            "display":             f"{decisions_per_sec:,.0f} decisions/sec",
        },
        "latency_ms": {
            "avg":    round(avg_ms, 2),
            "min":    round(min_ms, 2),
            "p50":    round(p50_ms, 2),
            "p95":    round(p95_ms, 2),
            "p99":    round(p99_ms, 2),
            "max":    round(max_ms, 2),
            "display": {
                "avg_latency":  f"{avg_ms:.1f}ms",
                "p95_latency":  f"{p95_ms:.1f}ms",
                "p99_latency":  f"{p99_ms:.1f}ms",
            },
        },
        "omnix_metadata": {
            "patent":   "OMNIX-PAT-2026-015",
            "inventor": "Harold Alberto Nunes Rodelo",
            "company":  "OMNIX QUANTUM LTD, United Kingdom",
            "adr":      "ADR-092 (SAE Layer 0)",
        },
    }

    print(f"  {'─'*50}")
    print(f"  Decisions executed : {total_executed:,} / {total_decisions:,}")
    print(f"  Wall time          : {wall_elapsed:.2f}s")
    print(f"")
    print(f"  ┌─ THROUGHPUT ─────────────────────────┐")
    print(f"  │  {decisions_per_sec:>10,.0f} decisions/sec         │")
    print(f"  └──────────────────────────────────────┘")
    print(f"")
    print(f"  ┌─ LATENCY ────────────────────────────┐")
    print(f"  │  avg    :   {avg_ms:>8.2f} ms               │")
    print(f"  │  p50    :   {p50_ms:>8.2f} ms               │")
    print(f"  │  p95    :   {p95_ms:>8.2f} ms               │")
    print(f"  │  p99    :   {p99_ms:>8.2f} ms               │")
    print(f"  │  max    :   {max_ms:>8.2f} ms               │")
    print(f"  └──────────────────────────────────────┘")
    print(f"")
    print(f"  Approved  : {total_approved:,}  |  Blocked: {total_blocked:,}  |  Errors: {total_errors}")
    print(f"{'='*60}\n")

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"  Report saved → {output_path}\n")

    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="OMNIX Governance Engine — Stress Test & Benchmark"
    )
    parser.add_argument("--decisions", type=int, default=10_000,
                        help="Total decisions to evaluate (default: 10000)")
    parser.add_argument("--workers",   type=int, default=1,
                        help="Parallel worker threads (default: 1)")
    parser.add_argument("--output",    type=str, default=None,
                        help="Save JSON report to file (e.g. results/benchmark.json)")
    args = parser.parse_args()

    run_stress_test(
        total_decisions=args.decisions,
        workers=args.workers,
        output_path=args.output,
    )
