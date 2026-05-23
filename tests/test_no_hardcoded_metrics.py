"""
OMNIX Real-Data Integrity Test — Anti-Regression Scanner

Scans all Python source files for suspicious patterns that indicate
hardcoded/fabricated metrics. If this test fails, it means someone
introduced a static value that could be shown to users as if it were
real data.

Policy: "todo real, nada inventado"
Created: February 24, 2026
"""

import os
import re
import ast
import pytest


SOURCE_DIRS = [
    'omnix_core',
    'omnix_services',
    'omnix_dashboard',
]

EXCLUDED_FILES = {
    'conftest.py',
    'test_',
    'data_integrity.py',
    '__pycache__',
}

EXCLUDED_PATHS = {
    'omnix_core/quantum/physics_validator.py',
    'omnix_core/quantum/testing_framework.py',
    'omnix_core/quantum/enhancements.py',
    'omnix_core/config/trading_profiles.py',
    # Vertical governance simulators — use random distributions INTENTIONALLY
    # to produce statistically realistic governance scenarios for demo/testing.
    # These are simulation engines, not production data sources.
    'omnix_core/stablecoin/stablecoin_simulator.py',
    'omnix_core/credit/credit_simulator.py',
    'omnix_core/insurance/insurance_simulator.py',
    'omnix_core/robotics/robotics_simulator.py',
    'omnix_core/medical/medical_simulator.py',
    'omnix_core/energy/energy_simulator.py',
    'omnix_core/real_estate/real_estate_simulator.py',
    'omnix_core/agents/agents_simulator.py',
    'omnix_services/trading_service/advanced_features.py',
    'omnix_services/trading_service/kelly_criterion.py',
    'omnix_services/trading_service/kalman_filter.py',
    'omnix_services/execution_service/execution_protocol.py',
    'omnix_services/execution_service/liquidity_analyzer.py',
    'omnix_services/optimization/auto_optimizer.py',
    'omnix_services/optimization/adaptive_weights.py',
    'omnix_services/derivatives/margin_engine.py',
    'omnix_services/derivatives/hedging_service.py',
    'omnix_services/analytics/chart_patterns.py',
    'omnix_services/analytics/volume_profile.py',
    'omnix_services/stock_trading/premium/modules/kalman_filter.py',
    'omnix_services/risk_management/memory_risk_adapter.py',
    'omnix_services/ai_service/ai_service.py',
    'omnix_services/ai_service/ai_models.py',
    'omnix_services/ai_service/conversational_ai_adapter.py',
    'omnix_services/ai_service/conversational_brain.py',
    'omnix_dashboard/gunicorn.conf.py',
    'omnix_dashboard/static/',
    'omnix_dashboard/templates/',
    'omnix_core/bot/auto_trading_bot.py',
    'omnix_core/defense/defense_simulator.py',
    'omnix_services/market_data/validators.py',
    'omnix_services/market_data/latency_monitor.py',
    'omnix_services/portfolio_management/',
    'omnix_services/build/',
    'omnix_core/build/',
    'omnix_services/analytics/institutional_report.py',
    'examples/',
}

SUSPICIOUS_PATTERNS = [
    (
        r"(?:prediction_accuracy|ai_confidence|success_rate|veto_accuracy)\s*[=:]\s*0\.\d+",
        "Hardcoded accuracy/confidence metric"
    ),
    (
        r"(?:win_rate|winrate)\s*[=:]\s*(?:5[0-9]|6[0-9]|7[0-9]|8[0-9]|9[0-9])\.?\d*(?!\s*[%])",
        "Hardcoded win rate value"
    ),
    (
        r"data_fidelity\s*=\s*0\.\d+",
        "Hardcoded data fidelity"
    ),
    (
        r"(?:correlation_score|narrative_coherence|narrative_strength)\s*[=:]\s*0\.\d+",
        "Hardcoded correlation/narrative score"
    ),
    (
        r"(?:btc_eth_correlation|btc_gold_correlation|btc_sp500_correlation)\s*[=:]\s*0\.\d+",
        "Hardcoded market correlation"
    ),
    (
        r"order_book_depth\s*=\s*0\.\d+",
        "Hardcoded order book depth"
    ),
    (
        r"bid_ask_spread\s*=\s*0\.\d+",
        "Hardcoded bid-ask spread"
    ),
    (
        r"market_impact\s*=\s*0\.\d+",
        "Hardcoded market impact"
    ),
    (
        r"fear_greed_index['\"]?\s*[=:]\s*\d{2,3}",
        "Hardcoded Fear & Greed Index"
    ),
    (
        r"sentiment_score['\"]?\s*[=:]\s*\d+\.\d+",
        "Hardcoded sentiment score"
    ),
    (
        r"iterations\s*=\s*1[05]\d{4}",
        "Claimed iteration count (verify it's real)"
    ),
    (
        r"(?:api_calls_today|api_calls)\s*[=:]\s*\d{2,4}(?!\s*[+\-*/])",
        "Hardcoded API call count"
    ),
    (
        r"(?:cpu_efficiency|response_optimization|learning_rate)\s*[=:]\s*0\.\d+",
        "Hardcoded system performance metric"
    ),
    (
        r"volatility\s*=\s*0\.0[12345]\d*\s",
        "Hardcoded volatility value"
    ),
    (
        r"momentum_score\s*[=:]\s*0\.\d+",
        "Hardcoded momentum score"
    ),
    (
        r"regime_accuracy['\"]?\s*[=:]\s*0\.\d+",
        "Hardcoded regime accuracy"
    ),
    (
        r"signal_quality['\"]?\s*[=:]\s*0\.\d+",
        "Hardcoded signal quality"
    ),
    (
        r"calibration_success_rate['\"]?\s*[=:]\s*0\.\d+",
        "Hardcoded calibration success rate"
    ),
    (
        r"\.get\(['\"]price['\"],\s*\d{4,6}\)",
        "Fallback price in .get() default — use None instead"
    ),
    (
        r"\.get\(['\"]change['\"],\s*\d+\.?\d*\)",
        "Fallback change% in .get() default — use None instead"
    ),
    (
        r"['\"]BTC['\"]\s*:\s*9[0-9]{4}|['\"]ETH['\"]\s*:\s*3[0-9]{3}",
        "Hardcoded crypto price (BTC/ETH) — use real API data"
    ),
    (
        r"source['\"]?\s*:\s*['\"](?:Estimado|Fallback)['\"]",
        "Data source marked as estimated/fallback — must use real source"
    ),
]

SYNTHETIC_DATA_PATTERNS = [
    (
        r"np\.random\.(normal|uniform|randint|random|seed)",
        "numpy random in runtime code — synthetic data generation"
    ),
    (
        r"random\.(?:random|uniform|gauss|normalvariate)\(",
        "Python random in runtime code — synthetic data generation"
    ),
]

CONTEXT_SAFE_PATTERNS = [
    r'temperature\s*=',
    r'top_p\s*=',
    r'top_k\s*=',
    r'#.*hardcod',
    r'#.*fallback',
    r'#.*default',
    r'THRESHOLD',
    r'threshold',
    r'_THRESHOLD',
    r'MIN_',
    r'MAX_',
    r'min_',
    r'max_',
    r'\.get\(',
    r'if\s+.*[<>=]',
    r'elif\s+.*[<>=]',
    r'assert',
    r'test_',
    r'__main__',
]


def _should_exclude(filepath):
    for exc in EXCLUDED_FILES:
        if exc in os.path.basename(filepath):
            return True
    for exc_path in EXCLUDED_PATHS:
        normalized = filepath.replace('\\', '/')
        if exc_path in normalized:
            return True
    return False


_main_block_cache = {}

def _get_main_block_lines(filepath):
    """Pre-compute which lines are inside __main__ blocks (cached per file)"""
    if filepath in _main_block_cache:
        return _main_block_cache[filepath]
    
    main_lines = set()
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        in_main = False
        main_indent = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('if __name__') and '__main__' in stripped:
                in_main = True
                main_indent = len(line) - len(line.lstrip())
                main_lines.add(i + 1)
                continue
            if in_main:
                if stripped and not stripped.startswith('#'):
                    current_indent = len(line) - len(line.lstrip())
                    if current_indent <= main_indent and not line[main_indent:main_indent+1].isspace():
                        if stripped.startswith(('def ', 'class ')) or (not stripped.startswith(('def ', 'class ')) and current_indent == 0 and i > 0):
                            in_main = False
                            continue
                main_lines.add(i + 1)
    except Exception:
        pass
    
    _main_block_cache[filepath] = main_lines
    return main_lines


def _is_in_main_block(filepath, line_number):
    return line_number in _get_main_block_lines(filepath)


def _is_context_safe(line):
    for safe in CONTEXT_SAFE_PATTERNS:
        if re.search(safe, line):
            return True
    return False


def _collect_python_files():
    files = []
    for source_dir in SOURCE_DIRS:
        if not os.path.isdir(source_dir):
            continue
        for root, dirs, filenames in os.walk(source_dir):
            dirs[:] = [d for d in dirs if d != '__pycache__']
            for fn in filenames:
                if fn.endswith('.py'):
                    filepath = os.path.join(root, fn)
                    if not _should_exclude(filepath):
                        files.append(filepath)
    return files


def _scan_file(filepath):
    violations = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except Exception:
        return violations

    for line_num, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue

        if _is_context_safe(stripped):
            continue

        if _is_in_main_block(filepath, line_num):
            continue

        for pattern, description in SUSPICIOUS_PATTERNS:
            if re.search(pattern, stripped):
                violations.append({
                    'file': filepath,
                    'line': line_num,
                    'content': stripped[:120],
                    'pattern': description
                })

    return violations


class TestNoHardcodedMetrics:
    """Anti-regression: scan for hardcoded metrics in production code"""

    def test_no_hardcoded_metrics_in_source(self):
        """Scan all source files for suspicious hardcoded metric patterns"""
        all_violations = []
        files = _collect_python_files()

        assert len(files) > 10, f"Expected to scan >10 files, found {len(files)}"

        for filepath in files:
            violations = _scan_file(filepath)
            all_violations.extend(violations)

        if all_violations:
            report = "\n\nHARDCODED METRICS DETECTED:\n"
            report += "=" * 60 + "\n"
            for v in all_violations:
                report += f"\n  File: {v['file']}:{v['line']}\n"
                report += f"  Type: {v['pattern']}\n"
                report += f"  Code: {v['content']}\n"
            report += f"\n{'=' * 60}"
            report += f"\nTotal violations: {len(all_violations)}"
            report += "\n\nPolicy: 'todo real, nada inventado'"
            report += "\nFix: Replace with real DB query or return 'Insufficient real data'"

            pytest.fail(report)

    def test_no_fabricated_fallback_values(self):
        """Check that except/fallback blocks don't return hardcoded numeric values"""
        files = _collect_python_files()
        violations = []

        fallback_patterns = [
            (r"return\s*\{.*['\"](?:probability|confidence|accuracy|score)['\"].*:\s*0\.\d+", "Fallback returns hardcoded metric"),
            (r"return\s*\{.*['\"](?:win_rate|success_rate)['\"].*:\s*\d+\.?\d*", "Fallback returns hardcoded rate"),
        ]

        for filepath in files:
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    lines = content.split('\n')
            except Exception:
                continue

            in_except = False
            for line_num, line in enumerate(lines, 1):
                stripped = line.strip()
                if stripped.startswith('except'):
                    in_except = True
                    continue
                if in_except and stripped and not stripped.startswith('#'):
                    indent_current = len(line) - len(line.lstrip())
                    if indent_current == 0 or (stripped.startswith('def ') or stripped.startswith('class ')):
                        in_except = False
                        continue

                    for pattern, desc in fallback_patterns:
                        if re.search(pattern, stripped):
                            if not _is_in_main_block(filepath, line_num):
                                violations.append({
                                    'file': filepath,
                                    'line': line_num,
                                    'content': stripped[:120],
                                    'pattern': desc
                                })

        if violations:
            report = "\n\nFABRICATED FALLBACK VALUES DETECTED:\n"
            report += "=" * 60 + "\n"
            for v in violations:
                report += f"\n  File: {v['file']}:{v['line']}\n"
                report += f"  Type: {v['pattern']}\n"
                report += f"  Code: {v['content']}\n"
            report += f"\n{'=' * 60}"
            report += f"\nTotal violations: {len(violations)}"
            report += "\n\nFix: Return {'status': 'insufficient_data'} instead of hardcoded values"

            pytest.fail(report)

    def test_no_synthetic_data_in_runtime(self):
        """Scan runtime code for numpy/random synthetic data generation"""
        files = _collect_python_files()
        violations = []

        synthetic_safe_paths = {
            'omnix_services/trading_service/monte_carlo.py',
            'omnix_services/trading_service/advanced_features.py',
            'omnix_services/stock_trading/premium/modules/monte_carlo.py',
            'omnix_services/stock_trading/premium/stock_auto_optimizer.py',
            'omnix_services/trading_service/backtesting_engine.py',
            'omnix_services/analytics/institutional_report.py',
            'omnix_services/ai_service/video/analyzer.py',
            'omnix_services/ai_service/ai_models.py',
            'omnix_services/optimization/auto_optimizer.py',
            'omnix_core/quantum/',
        }

        for filepath in files:
            normalized = filepath.replace('\\', '/')
            is_safe = any(safe in normalized for safe in synthetic_safe_paths)
            if is_safe:
                continue

            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
            except Exception:
                continue

            for line_num, line in enumerate(lines, 1):
                stripped = line.strip()
                if not stripped or stripped.startswith('#'):
                    continue
                if _is_in_main_block(filepath, line_num):
                    continue

                for pattern, desc in SYNTHETIC_DATA_PATTERNS:
                    if re.search(pattern, stripped):
                        violations.append({
                            'file': filepath,
                            'line': line_num,
                            'content': stripped[:120],
                            'pattern': desc
                        })

        if violations:
            report = "\n\nSYNTHETIC DATA GENERATION IN RUNTIME CODE:\n"
            report += "=" * 60 + "\n"
            for v in violations:
                report += f"\n  File: {v['file']}:{v['line']}\n"
                report += f"  Type: {v['pattern']}\n"
                report += f"  Code: {v['content']}\n"
            report += f"\n{'=' * 60}"
            report += f"\nTotal violations: {len(violations)}"
            report += "\nFix: Remove synthetic generation or move to /tests or /examples"

            pytest.fail(report)

    def test_no_demo_main_blocks_with_fake_data(self):
        """Verify __main__ blocks in runtime don't contain simulated trading signals"""
        files = _collect_python_files()
        violations = []

        demo_patterns = [
            r"^signal\s*=\s*Signal\.",
            r"^StrategySignal\(",
        ]

        for filepath in files:
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
            except Exception:
                continue

            in_main = False
            for line_num, line in enumerate(lines, 1):
                stripped = line.strip()
                if '__name__' in stripped and '__main__' in stripped:
                    in_main = True
                    continue
                if in_main:
                    for pattern in demo_patterns:
                        if re.search(pattern, stripped, re.IGNORECASE):
                            violations.append({
                                'file': filepath,
                                'line': line_num,
                                'content': stripped[:120],
                                'pattern': f"Demo data in __main__: {pattern}"
                            })

        if violations:
            report = "\n\nDEMO DATA IN __main__ BLOCKS:\n"
            report += "=" * 60 + "\n"
            for v in violations:
                report += f"\n  File: {v['file']}:{v['line']}\n"
                report += f"  Type: {v['pattern']}\n"
                report += f"  Code: {v['content']}\n"
            report += f"\n{'=' * 60}"
            report += "\nFix: Move demo code to examples/ directory"

            pytest.fail(report)

    def test_data_integrity_module_exists(self):
        """Verify the data_integrity module is importable"""
        import importlib
        spec = importlib.util.find_spec('omnix_core.data_integrity')
        assert spec is not None, "omnix_core.data_integrity module not found"

    def test_real_data_mode_enabled(self):
        """Verify REAL_DATA_MODE is True in production"""
        from omnix_core.data_integrity import REAL_DATA_MODE
        assert REAL_DATA_MODE is True, "REAL_DATA_MODE must be True in production"
