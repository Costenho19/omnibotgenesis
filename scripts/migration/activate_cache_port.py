#!/usr/bin/env python3
"""
OMNIX V7.0 - Cache Port Activation Script
==========================================

This script validates and helps activate USE_CACHE_PORT feature flag.

Usage:
    python scripts/migration/activate_cache_port.py --check     # Validate only
    python scripts/migration/activate_cache_port.py --shadow    # Run shadow comparison
    python scripts/migration/activate_cache_port.py --report    # Generate activation report

For Railway activation:
    1. Run --check to verify readiness
    2. Run --shadow to validate behavior
    3. Set USE_CACHE_PORT=true in Railway dashboard
    4. Monitor for 48h
    5. If issues, set USE_CACHE_PORT=false (instant rollback)
"""

import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import time
import json
import logging
from datetime import datetime
from typing import Dict, Any, Tuple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def check_cache_adapter_ready() -> Tuple[bool, Dict[str, Any]]:
    """Check if CacheAdapter is ready for production."""
    results = {
        'timestamp': datetime.utcnow().isoformat(),
        'checks': {},
        'ready': False
    }
    
    try:
        from src.omnix.infrastructure.adapters.cache_adapter import CacheAdapter
        results['checks']['import_adapter'] = {'status': 'PASS', 'message': 'CacheAdapter imported'}
    except ImportError as e:
        results['checks']['import_adapter'] = {'status': 'FAIL', 'message': str(e)}
        return False, results
    
    try:
        from src.omnix.ports.driven.cache_port import CachePort
        results['checks']['import_port'] = {'status': 'PASS', 'message': 'CachePort imported'}
    except ImportError as e:
        results['checks']['import_port'] = {'status': 'FAIL', 'message': str(e)}
        return False, results
    
    adapter = CacheAdapter()
    if isinstance(adapter, CachePort):
        results['checks']['protocol_compliance'] = {'status': 'PASS', 'message': 'Implements CachePort'}
    else:
        results['checks']['protocol_compliance'] = {'status': 'FAIL', 'message': 'Does not implement CachePort'}
        return False, results
    
    if adapter.is_connected():
        results['checks']['redis_connection'] = {'status': 'PASS', 'message': 'Redis connected'}
    else:
        results['checks']['redis_connection'] = {'status': 'WARN', 'message': 'Redis not connected (graceful degradation OK)'}
    
    health = adapter.health_check()
    results['checks']['health_check'] = {
        'status': 'PASS' if health.get('redis_cache_available') else 'WARN',
        'message': 'Health check functional',
        'details': health
    }
    
    required_methods = ['get', 'set', 'delete', 'exists', 'get_json', 'set_json']
    missing = [m for m in required_methods if not hasattr(adapter, m)]
    
    if not missing:
        results['checks']['methods'] = {'status': 'PASS', 'message': 'All methods present'}
    else:
        results['checks']['methods'] = {'status': 'FAIL', 'message': f'Missing: {missing}'}
        return False, results
    
    failed_checks = [k for k, v in results['checks'].items() if v['status'] == 'FAIL']
    results['ready'] = len(failed_checks) == 0
    
    return results['ready'], results


def run_shadow_comparison(iterations: int = 10) -> Dict[str, Any]:
    """Run shadow comparison between CacheAdapter and RedisCache."""
    results = {
        'timestamp': datetime.utcnow().isoformat(),
        'iterations': iterations,
        'operations': [],
        'summary': {}
    }
    
    try:
        from src.omnix.infrastructure.adapters.cache_adapter import CacheAdapter
        from omnix_core.cache.redis_cache import RedisCache
    except ImportError as e:
        results['error'] = str(e)
        return results
    
    adapter = CacheAdapter()
    legacy = RedisCache()
    
    if not legacy.client:
        results['error'] = 'Redis not available for shadow comparison'
        return results
    
    test_prefix = f"omnix:shadow:{int(time.time())}:"
    matches = 0
    mismatches = 0
    
    for i in range(iterations):
        key = f"{test_prefix}{i}"
        value = {"iteration": i, "timestamp": time.time(), "data": f"test_{i}"}
        
        legacy_set = legacy.set(key, value, ttl=60)
        adapter_set = adapter.set(f"{key}_adapter", value, ttl_seconds=60)
        
        legacy_get = legacy.get(key)
        adapter_get = adapter.get(f"{key}_adapter")
        
        legacy_exists = legacy.exists(key)
        adapter_exists = adapter.exists(f"{key}_adapter")
        
        match = (
            legacy_set == adapter_set and
            legacy_get == adapter_get and
            legacy_exists == adapter_exists
        )
        
        if match:
            matches += 1
        else:
            mismatches += 1
            results['operations'].append({
                'iteration': i,
                'key': key,
                'match': False,
                'legacy': {'set': legacy_set, 'get': legacy_get, 'exists': legacy_exists},
                'adapter': {'set': adapter_set, 'get': adapter_get, 'exists': adapter_exists}
            })
        
        legacy.delete(key)
        adapter.delete(f"{key}_adapter")
    
    results['summary'] = {
        'total': iterations,
        'matches': matches,
        'mismatches': mismatches,
        'match_rate': round(matches / iterations * 100, 2),
        'ready': mismatches == 0
    }
    
    return results


def generate_activation_report() -> str:
    """Generate activation readiness report."""
    ready, checks = check_cache_adapter_ready()
    shadow = run_shadow_comparison(iterations=5)
    
    report = []
    report.append("=" * 60)
    report.append("OMNIX V7.0 - Cache Port Activation Report")
    report.append(f"Generated: {datetime.utcnow().isoformat()}")
    report.append("=" * 60)
    report.append("")
    
    report.append("## Readiness Checks")
    report.append("-" * 40)
    for check, result in checks['checks'].items():
        status = result['status']
        icon = "✅" if status == "PASS" else ("⚠️" if status == "WARN" else "❌")
        report.append(f"  {icon} {check}: {result['message']}")
    report.append("")
    
    report.append("## Shadow Mode Comparison")
    report.append("-" * 40)
    if 'error' in shadow:
        report.append(f"  ❌ Error: {shadow['error']}")
    else:
        summary = shadow['summary']
        report.append(f"  Total operations: {summary['total']}")
        report.append(f"  Matches: {summary['matches']}")
        report.append(f"  Mismatches: {summary['mismatches']}")
        report.append(f"  Match rate: {summary['match_rate']}%")
    report.append("")
    
    report.append("## Activation Instructions")
    report.append("-" * 40)
    
    overall_ready = ready and shadow.get('summary', {}).get('ready', False)
    
    if overall_ready:
        report.append("  ✅ READY FOR ACTIVATION")
        report.append("")
        report.append("  To activate in Railway:")
        report.append("  1. Go to Railway dashboard > Variables")
        report.append("  2. Set: USE_CACHE_PORT=true")
        report.append("  3. Redeploy")
        report.append("  4. Monitor logs for 48h")
        report.append("")
        report.append("  To rollback:")
        report.append("  1. Set: USE_CACHE_PORT=false")
        report.append("  2. Redeploy (instant rollback)")
    else:
        report.append("  ❌ NOT READY - Fix issues before activation")
        if not ready:
            failed = [k for k, v in checks['checks'].items() if v['status'] == 'FAIL']
            report.append(f"  Failed checks: {', '.join(failed)}")
        if shadow.get('summary', {}).get('mismatches', 0) > 0:
            report.append(f"  Shadow mismatches: {shadow['summary']['mismatches']}")
    
    report.append("")
    report.append("=" * 60)
    
    return "\n".join(report)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Cache Port Activation Tool')
    parser.add_argument('--check', action='store_true', help='Run readiness checks')
    parser.add_argument('--shadow', action='store_true', help='Run shadow comparison')
    parser.add_argument('--report', action='store_true', help='Generate full report')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    args = parser.parse_args()
    
    if args.check:
        ready, results = check_cache_adapter_ready()
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            status = "READY" if ready else "NOT READY"
            print(f"\n🔍 Cache Port Readiness: {status}\n")
            for check, result in results['checks'].items():
                icon = "✅" if result['status'] == "PASS" else ("⚠️" if result['status'] == "WARN" else "❌")
                print(f"  {icon} {check}: {result['message']}")
        sys.exit(0 if ready else 1)
    
    elif args.shadow:
        results = run_shadow_comparison()
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            summary = results.get('summary', {})
            print(f"\n🔄 Shadow Comparison Results:")
            print(f"  Match rate: {summary.get('match_rate', 0)}%")
            print(f"  Ready: {'YES' if summary.get('ready') else 'NO'}")
        sys.exit(0 if results.get('summary', {}).get('ready') else 1)
    
    elif args.report:
        report = generate_activation_report()
        print(report)
        sys.exit(0)
    
    else:
        report = generate_activation_report()
        print(report)


if __name__ == "__main__":
    main()
