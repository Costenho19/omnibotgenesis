"""
OMNIX Backtest Phase 0 — Step 3: Run 6-Checkpoint Evaluation & Calculate P&L
=============================================================================
Runs GovernanceEvaluationEngine on all computed signal points.
Calculates actual vs. governance-adjusted P&L.

Uses the EXACT same GovernanceEvaluationEngine as the production system.
"""

import os
import sys
import json
import importlib.util
import psycopg2

# Import external_evaluator directly to avoid Telegram dependency chain
spec = importlib.util.spec_from_file_location(
    "external_evaluator",
    "/home/runner/workspace/omnix_core/governance/external_evaluator.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
GovernanceEvaluationEngine = mod.GovernanceEvaluationEngine

DATABASE_URL = os.environ['DATABASE_URL']


def calculate_group_pnl(cur, asset: str, eval_hour) -> tuple[float, int]:
    """
    Calculate actual P&L for all trades in this (asset, hour) group.
    P&L = sum of USD flows for trades matched to this hour.
    
    BUY:  USD negative (cash out), crypto positive (received)
    SELL: USD positive (cash in), crypto negative (sold out)
    Net USD flow per refid = sum of USD legs
    """
    cur.execute("""
        SELECT refid, SUM(amount_usd) as net_usd
        FROM kraken_real_trades
        WHERE asset IN ('USD', %s)
          AND type = 'trade'
          AND date_trunc('hour', trade_time) = %s
          AND amount_usd IS NOT NULL
        GROUP BY refid
        HAVING ABS(SUM(amount_usd)) > 0.01
    """, (asset, eval_hour))
    rows = cur.fetchall()
    
    total_pnl = sum(float(r[1]) for r in rows)
    trade_count = len(rows)
    return total_pnl, trade_count


def main():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    engine = GovernanceEvaluationEngine()
    
    # Get all computed signals
    cur.execute("""
        SELECT eval_key, asset, eval_hour,
               probability_score, risk_exposure, signal_coherence,
               trend_persistence, stress_resilience, logic_consistency
        FROM backtest_phase0_signals
        WHERE status = 'COMPUTED'
        ORDER BY eval_hour, asset
    """)
    signal_rows = cur.fetchall()
    
    print(f"Evaluating {len(signal_rows)} signal points...")
    
    approved = 0
    blocked = 0
    
    actual_total_pnl = 0.0
    governance_pnl = 0.0
    
    for row in signal_rows:
        eval_key, asset, eval_hour, p, r, c, t, s, l = row
        
        signals = {
            'probability_score': float(p),
            'risk_exposure':     float(r),
            'signal_coherence':  float(c),
            'trend_persistence': float(t),
            'stress_resilience': float(s),
            'logic_consistency': float(l),
        }
        
        result = engine.evaluate(
            signals=signals,
            asset=asset,
            domain="trading_backtest_phase0",
            metadata={"eval_key": eval_key, "method": "retrospective_estimation"}
        )
        
        decision = result.get('decision', 'BLOCKED')
        veto_chain = result.get('veto_chain', [])
        checkpoints_passed = result.get('checkpoints_passed', 0)
        
        # Calculate actual P&L for this (asset, hour) group
        actual_pnl, trade_count = calculate_group_pnl(cur, asset, eval_hour)
        
        # Counterfactual: if BLOCKED, trade doesn't execute → P&L = 0
        counterfactual_pnl = actual_pnl if decision == 'APPROVED' else 0.0
        
        actual_total_pnl += actual_pnl
        governance_pnl += counterfactual_pnl
        
        if decision == 'APPROVED':
            approved += 1
        else:
            blocked += 1
        
        cur.execute("""
            INSERT INTO backtest_phase0_results (
                eval_key, asset, eval_hour,
                decision, veto_chain, checkpoints_passed,
                actual_pnl_usd, counterfactual_pnl_usd, trade_count
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (
            eval_key, asset, eval_hour,
            decision,
            json.dumps(veto_chain),
            checkpoints_passed,
            round(actual_pnl, 4),
            round(counterfactual_pnl, 4),
            trade_count
        ))
    
    conn.commit()
    
    # Final summary
    total_evaluated = approved + blocked
    block_rate = blocked / total_evaluated * 100 if total_evaluated > 0 else 0
    pnl_improvement = governance_pnl - actual_total_pnl
    improvement_pct = (pnl_improvement / abs(actual_total_pnl) * 100) if actual_total_pnl != 0 else 0
    
    print("\n" + "="*60)
    print("BACKTEST PHASE 0 — FINAL RESULTS")
    print("="*60)
    print(f"Evaluation points analyzed: {total_evaluated}")
    print(f"  APPROVED:   {approved} ({100-block_rate:.1f}%)")
    print(f"  BLOCKED:    {blocked} ({block_rate:.1f}%)")
    print()
    print(f"ACTUAL P&L (all trades executed):    ${actual_total_pnl:+.2f}")
    print(f"GOVERNANCE P&L (only APPROVED):      ${governance_pnl:+.2f}")
    print(f"P&L Improvement:                     ${pnl_improvement:+.2f}")
    print(f"Improvement %:                       {improvement_pct:+.1f}%")
    print()
    
    # Most common veto reasons
    cur.execute("""
        SELECT jsonb_array_elements_text(veto_chain) as cp, COUNT(*) as cnt
        FROM backtest_phase0_results
        WHERE decision = 'BLOCKED' AND jsonb_array_length(veto_chain) > 0
        GROUP BY cp ORDER BY cnt DESC LIMIT 6
    """)
    veto_rows = cur.fetchall()
    if veto_rows:
        print("Most triggered veto checkpoints:")
        for vr in veto_rows:
            print(f"  {vr[0]}: {vr[1]} times")
    
    print()
    print("METHODOLOGY NOTE: This is a retrospective estimation using")
    print("reconstructed signals from real trade price history. It is")
    print("NOT a replay of the live system. See PHASE0_GOVERNANCE_BACKTEST.md")
    print("="*60)
    
    cur.close()
    conn.close()
    
    return {
        'total_evaluated': total_evaluated,
        'approved': approved,
        'blocked': blocked,
        'block_rate_pct': round(block_rate, 1),
        'actual_pnl': round(actual_total_pnl, 2),
        'governance_pnl': round(governance_pnl, 2),
        'pnl_improvement': round(pnl_improvement, 2),
        'improvement_pct': round(improvement_pct, 1),
    }


if __name__ == '__main__':
    results = main()
    print(f"\nResults dict: {results}")
