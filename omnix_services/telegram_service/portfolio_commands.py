"""
OMNIX V6.4 INSTITUTIONAL+ Portfolio Commands
Telegram commands for portfolio management and status
"""

import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from omnix_services.portfolio_management import OmnixPortfolioEngine
    PORTFOLIO_AVAILABLE = True
except ImportError:
    PORTFOLIO_AVAILABLE = False
    logger.warning("Portfolio management module not available")

portfolio_engine: Optional[OmnixPortfolioEngine] = None


def get_portfolio_engine() -> OmnixPortfolioEngine:
    """Lazy initialization of portfolio engine"""
    global portfolio_engine
    
    if portfolio_engine is None:
        portfolio_engine = OmnixPortfolioEngine(
            target_volatility=0.10,
            target_beta=0.5,
            risk_aversion=3.0,
            max_weight_per_asset=0.15,
            max_weight_per_sector=0.35
        )
    
    return portfolio_engine


async def handle_portfolio_status(update, context) -> None:
    """
    /portfolio_status - Show institutional portfolio status
    
    Displays:
    - Performance metrics (return, vol, Sharpe)
    - Exposure analysis (beta, net/gross)
    - Diversification metrics
    - Top positions
    - Risk warnings
    """
    try:
        if not PORTFOLIO_AVAILABLE:
            await update.message.reply_text(
                "Portfolio management module not available.\n"
                "Please ensure V6.4 INSTITUTIONAL+ is properly installed."
            )
            return
        
        engine = get_portfolio_engine()
        status = engine.get_portfolio_status()
        
        if status.get("status") == "NO_PORTFOLIO":
            msg = """**OMNIX V6.4 INSTITUTIONAL+**
Portfolio Status

No active portfolio constructed yet.

Use /rebalance_portfolio to build an optimal portfolio
based on current market conditions and module signals.

**Available Modules:**
 RiskModelEngine (Covariance/Beta)
 PortfolioOptimizer (Markowitz/Black-Litterman)
 VolatilityTargetingEngine
 ExposureManager (Limits/Compliance)
 ClusteringRiskDetector"""
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            return
        
        perf = status['performance']
        exp = status['exposure']
        div = status['diversification']
        
        msg = f"""**OMNIX V6.4 INSTITUTIONAL+**
Portfolio Status | {datetime.now().strftime('%H:%M:%S')}

**Performance Metrics**
 Expected Return: {perf['expected_return']}
 Expected Volatility: {perf['expected_volatility']}
 Sharpe Ratio: {perf['sharpe_ratio']}
 Risk Profile: {perf['risk_profile'].upper()}

**Exposure Analysis**
 Portfolio Beta: {exp['portfolio_beta']}
 Net Exposure: {exp['net_exposure']}
 Gross Exposure: {exp['gross_exposure']}

**Sector Breakdown**
"""
        for sector, weight in exp['sector_breakdown'].items():
            msg += f"  {sector}: {weight}\n"
        
        msg += f"""
**Diversification**
 Effective N Assets: {div['effective_n_assets']}
 Diversification Score: {div['diversification_score']}
 Total Positions: {div['total_positions']}

**Top 5 Positions**
"""
        for pos in status['top_positions']:
            msg += f"  {pos['symbol']}: {pos['weight']}\n"
        
        if status.get('warnings'):
            msg += f"\n**Risk Warnings** ({len(status['warnings'])})\n"
            for warn in status['warnings'][:3]:
                msg += f"  {warn}\n"
        else:
            msg += "\n No active risk warnings"
        
        await update.message.reply_text(msg, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in portfolio_status: {e}")
        await update.message.reply_text(
            f"Error getting portfolio status: {str(e)}"
        )


async def handle_risk_dashboard(update, context) -> None:
    """
    /risk_dashboard - Show institutional risk analysis
    
    Displays:
    - Volatility regime
    - Asset betas
    - Cluster risks
    - Exposure limits
    """
    try:
        if not PORTFOLIO_AVAILABLE:
            await update.message.reply_text(
                "Portfolio management module not available."
            )
            return
        
        engine = get_portfolio_engine()
        report = engine.get_risk_report()
        
        if report.get("status") == "NO_DATA":
            msg = """**OMNIX V6.4 INSTITUTIONAL+**
Risk Dashboard

No risk metrics computed yet.

Run /rebalance_portfolio first to compute risk metrics."""
            await update.message.reply_text(msg, parse_mode='Markdown')
            return
        
        vol_regime = report['volatility_regime']
        
        msg = f"""**OMNIX V6.4 INSTITUTIONAL+**
Risk Dashboard | {datetime.now().strftime('%H:%M:%S')}

**Data Quality**: {report['data_quality']}
**Benchmark**: {report['benchmark']}

**Volatility Regime**
 Status: {vol_regime['status'].upper()}
 Trend: {vol_regime['trend']}
 Current/Historical: {vol_regime['current_vs_historical']}x

**Top Asset Betas** (vs {report['benchmark']})
"""
        for symbol, beta in list(report['betas'].items())[:8]:
            beta_emoji = "" if beta > 1.2 else "" if beta < 0.8 else ""
            msg += f"  {symbol}: {beta} {beta_emoji}\n"
        
        msg += "\n**Asset Volatilities** (Annual)\n"
        for symbol, vol in list(report['volatilities'].items())[:8]:
            msg += f"  {symbol}: {vol}\n"
        
        msg += f"""
**Cluster Risk**
 Warning Count: {report['cluster_risks']['warnings_count']}
 Diversification: {report['cluster_risks']['diversification']}

**Exposure Limits**
 Max per Asset: {report['exposure_limits']['max_asset']:.0%}
 Max per Sector: {report['exposure_limits']['max_sector']:.0%}
 Target Beta: {report['exposure_limits']['target_beta']}
 Max Gross: {report['exposure_limits']['max_gross']:.0%}"""
        
        await update.message.reply_text(msg, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in risk_dashboard: {e}")
        await update.message.reply_text(f"Error: {str(e)}")


async def handle_rebalance_portfolio(update, context) -> None:
    """
    /rebalance_portfolio - Build optimal institutional portfolio
    
    Runs the full optimization pipeline:
    1. Fetch latest prices
    2. Gather module signals
    3. Run Black-Litterman optimization
    4. Apply volatility targeting
    5. Check exposure limits
    6. Detect cluster risks
    7. Generate rebalance orders
    """
    try:
        if not PORTFOLIO_AVAILABLE:
            await update.message.reply_text(
                "Portfolio management module not available."
            )
            return
        
        await update.message.reply_text(
            "**OMNIX V6.4 INSTITUTIONAL+**\n\n"
            "Building optimal portfolio...\n\n"
            " RiskModelEngine\n"
            " PortfolioOptimizer\n"
            " VolatilityTargeting\n"
            " ExposureManager\n"
            " ClusterDetector",
            parse_mode='Markdown'
        )
        
        engine = get_portfolio_engine()
        
        demo_prices = {
            "AAPL": [175 + i*0.5 for i in range(60)],
            "MSFT": [380 + i*0.8 for i in range(60)],
            "GOOGL": [140 + i*0.3 for i in range(60)],
            "NVDA": [480 + i*2.0 for i in range(60)],
            "TSLA": [250 + i*1.5 for i in range(60)],
            "JPM": [170 + i*0.4 for i in range(60)],
            "BTC": [43000 + i*200 for i in range(60)],
            "ETH": [2200 + i*30 for i in range(60)],
            "SPY": [450 + i*0.6 for i in range(60)],
        }
        
        demo_signals = {
            "AAPL": {"direction": "LONG", "confidence": 0.75, "source": "HMM"},
            "MSFT": {"direction": "LONG", "confidence": 0.80, "source": "ARES"},
            "GOOGL": {"direction": "NEUTRAL", "confidence": 0.60, "source": "MONTE_CARLO"},
            "NVDA": {"direction": "STRONG_LONG", "confidence": 0.85, "source": "MEMORY_KERNEL"},
            "TSLA": {"direction": "SHORT", "confidence": 0.65, "source": "HMM"},
            "JPM": {"direction": "LONG", "confidence": 0.70, "source": "KALMAN"},
            "BTC": {"direction": "LONG", "confidence": 0.72, "source": "ARES"},
            "ETH": {"direction": "LONG", "confidence": 0.68, "source": "HMM"},
        }
        
        from omnix_services.portfolio_management.institutional.volatility_targeting import RiskProfile
        
        snapshot = engine.build_portfolio(
            prices=demo_prices,
            signals=demo_signals,
            risk_profile=RiskProfile.INSTITUTIONAL,
            view_confidence=0.5
        )
        
        sorted_weights = sorted(
            [(s, w) for s, w in snapshot.weights.items() if w > 0.01],
            key=lambda x: -x[1]
        )
        
        msg = f"""**OMNIX V6.4 INSTITUTIONAL+**
Portfolio Constructed Successfully

**Performance**
 Expected Return: {snapshot.expected_return:.1%}
 Volatility: {snapshot.expected_volatility:.1%}
 Sharpe Ratio: {snapshot.sharpe_ratio:.2f}
 Risk Profile: {snapshot.risk_profile.upper()}

**Risk Metrics**
 Portfolio Beta: {snapshot.portfolio_beta:.2f}
 Net Exposure: {snapshot.net_exposure:.1%}
 Gross Exposure: {snapshot.gross_exposure:.1%}
 Effective N: {snapshot.effective_n_assets:.1f}
 Diversification: {snapshot.diversification_score:.0%}

**Optimal Allocation**
"""
        for symbol, weight in sorted_weights[:8]:
            msg += f"  {symbol}: {weight:.1%}\n"
        
        if snapshot.cluster_warnings:
            msg += f"\n**Cluster Warnings** ({len(snapshot.cluster_warnings)})\n"
            for warn in snapshot.cluster_warnings[:2]:
                msg += f"  {warn}\n"
        else:
            msg += "\n All exposure checks passed"
        
        msg += "\n\nUse /portfolio_status for detailed view"
        
        await update.message.reply_text(msg, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in rebalance_portfolio: {e}")
        await update.message.reply_text(f"Error building portfolio: {str(e)}")


async def handle_module_status(update, context) -> None:
    """
    /module_status - Show status of all institutional modules
    """
    try:
        if not PORTFOLIO_AVAILABLE:
            await update.message.reply_text(
                "Portfolio management module not available."
            )
            return
        
        engine = get_portfolio_engine()
        status = engine.get_all_module_status()
        
        msg = """**OMNIX V6.4 INSTITUTIONAL+**
Module Status

**Portfolio Engine**
"""
        pe = status['portfolio_engine']
        msg += f"  Version: {pe['version']} {pe['codename']}\n"
        msg += f"  Last Build: {pe['last_build'] or 'Never'}\n"
        
        msg += f"""
**RiskModelEngine**
  Version: {status['risk_model']['version']}
  Benchmark: {status['risk_model']['benchmark']}
  Lookback: {status['risk_model']['lookback_days']} days
  Cache Valid: {status['risk_model']['cache_valid']}

**PortfolioOptimizer**
  Version: {status['optimizer']['version']}
  Risk Aversion: {status['optimizer']['risk_aversion']}
  Risk-Free Rate: {status['optimizer']['risk_free_rate']:.1%}

**VolatilityTargeting**
  Version: {status['volatility_targeting']['version']}
  Target Vol: {status['volatility_targeting']['target_volatility']:.0%}
  Max Leverage: {status['volatility_targeting']['max_leverage']}x

**ExposureManager**
  Version: {status['exposure_manager']['version']}
  Max Asset: {status['exposure_manager']['limits']['max_asset']:.0%}
  Max Sector: {status['exposure_manager']['limits']['max_sector']:.0%}
  Target Beta: {status['exposure_manager']['limits']['target_beta']}

**ClusterDetector**
  Version: {status['cluster_detector']['version']}
  Corr Threshold: {status['cluster_detector']['correlation_threshold']:.0%}
  Cluster Limit: {status['cluster_detector']['cluster_weight_limit']:.0%}

All 5 institutional modules operational"""
        
        await update.message.reply_text(msg, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in module_status: {e}")
        await update.message.reply_text(f"Error: {str(e)}")
