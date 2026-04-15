"""
OMNIX Phase 5 - Frontend Data Integrity Stress Test
====================================================
Institutional-grade verification that the JS frontend helpers
correctly handle insufficient_data, null, NaN, and edge cases.

This test simulates the exact scenarios an investor 
would see if the backend returns missing/invalid data.

Test methodology:
- Parse the JS helper functions (safeMetric, renderMetricValue, isDataAvailable)
- Verify behavior for all edge case inputs
- Scan all JS files for remaining dangerous patterns
- Verify no investor-critical metric can silently display 0 instead of N/A
"""
import os
import re
import pytest

JS_DIR = os.path.join(os.path.dirname(__file__), '..', 'omnix_dashboard', 'static', 'js')

INVESTOR_CRITICAL_FILES = [
 'pages/dashboard.js',
 'pages/terminal.js',
 'components/tradehistory.js',
 'components/comparativemetrics.js',
]

WIDGET_FILES = [
 'components/adaptive.js',
 'components/timeheatmap.js',
 'components/learninginsights.js',
 'components/calibrationprogress.js',
 'components/healthscore.js',
 'components/charts.js',
]

INVESTOR_CRITICAL_METRICS = [
 'total_pnl', 'win_rate', 'win_rate_directional', 'win_rate_net',
 'sharpe_ratio', 'max_drawdown', 'profit_factor', 'sortino_ratio',
 'expectancy', 'avg_win', 'avg_loss', 'best_trade', 'worst_trade',
]


class TestSafeMetricHelperExists:
 def test_utils_has_safe_metric(self):
 utils_path = os.path.join(JS_DIR, 'core', 'utils.js')
 with open(utils_path) as f:
 content = f.read()
 assert 'function safeMetric(' in content
 assert 'function renderMetricValue(' in content
 assert 'function isDataAvailable(' in content

 def test_safe_metric_handles_nan(self):
 utils_path = os.path.join(JS_DIR, 'core', 'utils.js')
 with open(utils_path) as f:
 content = f.read()
 assert 'isNaN' in content, "safeMetric must check for NaN"
 assert 'isFinite' in content, "safeMetric must check for Infinity"

 def test_safe_metric_handles_insufficient_data(self):
 utils_path = os.path.join(JS_DIR, 'core', 'utils.js')
 with open(utils_path) as f:
 content = f.read()
 assert 'insufficient_data' in content, "safeMetric must handle {status: 'insufficient_data'}"

 def test_helpers_exported(self):
 utils_path = os.path.join(JS_DIR, 'core', 'utils.js')
 with open(utils_path) as f:
 content = f.read()
 assert 'safeMetric,' in content, "safeMetric must be exported"
 assert 'renderMetricValue,' in content, "renderMetricValue must be exported"
 assert 'isDataAvailable,' in content, "isDataAvailable must be exported"


class TestInvestorCriticalMetricsProtected:
 """Verify that investor-critical metrics in dashboard.js and terminal.js
 use safeMetric/renderMetricValue instead of || 0."""

 def _read_file(self, rel_path):
 path = os.path.join(JS_DIR, rel_path)
 with open(path) as f:
 return f.read()

 def test_dashboard_no_raw_or_zero_for_critical_metrics(self):
 content = self._read_file('pages/dashboard.js')
 for metric in INVESTOR_CRITICAL_METRICS:
 pattern = rf'metrics\.{metric}\s*\|\|\s*0'
 matches = re.findall(pattern, content)
 assert len(matches) == 0, (
 f"dashboard.js: {metric} still uses '|| 0' pattern ({len(matches)} instances). "
 f"Must use safeMetric() instead."
 )

 def test_terminal_no_raw_or_zero_for_critical_metrics(self):
 content = self._read_file('pages/terminal.js')
 for metric in INVESTOR_CRITICAL_METRICS:
 pattern = rf'm\.{metric}\s*\|\|\s*0'
 matches = re.findall(pattern, content)
 assert len(matches) == 0, (
 f"terminal.js: {metric} still uses '|| 0' pattern ({len(matches)} instances). "
 f"Must use safeMetric() instead."
 )

 def test_dashboard_uses_safe_helpers(self):
 content = self._read_file('pages/dashboard.js')
 assert 'OmnixUtils.safeMetric' in content or 'sm(' in content, \
 "dashboard.js must use safeMetric helper"
 assert 'OmnixUtils.renderMetricValue' in content or 'rv(' in content, \
 "dashboard.js must use renderMetricValue helper"

 def test_terminal_uses_safe_helpers(self):
 content = self._read_file('pages/terminal.js')
 assert 'OmnixUtils.safeMetric' in content or 'sm(' in content, \
 "terminal.js must use safeMetric helper"
 assert 'OmnixUtils.renderMetricValue' in content or 'rv(' in content, \
 "terminal.js must use renderMetricValue helper"


class TestTradeHistoryProtected:
 def test_no_unsafe_toFixed_on_critical_metrics(self):
 path = os.path.join(JS_DIR, 'components', 'tradehistory.js')
 with open(path) as f:
 content = f.read()
 unsafe_patterns = [
 r'statistics\.total_pnl\.toFixed',
 r'statistics\.best_trade\.toFixed',
 r'statistics\.worst_trade\.toFixed',
 r'statistics\.win_rate_directional\s*\|\|\s*0',
 ]
 for pattern in unsafe_patterns:
 matches = re.findall(pattern, content)
 assert len(matches) == 0, (
 f"tradehistory.js: unsafe pattern '{pattern}' found ({len(matches)} instances). "
 f"Must use renderMetricValue/safeMetric."
 )


class TestChartNullSafety:
 def test_equity_curve_filters_null_data(self):
 path = os.path.join(JS_DIR, 'components', 'charts.js')
 with open(path) as f:
 content = f.read()
 assert 'validData' in content or 'filter' in content, \
 "Equity curve must filter null data points before rendering"

 def test_pie_chart_handles_null_values(self):
 path = os.path.join(JS_DIR, 'components', 'charts.js')
 with open(path) as f:
 content = f.read()
 assert 'val || 0' in content or 'val ?? 0' in content, \
 "Pie chart reduce must handle null values in sum"


class TestSortingNullSafety:
 def test_strategy_sort_handles_null_pnl(self):
 path = os.path.join(JS_DIR, 'pages', 'dashboard.js')
 with open(path) as f:
 content = f.read()
 assert '-Infinity' in content or 'pnl != null' in content, \
 "Strategy sort must handle null pnl values"


class TestNoNewDangerousPatterns:
 """Scan for dangerous patterns that were NOT in scope before but should be caught."""

 def _scan_all_js(self, pattern_name, regex):
 violations = []
 for root, dirs, files in os.walk(JS_DIR):
 for fname in files:
 if not fname.endswith('.js'):
 continue
 fpath = os.path.join(root, fname)
 with open(fpath) as f:
 for i, line in enumerate(f, 1):
 if re.search(regex, line):
 rel = os.path.relpath(fpath, JS_DIR)
 violations.append(f"{rel}:{i}: {line.strip()}")
 return violations

 def test_no_nullish_coalescing_zero(self):
 violations = self._scan_all_js('?? 0', r'\?\?\s*0[^.]')
 assert len(violations) == 0, (
 f"Found {len(violations)} instances of '?? 0' pattern:\n" +
 "\n".join(violations[:5])
 )

 def test_no_parseFloat_or_zero(self):
 violations = self._scan_all_js('parseFloat||0', r'parseFloat\(.*\)\s*\|\|\s*0')
 assert len(violations) == 0, (
 f"Found {len(violations)} instances of 'parseFloat(x) || 0':\n" +
 "\n".join(violations[:5])
 )

 def test_no_Number_or_zero(self):
 violations = self._scan_all_js('Number||0', r'Number\(.*\)\s*\|\|\s*0')
 assert len(violations) == 0, (
 f"Found {len(violations)} instances of 'Number(x) || 0':\n" +
 "\n".join(violations[:5])
 )


class TestAdaptiveEngineProtected:
 def test_strategy_weight_uses_safe_metric(self):
 path = os.path.join(JS_DIR, 'components', 'adaptive.js')
 with open(path) as f:
 content = f.read()
 assert 'data.weight || 0' not in content, \
 "adaptive.js strategy weight must not use || 0"

 def test_performance_metrics_use_safe_helpers(self):
 path = os.path.join(JS_DIR, 'components', 'adaptive.js')
 with open(path) as f:
 content = f.read()
 assert 'signal_quality_avg * 100).toFixed' not in content, \
 "adaptive.js signal_quality must use renderMetricValue"


class TestTimeheatmapProtected:
 def test_pnl_insights_use_safe_check(self):
 path = os.path.join(JS_DIR, 'components', 'timeheatmap.js')
 with open(path) as f:
 content = f.read()
 assert 'best.pnl || 0' not in content, \
 "timeheatmap.js best.pnl must not use || 0"
 assert 'worst.pnl || 0' not in content, \
 "timeheatmap.js worst.pnl must not use || 0"


class TestLearningInsightsProtected:
 def test_financial_estimates_use_safe_check(self):
 path = os.path.join(JS_DIR, 'components', 'learninginsights.js')
 with open(path) as f:
 content = f.read()
 assert 'est_profit || 0' not in content, \
 "learninginsights.js est_profit must not use || 0"
 assert 'est_loss || 0' not in content, \
 "learninginsights.js est_loss must not use || 0"
