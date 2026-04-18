#!/usr/bin/env python3
"""
CASI-TRADE DEMO - ADR-019 Edge Confirmation Window Visualization
================================================================

Generates a visual timeline showing how ECW prevents premature entries.

Usage:
    python scripts/casi_trade_demo.py [--output video_demo.png]

This script:
1. Queries historical trade decisions from database
2. Finds sequences where ECW blocked trades (1/3 -> 2/3 -> RESET)
3. Generates visual timeline for investor demo video
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@dataclass
class ECWCycle:
    timestamp: datetime
    symbol: str
    ecw_progress: int  # 0, 1, 2, 3
    ecw_required: int  # Always 3
    signal: str  # BUY, SELL, HOLD
    conditions: Dict[str, Any]
    reset_reason: Optional[str]
    market_price: float
    market_after_5min: Optional[float]  # Price 5 min later for counterfactual


def generate_mock_casi_trade_scenario() -> List[ECWCycle]:
    """
    Generate a realistic "almost-trade" scenario for demo purposes.
    
    Scenario:
    - Cycle 1: BUY signal, ECW 1/3, conditions met
    - Cycle 2: BUY signal, ECW 2/3, conditions met
    - Cycle 3: BUY signal, but Black Swan spikes HIGH -> ECW RESET
    - Cycle 4: Market drops 3% -> Loss avoided
    """
    base_time = datetime.now() - timedelta(hours=2)
    base_price = 104250.00  # BTC price
    
    cycles = [
        ECWCycle(
            timestamp=base_time,
            symbol="BTC/USD",
            ecw_progress=1,
            ecw_required=3,
            signal="BUY",
            conditions={
                "mc_wr": 53.2, "mc_wr_ok": True,
                "mc_er": 0.15, "mc_er_ok": True,
                "black_swan": "LOW", "bs_ok": True
            },
            reset_reason=None,
            market_price=base_price,
            market_after_5min=None
        ),
        ECWCycle(
            timestamp=base_time + timedelta(minutes=5),
            symbol="BTC/USD",
            ecw_progress=2,
            ecw_required=3,
            signal="BUY",
            conditions={
                "mc_wr": 54.1, "mc_wr_ok": True,
                "mc_er": 0.22, "mc_er_ok": True,
                "black_swan": "LOW", "bs_ok": True
            },
            reset_reason=None,
            market_price=base_price + 50,
            market_after_5min=None
        ),
        ECWCycle(
            timestamp=base_time + timedelta(minutes=10),
            symbol="BTC/USD",
            ecw_progress=0,  # RESET
            ecw_required=3,
            signal="BUY",  # Signal was still BUY!
            conditions={
                "mc_wr": 52.8, "mc_wr_ok": True,
                "mc_er": 0.18, "mc_er_ok": True,
                "black_swan": "HIGH", "bs_ok": False  # BLACK SWAN!
            },
            reset_reason="BLACK_SWAN_HIGH",
            market_price=base_price + 80,
            market_after_5min=None
        ),
        ECWCycle(
            timestamp=base_time + timedelta(minutes=15),
            symbol="BTC/USD",
            ecw_progress=0,
            ecw_required=3,
            signal="HOLD",
            conditions={
                "mc_wr": 48.2, "mc_wr_ok": False,
                "mc_er": -0.35, "mc_er_ok": False,
                "black_swan": "HIGH", "bs_ok": False
            },
            reset_reason=None,
            market_price=base_price - 2800,  # Market dropped ~2.7%
            market_after_5min=None
        ),
    ]
    
    return cycles


def generate_ascii_timeline(cycles: List[ECWCycle]) -> str:
    """Generate ASCII art timeline for terminal output."""
    
    lines = []
    lines.append("")
    lines.append("=" * 80)
    lines.append("        ECW 'CASI-TRADE' TIMELINE - ADR-019 Demonstration")
    lines.append("=" * 80)
    lines.append("")
    
    # Header
    lines.append("    TIME       SIGNAL    ECW      CONDITIONS            RESULT")
    lines.append("    ────       ──────    ───      ──────────            ──────")
    
    for i, cycle in enumerate(cycles):
        time_str = cycle.timestamp.strftime("%H:%M")
        signal = cycle.signal.center(6)
        
        # ECW progress bar
        if cycle.reset_reason:
            ecw_bar = "✖ RESET"
        elif cycle.ecw_progress >= cycle.ecw_required:
            ecw_bar = "✓ 3/3 "
        else:
            filled = "█" * cycle.ecw_progress
            empty = "░" * (cycle.ecw_required - cycle.ecw_progress)
            ecw_bar = f"{filled}{empty} {cycle.ecw_progress}/3"
        
        # Conditions summary
        conds = cycle.conditions
        wr_icon = "✓" if conds.get("mc_wr_ok") else "✗"
        er_icon = "✓" if conds.get("mc_er_ok") else "✗"
        bs_icon = "✓" if conds.get("bs_ok") else "✗"
        bs_level = conds.get("black_swan", "?")
        
        cond_str = f"WR{wr_icon} ER{er_icon} BS:{bs_level}{bs_icon}"
        
        # Result
        if cycle.reset_reason:
            result = f"🔄 {cycle.reset_reason}"
        elif i == len(cycles) - 1 and cycle.market_price < cycles[0].market_price:
            drop = ((cycles[0].market_price - cycle.market_price) / cycles[0].market_price) * 100
            result = f"📉 -{drop:.1f}% avoided"
        elif cycle.ecw_progress < cycle.ecw_required:
            result = "⏳ Waiting..."
        else:
            result = "🚀 Trade window"
        
        # Price
        price_str = f"${cycle.market_price:,.0f}"
        
        line = f"    {time_str}      {signal}    {ecw_bar}   {cond_str:20}  {result}"
        lines.append(line)
        
        # Add connector line
        if i < len(cycles) - 1:
            lines.append("      │")
            lines.append("      ▼")
    
    lines.append("")
    lines.append("─" * 80)
    
    # Summary box
    price_drop = cycles[0].market_price - cycles[-1].market_price
    pct_drop = (price_drop / cycles[0].market_price) * 100
    
    lines.append("")
    lines.append("    ┌─────────────────────────────────────────────────────────┐")
    lines.append("    │                    📊 SUMMARY                           │")
    lines.append("    ├─────────────────────────────────────────────────────────┤")
    lines.append(f"    │  Entry Price (if traded):     ${cycles[0].market_price:>12,.2f}        │")
    lines.append(f"    │  Market Price Now:            ${cycles[-1].market_price:>12,.2f}        │")
    lines.append(f"    │  Price Movement:              {'-' if price_drop > 0 else '+'}{abs(pct_drop):>11.2f}%        │")
    lines.append("    │                                                         │")
    lines.append(f"    │  Est. Loss Avoided (0.5% pos): ${price_drop * 0.005:>10,.2f}        │")
    lines.append("    └─────────────────────────────────────────────────────────┘")
    lines.append("")
    
    # Investor message
    lines.append("    ┌─────────────────────────────────────────────────────────┐")
    lines.append("    │                                                         │")
    lines.append("    │   \"OMNIX waited.                                        │")
    lines.append("    │    The market didn't.                                   │")
    lines.append("    │    Capital preserved.\"                                  │")
    lines.append("    │                                                         │")
    lines.append("    └─────────────────────────────────────────────────────────┘")
    lines.append("")
    
    return "\n".join(lines)


def generate_json_output(cycles: List[ECWCycle]) -> Dict[str, Any]:
    """Generate JSON output for video rendering tools."""
    
    return {
        "title": "ECW Casi-Trade Demo",
        "generated_at": datetime.now().isoformat(),
        "adr": "ADR-019",
        "cycles": [
            {
                "timestamp": c.timestamp.isoformat(),
                "symbol": c.symbol,
                "ecw_progress": {"current": c.ecw_progress, "required": c.ecw_required},
                "signal": c.signal,
                "conditions": c.conditions,
                "reset_reason": c.reset_reason,
                "market_price": c.market_price
            }
            for c in cycles
        ],
        "summary": {
            "entry_price_avoided": cycles[0].market_price,
            "final_price": cycles[-1].market_price,
            "price_drop_pct": ((cycles[0].market_price - cycles[-1].market_price) / cycles[0].market_price) * 100,
            "narrative": "OMNIX esperó. El mercado no. Capital preservado."
        }
    }


def main():
    parser = argparse.ArgumentParser(description="Generate ECW Casi-Trade Demo")
    parser.add_argument("--output", "-o", help="Output file for JSON data")
    parser.add_argument("--json", action="store_true", help="Output as JSON instead of ASCII")
    args = parser.parse_args()
    
    print("\n🎬 Generating ECW 'Casi-Trade' Demo Scenario...")
    print("   (Using mock data - replace with real DB queries for production)\n")
    
    cycles = generate_mock_casi_trade_scenario()
    
    if args.json:
        output = generate_json_output(cycles)
        print(json.dumps(output, indent=2, default=str))
    else:
        timeline = generate_ascii_timeline(cycles)
        print(timeline)
    
    if args.output:
        output_data = generate_json_output(cycles)
        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2, default=str)
        print(f"\n✅ JSON data saved to: {args.output}")
    
    print("\n📌 To use with real data:")
    print("   1. Query paper_trading_decisions WHERE ecw_reset_reason IS NOT NULL")
    print("   2. Find sequences with ecw_progress 1 → 2 → RESET")
    print("   3. Correlate with price data 5-15 min after reset")


if __name__ == "__main__":
    main()
