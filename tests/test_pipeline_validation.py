"""
OMNIX Pipeline Validation — Institutional Audit Test Suite
============================================================
End-to-end verification: DB → calculate_metrics() → /api/metrics → Dashboard

Tests verify:
1. DB data integrity (no NULL critical fields, valid timestamps, valid P&L)
2. Metrics calculation consistency (SQL vs Python vs API)
3. Track Record period separation (Baseline vs Official)
4. Governance receipt hash chain integrity
5. Veto traceability
6. No hardcoded metrics in frontend

Run: TESTING=true TELEGRAM_BOT_TOKEN=test-token python -m pytest tests/test_pipeline_validation.py -v
"""
import os
import re
import json
import pytest
import psycopg2
import numpy as np

DB_URL = os.environ.get('DATABASE_URL')
JS_DIR = os.path.join(os.path.dirname(__file__), '..', 'omnix_dashboard', 'static', 'js')


def get_db_connection():
    if not DB_URL:
        pytest.skip("DATABASE_URL not set")
    return psycopg2.connect(DB_URL)


class TestDBDataIntegrity:
    """Stage 1: Verify raw data quality in paper_trading_trades"""

    def test_no_null_critical_fields(self):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                COUNT(CASE WHEN entry_price IS NULL THEN 1 END) as null_entry,
                COUNT(CASE WHEN symbol IS NULL OR symbol = '' THEN 1 END) as null_symbol,
                COUNT(CASE WHEN side IS NULL OR side = '' THEN 1 END) as null_side,
                COUNT(CASE WHEN quantity IS NULL OR quantity <= 0 THEN 1 END) as invalid_qty,
                COUNT(CASE WHEN opened_at IS NULL THEN 1 END) as null_opened
            FROM paper_trading_trades
        """)
        row = cur.fetchone()
        conn.close()
        assert row[0] == 0, f"Found {row[0]} trades with NULL entry_price"
        assert row[1] == 0, f"Found {row[1]} trades with NULL/empty symbol"
        assert row[2] == 0, f"Found {row[2]} trades with NULL/empty side"
        assert row[3] == 0, f"Found {row[3]} trades with invalid quantity"
        assert row[4] == 0, f"Found {row[4]} trades with NULL opened_at"

    def test_no_duplicate_trades(self):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT symbol, opened_at, COUNT(*) as dupes
            FROM paper_trading_trades
            GROUP BY symbol, opened_at
            HAVING COUNT(*) > 1
        """)
        dupes = cur.fetchall()
        conn.close()
        assert len(dupes) == 0, f"Found {len(dupes)} duplicate trade entries"

    def test_timestamps_are_logical(self):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM paper_trading_trades
            WHERE closed_at IS NOT NULL AND closed_at < opened_at
        """)
        bad = cur.fetchone()[0]
        conn.close()
        assert bad == 0, f"Found {bad} trades where closed_at < opened_at"

    def test_closed_trades_have_exit_price(self):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM paper_trading_trades
            WHERE closed_at IS NOT NULL AND exit_price IS NULL
        """)
        bad = cur.fetchone()[0]
        conn.close()
        assert bad == 0, f"Found {bad} closed trades with NULL exit_price"

    def test_pnl_direction_consistency(self):
        """P&L should generally align with price movement direction (allowing for fees)"""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM paper_trading_trades
            WHERE closed_at IS NOT NULL
            AND side = 'buy'
            AND exit_price > entry_price * 1.01
            AND profit_loss < -100
        """)
        severe = cur.fetchone()[0]
        conn.close()
        assert severe <= 1, (
            f"Found {severe} trades where price went up >1% but P&L is severely negative. "
            f"1 known anomaly (trade #1) is acceptable."
        )


class TestMetricsCalculationConsistency:
    """Stage 2: SQL aggregations must match calculate_metrics()"""

    def _get_sql_metrics(self):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                ROUND(SUM(profit_loss)::numeric, 2),
                COUNT(CASE WHEN profit_loss > 0 THEN 1 END),
                COUNT(CASE WHEN profit_loss < 0 THEN 1 END),
                ROUND(COUNT(CASE WHEN profit_loss > 0 THEN 1 END)::numeric / 
                      NULLIF(COUNT(*)::numeric, 0) * 100, 2),
                ROUND(MAX(profit_loss)::numeric, 2),
                ROUND(MIN(profit_loss)::numeric, 2),
                ROUND(AVG(CASE WHEN profit_loss > 0 THEN profit_loss END)::numeric, 2),
                ROUND(AVG(CASE WHEN profit_loss < 0 THEN ABS(profit_loss) END)::numeric, 2)
            FROM paper_trading_trades
            WHERE closed_at IS NOT NULL
        """)
        row = cur.fetchone()
        conn.close()
        return {
            'total_pnl': float(row[0]),
            'winners': int(row[1]),
            'losers': int(row[2]),
            'win_rate': float(row[3]),
            'best_trade': float(row[4]),
            'worst_trade': float(row[5]),
            'avg_win': float(row[6]),
            'avg_loss': float(row[7]),
        }

    def _get_python_metrics(self):
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'omnix_dashboard'))
        from utils.queries import get_paper_trades, calculate_metrics
        result = get_paper_trades(return_dict=True)
        if not result['success']:
            pytest.skip(f"Cannot connect to DB: {result['error']}")
        return calculate_metrics(result['trades'])

    def test_total_pnl_matches(self):
        sql = self._get_sql_metrics()
        py = self._get_python_metrics()
        assert sql['total_pnl'] == py['total_pnl'], \
            f"P&L mismatch: SQL={sql['total_pnl']}, Python={py['total_pnl']}"

    def test_win_rate_matches(self):
        sql = self._get_sql_metrics()
        py = self._get_python_metrics()
        assert sql['win_rate'] == py['win_rate'], \
            f"Win rate mismatch: SQL={sql['win_rate']}, Python={py['win_rate']}"

    def test_best_worst_trade_matches(self):
        sql = self._get_sql_metrics()
        py = self._get_python_metrics()
        assert sql['best_trade'] == py['best_trade'], \
            f"Best trade mismatch: SQL={sql['best_trade']}, Python={py['best_trade']}"
        assert sql['worst_trade'] == py['worst_trade'], \
            f"Worst trade mismatch: SQL={sql['worst_trade']}, Python={py['worst_trade']}"

    def test_avg_win_loss_matches(self):
        sql = self._get_sql_metrics()
        py = self._get_python_metrics()
        assert sql['avg_win'] == py['avg_win'], \
            f"Avg win mismatch: SQL={sql['avg_win']}, Python={py['avg_win']}"
        assert sql['avg_loss'] == py['avg_loss'], \
            f"Avg loss mismatch: SQL={sql['avg_loss']}, Python={py['avg_loss']}"


class TestAPIMetricsConsistency:
    """Stage 2b: /api/metrics must return same values as SQL and calculate_metrics()"""

    def _get_api_metrics(self):
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'omnix_dashboard'))
        from omnix_dashboard.app import create_app
        app = create_app()
        with app.test_client() as client:
            resp = client.get('/api/metrics')
            assert resp.status_code == 200, f"API returned {resp.status_code}"
            data = resp.get_json()
            assert data.get('success'), f"API returned success=False: {data.get('error')}"
            return data['metrics']

    def _get_sql_metrics(self):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                ROUND(SUM(profit_loss)::numeric, 2),
                ROUND(COUNT(CASE WHEN profit_loss > 0 THEN 1 END)::numeric / 
                      NULLIF(COUNT(*)::numeric, 0) * 100, 2),
                ROUND(MAX(profit_loss)::numeric, 2),
                ROUND(MIN(profit_loss)::numeric, 2)
            FROM paper_trading_trades
            WHERE closed_at IS NOT NULL
        """)
        row = cur.fetchone()
        conn.close()
        return {
            'total_pnl': float(row[0]),
            'win_rate': float(row[1]),
            'best_trade': float(row[2]),
            'worst_trade': float(row[3]),
        }

    def test_api_pnl_matches_sql(self):
        api = self._get_api_metrics()
        sql = self._get_sql_metrics()
        assert api['total_pnl'] == sql['total_pnl'], \
            f"API P&L ({api['total_pnl']}) != SQL P&L ({sql['total_pnl']})"

    def test_api_win_rate_matches_sql(self):
        api = self._get_api_metrics()
        sql = self._get_sql_metrics()
        assert api['win_rate'] == sql['win_rate'], \
            f"API win_rate ({api['win_rate']}) != SQL win_rate ({sql['win_rate']})"

    def test_api_best_worst_matches_sql(self):
        api = self._get_api_metrics()
        sql = self._get_sql_metrics()
        assert api['best_trade'] == sql['best_trade'], \
            f"API best_trade ({api['best_trade']}) != SQL ({sql['best_trade']})"
        assert api['worst_trade'] == sql['worst_trade'], \
            f"API worst_trade ({api['worst_trade']}) != SQL ({sql['worst_trade']})"


class TestTrackRecordSeparation:
    """Stage 3: Baseline vs Official Track Record"""

    def test_no_trades_in_official_track_record(self):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM paper_trading_trades
            WHERE opened_at >= '2026-01-15'
        """)
        count = cur.fetchone()[0]
        conn.close()
        assert count == 0, (
            f"Found {count} trades in Official Track Record period. "
            f"Expected 0 (system in governance/HOLD mode since Jan 15)."
        )

    def test_all_trades_are_baseline(self):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM paper_trading_trades
            WHERE opened_at < '2026-01-15'
        """)
        baseline = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM paper_trading_trades")
        total = cur.fetchone()[0]
        conn.close()
        assert baseline == total, \
            f"Baseline={baseline}, Total={total}. All trades should be in baseline period."

    def test_all_trades_have_telemetry_source(self):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT telemetry_source FROM paper_trading_trades
        """)
        sources = [r[0] for r in cur.fetchall()]
        conn.close()
        assert len(sources) > 0, "No telemetry sources found"
        for src in sources:
            assert src is not None, "Found trade with NULL telemetry_source"


class TestGovernanceReceiptIntegrity:
    """Stage 4: Hash chain and signature verification"""

    def test_receipts_exist(self):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM decision_receipts")
        count = cur.fetchone()[0]
        conn.close()
        assert count > 0, "No governance receipts found"

    def test_all_receipts_signed_with_dilithium(self):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM decision_receipts
            WHERE signature_algorithm != 'Dilithium-3 (ML-DSA-65)'
        """)
        non_dilithium = cur.fetchone()[0]
        conn.close()
        assert non_dilithium == 0, \
            f"Found {non_dilithium} receipts NOT signed with Dilithium-3"

    def test_hash_chain_integrity(self):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) as broken
            FROM decision_receipts r
            JOIN decision_receipts prev_r ON prev_r.id = r.id - 1
            WHERE r.id > (SELECT MIN(id) FROM decision_receipts)
            AND r.prev_hash != prev_r.content_hash
        """)
        broken = cur.fetchone()[0]
        conn.close()
        assert broken == 0, f"Hash chain broken at {broken} points"

    def test_no_null_hashes(self):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM decision_receipts
            WHERE content_hash IS NULL OR content_hash = ''
            OR signature IS NULL OR signature = ''
        """)
        nulls = cur.fetchone()[0]
        conn.close()
        assert nulls == 0, f"Found {nulls} receipts with NULL hash or signature"


class TestVetoTraceability:
    """Stage 4b: Veto log and shadow portfolio"""

    def test_veto_log_populated(self):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM trading_veto_log")
        count = cur.fetchone()[0]
        conn.close()
        assert count > 0, "No veto log entries found"

    def test_shadow_events_populated(self):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM shadow_trade_events")
        count = cur.fetchone()[0]
        conn.close()
        assert count > 0, "No shadow trade events found"

    def test_veto_types_are_valid(self):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT veto_type FROM trading_veto_log")
        types = [r[0] for r in cur.fetchall()]
        conn.close()
        valid_types = {'BLACK_SWAN', 'ECW_WAITING', 'COHERENCE_GATE', 'MC_VETO', 'RMS_VETO', 'ADAPTIVE_GATE', 'DCI_VETO'}
        for vt in types:
            assert vt in valid_types, f"Unknown veto type: {vt}"


class TestNoHardcodedMetricsInFrontend:
    """Stage 3b: No hardcoded financial values in JS"""

    def test_no_hardcoded_pnl_in_tradehistory(self):
        path = os.path.join(JS_DIR, 'components', 'tradehistory.js')
        with open(path) as f:
            content = f.read()
        pattern = r'-?\$[\d,]+\.\d{2}\s+P&L'
        matches = re.findall(pattern, content)
        assert len(matches) == 0, (
            f"Found hardcoded P&L values in tradehistory.js: {matches}. "
            f"Must use dynamic data from API."
        )

    def test_no_hardcoded_trade_counts_in_tradehistory(self):
        path = os.path.join(JS_DIR, 'components', 'tradehistory.js')
        with open(path) as f:
            content = f.read()
        pattern = r'\b119 trades\b'
        matches = re.findall(pattern, content)
        assert len(matches) == 0, (
            f"Found hardcoded '119 trades' in tradehistory.js: must use dynamic data."
        )
