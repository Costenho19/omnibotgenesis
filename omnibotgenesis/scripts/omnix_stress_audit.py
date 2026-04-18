#!/usr/bin/env python3
"""
OMNIX Decision Governance — Institutional Security Stress Audit
Automated security validation and performance benchmarking tool.

Measures: Latency (p50/p95/p99), error rates, security header compliance,
and information leakage detection across all dashboard API endpoints.

Usage:
    python scripts/omnix_stress_audit.py [--base-url URL] [--requests N] [--concurrency C] [--duration S]
"""

import os
import sys
import json
import time
import argparse
import statistics
import threading
import re
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from http.cookiejar import CookieJar
from urllib.request import build_opener, HTTPCookieProcessor

ENDPOINTS = [
    {"path": "/api/health", "method": "GET", "auth_required": False, "category": "system"},
    {"path": "/api/core/trades", "method": "GET", "auth_required": True, "category": "core"},
    {"path": "/api/core/performance", "method": "GET", "auth_required": True, "category": "core"},
    {"path": "/api/core/balance", "method": "GET", "auth_required": True, "category": "core"},
    {"path": "/api/core/decisions", "method": "GET", "auth_required": True, "category": "core"},
    {"path": "/api/core/portfolio", "method": "GET", "auth_required": True, "category": "core"},
    {"path": "/api/core/equity_curve", "method": "GET", "auth_required": True, "category": "core"},
    {"path": "/api/core/win_rate_dual", "method": "GET", "auth_required": True, "category": "core"},
    {"path": "/api/core/pnl_breakdown", "method": "GET", "auth_required": True, "category": "core"},
    {"path": "/api/core/drawdown_chart", "method": "GET", "auth_required": True, "category": "core"},
    {"path": "/api/market/btc", "method": "GET", "auth_required": True, "category": "market"},
    {"path": "/api/market/sentiment", "method": "GET", "auth_required": True, "category": "market"},
    {"path": "/api/market/time_heatmap", "method": "GET", "auth_required": True, "category": "market"},
    {"path": "/api/intelligence/shadow", "method": "GET", "auth_required": True, "category": "intelligence"},
    {"path": "/api/intelligence/learning", "method": "GET", "auth_required": True, "category": "intelligence"},
    {"path": "/api/intelligence/regime", "method": "GET", "auth_required": True, "category": "intelligence"},
    {"path": "/api/intelligence/correlation_heatmap", "method": "GET", "auth_required": True, "category": "intelligence"},
    {"path": "/api/intelligence/dci", "method": "GET", "auth_required": True, "category": "intelligence"},
    {"path": "/api/system/version", "method": "GET", "auth_required": True, "category": "system"},
    {"path": "/api/system/quarantine", "method": "GET", "auth_required": True, "category": "system"},
]

REQUIRED_SECURITY_HEADERS = [
    "X-Content-Type-Options",
    "X-Frame-Options",
    "X-XSS-Protection",
    "Referrer-Policy",
    "Permissions-Policy",
    "Strict-Transport-Security",
    "Content-Security-Policy",
    "X-Request-ID",
    "Cache-Control",
]

FORBIDDEN_HEADERS = [
    "X-Powered-By",
]

INFO_LEAK_PATTERNS = [
    re.compile(r'Traceback \(most recent call last\)', re.IGNORECASE),
    re.compile(r'File "/.*?", line \d+'),
    re.compile(r'KeyError|AttributeError|TypeError|ValueError|ImportError', re.IGNORECASE),
    re.compile(r'sk-[a-zA-Z0-9]{20,}'),
    re.compile(r'AIza[a-zA-Z0-9_-]{35}'),
    re.compile(r'\d{8,}:[A-Za-z0-9_-]{35}'),
    re.compile(r'ghp_[a-zA-Z0-9]{36}'),
    re.compile(r'postgres://[^\s]+'),
    re.compile(r'redis://[^\s]+'),
    re.compile(r'mongodb://[^\s]+'),
    re.compile(r'/home/runner/'),
    re.compile(r'/app/[a-zA-Z]'),
    re.compile(r'TELEGRAM_BOT_TOKEN|OPENAI_API_KEY|DATABASE_URL|SESSION_SECRET', re.IGNORECASE),
    re.compile(r'Werkzeug|werkzeug'),
]


class StressAuditor:
    def __init__(self, base_url, total_requests, concurrency, duration):
        self.base_url = base_url.rstrip('/')
        self.total_requests = total_requests
        self.concurrency = concurrency
        self.duration = duration
        self.results = {}
        self.session_cookie = None
        self.lock = threading.Lock()
        self.start_time = None

    def _create_opener(self):
        cj = CookieJar()
        opener = build_opener(HTTPCookieProcessor(cj))
        try:
            opener.open(f"{self.base_url}/terminal")
        except Exception:
            pass
        return opener

    def _make_request(self, opener, path):
        url = f"{self.base_url}{path}"
        start = time.monotonic()
        try:
            req = Request(url, method='GET')
            resp = opener.open(req, timeout=15)
            elapsed = (time.monotonic() - start) * 1000
            body = resp.read().decode('utf-8', errors='replace')
            headers = dict(resp.headers)
            status = resp.status
            return {
                "status": status,
                "latency_ms": round(elapsed, 2),
                "body": body,
                "headers": headers,
                "error": None
            }
        except HTTPError as e:
            elapsed = (time.monotonic() - start) * 1000
            body = ""
            try:
                body = e.read().decode('utf-8', errors='replace')
            except Exception:
                pass
            return {
                "status": e.code,
                "latency_ms": round(elapsed, 2),
                "body": body,
                "headers": dict(e.headers) if hasattr(e, 'headers') else {},
                "error": None
            }
        except Exception as e:
            elapsed = (time.monotonic() - start) * 1000
            return {
                "status": 0,
                "latency_ms": round(elapsed, 2),
                "body": "",
                "headers": {},
                "error": str(type(e).__name__)
            }

    def check_security_headers(self, headers):
        findings = {"present": [], "missing": [], "forbidden_present": []}
        for h in REQUIRED_SECURITY_HEADERS:
            found = any(k.lower() == h.lower() for k in headers.keys())
            if found:
                findings["present"].append(h)
            else:
                findings["missing"].append(h)
        for h in FORBIDDEN_HEADERS:
            found = any(k.lower() == h.lower() for k in headers.keys())
            if found:
                findings["forbidden_present"].append(h)
        server_header = headers.get("Server", headers.get("server", ""))
        if "werkzeug" in server_header.lower() or "python" in server_header.lower():
            findings["forbidden_present"].append(f"Server: {server_header} (version fingerprinting)")
        return findings

    def check_info_leakage(self, body, status_code):
        leaks = []
        if status_code >= 400:
            for pattern in INFO_LEAK_PATTERNS:
                matches = pattern.findall(body)
                if matches:
                    leaks.append({
                        "pattern": pattern.pattern[:60],
                        "matches": len(matches),
                        "sample": matches[0][:50] if matches else ""
                    })
        return leaks

    def run_endpoint_audit(self, endpoint, opener):
        path = endpoint["path"]
        results = []
        requests_sent = 0
        deadline = time.monotonic() + self.duration
        per_endpoint_max = max(self.total_requests // len(ENDPOINTS), 50)

        while requests_sent < per_endpoint_max and time.monotonic() < deadline:
            result = self._make_request(opener, path)
            results.append(result)
            requests_sent += 1

        return path, results

    def run_stress_test(self):
        print(f"\n{'='*70}")
        print(f"  OMNIX Decision Governance — Institutional Security Stress Audit")
        print(f"  Target: {self.base_url}")
        print(f"  Config: {self.total_requests} requests, concurrency {self.concurrency}, {self.duration}s max")
        print(f"  Timestamp: {datetime.now(timezone.utc).isoformat()}")
        print(f"{'='*70}\n")

        opener = self._create_opener()
        print("[1/4] Establishing session...")

        try:
            resp = opener.open(f"{self.base_url}/api/health", timeout=10)
            print(f"  Health check: {resp.status} OK\n")
        except Exception as e:
            print(f"  Health check FAILED: {type(e).__name__}")
            print("  Cannot proceed — server not reachable.\n")
            return None

        print("[2/4] Running security header audit...")
        header_results = {}
        for ep in ENDPOINTS:
            result = self._make_request(opener, ep["path"])
            header_check = self.check_security_headers(result["headers"])
            leak_check = self.check_info_leakage(result["body"], result["status"])
            header_results[ep["path"]] = {
                "status": result["status"],
                "headers": header_check,
                "info_leakage": leak_check,
                "latency_ms": result["latency_ms"]
            }
            status_icon = "✓" if result["status"] in (200, 302, 503) else "✗"
            leak_icon = "✓" if not leak_check else f"✗ ({len(leak_check)} leaks)"
            missing_ct = len(header_check["missing"])
            hdr_icon = "✓" if missing_ct == 0 else f"✗ ({missing_ct} missing)"
            print(f"  {status_icon} {ep['path']:<45} HTTP {result['status']}  Headers: {hdr_icon}  Leaks: {leak_icon}")

        print(f"\n[3/4] Running latency stress test ({self.total_requests} requests, {self.concurrency} concurrent)...")
        latency_results = {}
        self.start_time = time.monotonic()

        with ThreadPoolExecutor(max_workers=self.concurrency) as pool:
            futures = {}
            for ep in ENDPOINTS:
                future = pool.submit(self.run_endpoint_audit, ep, opener)
                futures[future] = ep["path"]

            for future in as_completed(futures):
                path, results = future.result()
                latencies = [r["latency_ms"] for r in results if r["status"] > 0]
                errors = [r for r in results if r["status"] == 0 or r["status"] >= 500]
                statuses = {}
                for r in results:
                    s = str(r["status"])
                    statuses[s] = statuses.get(s, 0) + 1

                if latencies:
                    latencies_sorted = sorted(latencies)
                    n = len(latencies_sorted)
                    latency_results[path] = {
                        "requests": len(results),
                        "p50": round(latencies_sorted[int(n * 0.50)], 2),
                        "p95": round(latencies_sorted[int(n * 0.95)], 2),
                        "p99": round(latencies_sorted[min(int(n * 0.99), n-1)], 2),
                        "min": round(min(latencies), 2),
                        "max": round(max(latencies), 2),
                        "mean": round(statistics.mean(latencies), 2),
                        "error_count": len(errors),
                        "error_rate": round(len(errors) / len(results) * 100, 2),
                        "status_codes": statuses
                    }
                else:
                    latency_results[path] = {
                        "requests": len(results),
                        "p50": 0, "p95": 0, "p99": 0,
                        "min": 0, "max": 0, "mean": 0,
                        "error_count": len(results),
                        "error_rate": 100.0,
                        "status_codes": statuses
                    }

        total_elapsed = round(time.monotonic() - self.start_time, 2)
        total_reqs = sum(r["requests"] for r in latency_results.values())
        total_errors = sum(r["error_count"] for r in latency_results.values())
        all_latencies = []
        for path, data in latency_results.items():
            pass

        print(f"\n  Completed: {total_reqs} requests in {total_elapsed}s")
        print(f"  Throughput: {round(total_reqs / max(total_elapsed, 0.1), 1)} req/s")
        print(f"  Errors: {total_errors} ({round(total_errors / max(total_reqs, 1) * 100, 2)}%)\n")

        print(f"  {'Endpoint':<45} {'Reqs':>5} {'p50':>8} {'p95':>8} {'p99':>8} {'Err%':>6}")
        print(f"  {'-'*85}")
        for path in sorted(latency_results.keys()):
            d = latency_results[path]
            print(f"  {path:<45} {d['requests']:>5} {d['p50']:>7.1f}ms {d['p95']:>7.1f}ms {d['p99']:>7.1f}ms {d['error_rate']:>5.1f}%")

        print(f"\n[4/4] Generating audit report...")

        all_leaks = []
        for path, data in header_results.items():
            for leak in data["info_leakage"]:
                all_leaks.append({"endpoint": path, **leak})

        all_missing_headers = set()
        all_forbidden = set()
        for path, data in header_results.items():
            for h in data["headers"]["missing"]:
                all_missing_headers.add(h)
            for h in data["headers"]["forbidden_present"]:
                all_forbidden.add(h)

        report = {
            "audit_metadata": {
                "tool": "OMNIX Institutional Security Stress Audit",
                "version": "1.0",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "target": self.base_url,
                "config": {
                    "total_requests": self.total_requests,
                    "concurrency": self.concurrency,
                    "duration_limit_s": self.duration,
                    "actual_duration_s": total_elapsed
                }
            },
            "summary": {
                "endpoints_tested": len(ENDPOINTS),
                "total_requests": total_reqs,
                "total_errors": total_errors,
                "overall_error_rate": round(total_errors / max(total_reqs, 1) * 100, 2),
                "throughput_rps": round(total_reqs / max(total_elapsed, 0.1), 1),
                "security_headers_compliant": len(all_missing_headers) == 0,
                "missing_headers": list(all_missing_headers),
                "forbidden_headers_present": list(all_forbidden),
                "info_leaks_found": len(all_leaks),
                "info_leak_details": all_leaks,
                "verdict": "PASS" if len(all_leaks) == 0 and len(all_missing_headers) <= 1 else "NEEDS_REVIEW"
            },
            "header_audit": header_results,
            "latency_audit": latency_results
        }

        os.makedirs("output", exist_ok=True)
        with open("output/stress_results.json", "w") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"  Results saved: output/stress_results.json")

        self._generate_summary_md(report)
        print(f"  Summary saved: output/stress_summary.md")

        verdict = report["summary"]["verdict"]
        leaks = report["summary"]["info_leaks_found"]
        missing = len(report["summary"]["missing_headers"])
        forbidden = len(report["summary"]["forbidden_headers_present"])

        print(f"\n{'='*70}")
        print(f"  AUDIT VERDICT: {verdict}")
        print(f"  Security Headers: {9 - missing}/9 compliant" + (f" ({missing} missing on some endpoints)" if missing else ""))
        if forbidden:
            print(f"  Forbidden Headers: {forbidden} detected (info fingerprinting risk)")
        print(f"  Information Leakage: {'NONE DETECTED' if leaks == 0 else f'{leaks} LEAKS FOUND'}")
        print(f"  Error Rate: {report['summary']['overall_error_rate']}%")
        print(f"  Throughput: {report['summary']['throughput_rps']} req/s")
        print(f"{'='*70}\n")

        return report

    def _generate_summary_md(self, report):
        meta = report["audit_metadata"]
        summary = report["summary"]
        lines = [
            f"# OMNIX Security Stress Audit — Summary Report",
            f"",
            f"**Generated**: {meta['timestamp']}",
            f"**Target**: {meta['target']}",
            f"**Config**: {meta['config']['total_requests']} requests, {meta['config']['concurrency']} concurrency, {meta['config']['actual_duration_s']}s",
            f"",
            f"## Verdict: {summary['verdict']}",
            f"",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Endpoints Tested | {summary['endpoints_tested']} |",
            f"| Total Requests | {summary['total_requests']} |",
            f"| Overall Error Rate | {summary['overall_error_rate']}% |",
            f"| Throughput | {summary['throughput_rps']} req/s |",
            f"| Security Headers Compliant | {'Yes' if summary['security_headers_compliant'] else 'No'} |",
            f"| Information Leaks | {summary['info_leaks_found']} |",
            f"",
            f"## Security Header Compliance",
            f"",
        ]

        if summary["missing_headers"]:
            lines.append("**Missing on some endpoints:**")
            for h in summary["missing_headers"]:
                lines.append(f"- {h}")
            lines.append("")

        if summary["forbidden_headers_present"]:
            lines.append("**Forbidden headers detected:**")
            for h in summary["forbidden_headers_present"]:
                lines.append(f"- {h}")
            lines.append("")

        if not summary["missing_headers"] and not summary["forbidden_headers_present"]:
            lines.append("All 9 required security headers present. No forbidden headers detected.")
            lines.append("")

        lines.extend([
            f"## Latency Percentiles (ms)",
            f"",
            f"| Endpoint | Reqs | p50 | p95 | p99 | Err% |",
            f"|----------|------|-----|-----|-----|------|",
        ])

        for path in sorted(report["latency_audit"].keys()):
            d = report["latency_audit"][path]
            lines.append(f"| {path} | {d['requests']} | {d['p50']} | {d['p95']} | {d['p99']} | {d['error_rate']}% |")

        lines.extend(["", "## Information Leakage Scan", ""])
        if summary["info_leaks_found"] == 0:
            lines.append("No information leakage detected across all tested endpoints.")
        else:
            lines.append(f"**{summary['info_leaks_found']} potential leaks found:**")
            lines.append("")
            lines.append("| Endpoint | Pattern | Matches |")
            lines.append("|----------|---------|---------|")
            for leak in summary["info_leak_details"]:
                lines.append(f"| {leak['endpoint']} | `{leak['pattern'][:40]}` | {leak['matches']} |")

        lines.extend([
            "",
            "## Endpoints Status",
            "",
            "| Endpoint | HTTP Status | Category |",
            "|----------|-------------|----------|",
        ])
        for path in sorted(report["header_audit"].keys()):
            d = report["header_audit"][path]
            ep = next((e for e in ENDPOINTS if e["path"] == path), {})
            status_label = {200: "OK", 302: "Redirect (auth)", 503: "Service Unavailable (expected)"}.get(d["status"], str(d["status"]))
            lines.append(f"| {path} | {d['status']} ({status_label}) | {ep.get('category', 'unknown')} |")

        lines.extend(["", f"---", f"*OMNIX Decision Governance — Automated Security Audit Tool v1.0*"])

        with open("output/stress_summary.md", "w") as f:
            f.write("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description="OMNIX Institutional Security Stress Audit")
    parser.add_argument("--base-url", default="http://localhost:5000", help="Base URL of the dashboard")
    parser.add_argument("--requests", type=int, default=2000, help="Total requests to send")
    parser.add_argument("--concurrency", type=int, default=50, help="Concurrent workers")
    parser.add_argument("--duration", type=int, default=30, help="Max duration in seconds")
    args = parser.parse_args()

    auditor = StressAuditor(args.base_url, args.requests, args.concurrency, args.duration)
    report = auditor.run_stress_test()

    if report:
        sys.exit(0 if report["summary"]["info_leaks_found"] == 0 else 1)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()
