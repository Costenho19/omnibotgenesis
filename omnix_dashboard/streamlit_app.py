"""
OMNIX V6.5.4 INSTITUTIONAL+ PREMIUM
Streamlit Dashboard - Investor-Grade Visualization

Para presentaciones a inversores UAE/GCC.
Métricas Sharpe, Sortino, Calmar con visualización profesional.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(
    page_title="OMNIX V6.5.4 INSTITUTIONAL+",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

DARK_THEME = {
    'bg': '#0E1117',
    'card': '#1E2130',
    'text': '#FAFAFA',
    'accent': '#00D4AA',
    'positive': '#00D4AA',
    'negative': '#FF6B6B',
    'warning': '#FFD93D',
    'blue': '#4DABF7'
}

st.markdown("""
<style>
    .main {background-color: #0E1117;}
    .metric-card {
        background: linear-gradient(135deg, #1E2130 0%, #2A2F45 100%);
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        border: 1px solid #3D4460;
    }
    .metric-value {
        font-size: 32px;
        font-weight: bold;
        color: #00D4AA;
    }
    .metric-label {
        font-size: 14px;
        color: #8B92A5;
        text-transform: uppercase;
    }
    .header-title {
        font-size: 42px;
        font-weight: 800;
        background: linear-gradient(90deg, #00D4AA, #4DABF7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .sharpe-card {
        background: linear-gradient(135deg, #1a472a 0%, #2d5a3d 100%);
        border: 2px solid #00D4AA;
    }
    .sortino-card {
        background: linear-gradient(135deg, #1a3a4a 0%, #2d4a5a 100%);
        border: 2px solid #4DABF7;
    }
    .calmar-card {
        background: linear-gradient(135deg, #3a1a4a 0%, #4a2d5a 100%);
        border: 2px solid #9B59B6;
    }
</style>
""", unsafe_allow_html=True)


def load_metrics():
    try:
        from omnix_services.analytics.institutional_metrics import (
            InstitutionalMetricsCalculator,
            TradeRecord
        )
        from omnix_services.database_service.database_service import get_database_service
        
        db = get_database_service()
        if not db:
            return None
        
        trades_raw = db.get_closed_trades(limit=500)
        if not trades_raw:
            return None
        
        trades = []
        for t in trades_raw:
            try:
                entry_time = t.get('opened_at') or t.get('entry_time') or datetime.now(timezone.utc)
                exit_time = t.get('closed_at') or t.get('exit_time') or datetime.now(timezone.utc)
                
                if isinstance(entry_time, str):
                    entry_time = datetime.fromisoformat(entry_time.replace('Z', '+00:00'))
                if isinstance(exit_time, str):
                    exit_time = datetime.fromisoformat(exit_time.replace('Z', '+00:00'))
                
                pnl_usd = float(t.get('pnl', 0) or t.get('realized_pnl', 0) or 0)
                entry_price = float(t.get('entry_price', 1) or 1)
                exit_price = float(t.get('exit_price', 0) or entry_price)
                side = t.get('side', 'buy').lower()
                
                if side == 'buy':
                    pnl_pct = (exit_price - entry_price) / entry_price if entry_price else 0
                else:
                    pnl_pct = (entry_price - exit_price) / entry_price if entry_price else 0
                
                trades.append(TradeRecord(
                    symbol=t.get('symbol', 'UNKNOWN'),
                    pnl_usd=pnl_usd,
                    pnl_pct=pnl_pct,
                    entry_time=entry_time,
                    exit_time=exit_time,
                    side=side,
                    size_usd=float(t.get('position_size', 0) or 0)
                ))
            except Exception:
                continue
        
        if not trades:
            return None
        
        calculator = InstitutionalMetricsCalculator()
        return calculator.calculate_portfolio_metrics(trades, "all_time")
        
    except Exception as e:
        st.error(f"Error loading metrics: {e}")
        return None


def load_calibration():
    try:
        from omnix_core.config.trading_profiles import PAIR_CALIBRATIONS
        return PAIR_CALIBRATIONS
    except Exception:
        return {}


def main():
    st.markdown('<p class="header-title">OMNIX V6.5.4 INSTITUTIONAL+</p>', unsafe_allow_html=True)
    st.markdown("### Investor-Grade Trading Analytics Dashboard")
    st.markdown("---")
    
    with st.sidebar:
        st.image("https://via.placeholder.com/150x50/0E1117/00D4AA?text=OMNIX", width=150)
        st.markdown("### Navigation")
        page = st.radio("", ["Overview", "Risk Metrics", "Pair Analysis", "Calibration"])
        st.markdown("---")
        st.markdown("**Last Updated**")
        st.markdown(f"🕐 {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    
    metrics = load_metrics()
    calibration = load_calibration()
    
    if page == "Overview":
        render_overview(metrics)
    elif page == "Risk Metrics":
        render_risk_metrics(metrics)
    elif page == "Pair Analysis":
        render_pair_analysis(metrics)
    elif page == "Calibration":
        render_calibration(calibration)


def render_overview(metrics):
    st.markdown("## Portfolio Overview")
    
    if not metrics:
        st.warning("No trade data available. Run some trades to see metrics.")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Trades", "0")
        with col2:
            st.metric("Win Rate", "0%")
        with col3:
            st.metric("Total P&L", "$0.00")
        with col4:
            st.metric("Sharpe Ratio", "0.00")
        return
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Trades",
            f"{metrics.total_trades:,}",
            delta=f"+{metrics.total_trades}" if metrics.total_trades > 0 else None
        )
    
    with col2:
        win_rate = metrics.win_rate * 100
        color = "normal" if win_rate >= 55 else "inverse"
        st.metric(
            "Win Rate",
            f"{win_rate:.1f}%",
            delta=f"{win_rate - 50:.1f}% vs 50%" if win_rate != 50 else None,
            delta_color=color
        )
    
    with col3:
        pnl_color = "normal" if metrics.total_pnl >= 0 else "inverse"
        st.metric(
            "Total P&L",
            f"${metrics.total_pnl:,.2f}",
            delta_color=pnl_color
        )
    
    with col4:
        sharpe_color = "normal" if metrics.sharpe_ratio >= 1.0 else "inverse"
        st.metric(
            "Sharpe Ratio",
            f"{metrics.sharpe_ratio:.3f}",
            delta="Good" if metrics.sharpe_ratio >= 1.5 else "Needs work" if metrics.sharpe_ratio < 1.0 else "Acceptable",
            delta_color=sharpe_color
        )
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### P&L by Pair")
        if metrics.pair_metrics:
            pairs = list(metrics.pair_metrics.keys())
            pnls = [pm.total_pnl for pm in metrics.pair_metrics.values()]
            colors = [DARK_THEME['positive'] if p >= 0 else DARK_THEME['negative'] for p in pnls]
            
            fig = go.Figure(data=[
                go.Bar(x=pairs, y=pnls, marker_color=colors)
            ])
            fig.update_layout(
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=300,
                margin=dict(l=20, r=20, t=20, b=40)
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### Win Rate by Pair")
        if metrics.pair_metrics:
            pairs = list(metrics.pair_metrics.keys())
            win_rates = [pm.win_rate * 100 for pm in metrics.pair_metrics.values()]
            
            fig = go.Figure(data=[
                go.Bar(x=pairs, y=win_rates, marker_color=DARK_THEME['blue'])
            ])
            fig.add_hline(y=55, line_dash="dash", line_color=DARK_THEME['positive'], annotation_text="Target 55%")
            fig.update_layout(
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=300,
                yaxis_title="Win Rate %",
                margin=dict(l=20, r=20, t=20, b=40)
            )
            st.plotly_chart(fig, use_container_width=True)


def render_risk_metrics(metrics):
    st.markdown("## Risk-Adjusted Performance Metrics")
    st.markdown("*Industry-standard metrics used by Citadel, Millennium, Two Sigma*")
    
    if not metrics:
        st.warning("No trade data available")
        return
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="metric-card sharpe-card">
            <p class="metric-label">Sharpe Ratio</p>
            <p class="metric-value">{:.3f}</p>
            <p style="color: #8B92A5; font-size: 12px;">Return / Total Risk</p>
        </div>
        """.format(metrics.sharpe_ratio), unsafe_allow_html=True)
        
        interpretation = "Excellent" if metrics.sharpe_ratio >= 2.0 else \
                        "Good" if metrics.sharpe_ratio >= 1.0 else \
                        "Fair" if metrics.sharpe_ratio >= 0.5 else "Poor"
        st.info(f"Interpretation: **{interpretation}**")
    
    with col2:
        st.markdown("""
        <div class="metric-card sortino-card">
            <p class="metric-label">Sortino Ratio</p>
            <p class="metric-value" style="color: #4DABF7;">{:.3f}</p>
            <p style="color: #8B92A5; font-size: 12px;">Return / Downside Risk</p>
        </div>
        """.format(metrics.sortino_ratio), unsafe_allow_html=True)
        
        interpretation = "Excellent" if metrics.sortino_ratio >= 3.0 else \
                        "Good" if metrics.sortino_ratio >= 1.5 else \
                        "Fair" if metrics.sortino_ratio >= 0.5 else "Poor"
        st.info(f"Interpretation: **{interpretation}**")
    
    with col3:
        st.markdown("""
        <div class="metric-card calmar-card">
            <p class="metric-label">Calmar Ratio</p>
            <p class="metric-value" style="color: #9B59B6;">{:.3f}</p>
            <p style="color: #8B92A5; font-size: 12px;">Annualized Return / Max DD</p>
        </div>
        """.format(metrics.calmar_ratio), unsafe_allow_html=True)
        
        interpretation = "Excellent" if metrics.calmar_ratio >= 3.0 else \
                        "Good" if metrics.calmar_ratio >= 1.0 else \
                        "Fair" if metrics.calmar_ratio >= 0.5 else "Needs work"
        st.info(f"Interpretation: **{interpretation}**")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Risk Indicators")
        st.metric("Max Drawdown", f"{metrics.max_drawdown * 100:.2f}%")
        st.metric("Profit Factor", f"{metrics.profit_factor:.2f}")
    
    with col2:
        st.markdown("### Performance Grade")
        grade = 'A' if metrics.sharpe_ratio >= 2.0 else \
                'B' if metrics.sharpe_ratio >= 1.0 else \
                'C' if metrics.sharpe_ratio >= 0.5 else 'D'
        
        grade_colors = {'A': '#00D4AA', 'B': '#4DABF7', 'C': '#FFD93D', 'D': '#FF6B6B'}
        
        st.markdown(f"""
        <div style="text-align: center; padding: 40px;">
            <div style="font-size: 120px; font-weight: bold; color: {grade_colors[grade]};">{grade}</div>
            <p style="color: #8B92A5;">Overall Performance Grade</p>
        </div>
        """, unsafe_allow_html=True)


def render_pair_analysis(metrics):
    st.markdown("## Per-Pair Performance Analysis")
    
    if not metrics or not metrics.pair_metrics:
        st.warning("No pair data available")
        return
    
    data = []
    for symbol, pm in metrics.pair_metrics.items():
        data.append({
            'Symbol': symbol,
            'Trades': pm.total_trades,
            'Win Rate': f"{pm.win_rate * 100:.1f}%",
            'Total P&L': f"${pm.total_pnl:.2f}",
            'Sharpe': f"{pm.sharpe_ratio:.3f}",
            'Sortino': f"{pm.sortino_ratio:.3f}",
            'Calmar': f"{pm.calmar_ratio:.3f}",
            'Profit Factor': f"{pm.profit_factor:.2f}",
            'Max DD': f"{pm.max_drawdown * 100:.2f}%"
        })
    
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    symbols = list(metrics.pair_metrics.keys())
    selected = st.selectbox("Select pair for detailed analysis", symbols)
    
    if selected:
        pm = metrics.pair_metrics[selected]
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Avg Win", f"${pm.avg_win:.2f}")
        with col2:
            st.metric("Avg Loss", f"${pm.avg_loss:.2f}")
        with col3:
            st.metric("Largest Win", f"${pm.largest_win:.2f}")
        with col4:
            st.metric("Largest Loss", f"${pm.largest_loss:.2f}")


def render_calibration(calibration):
    st.markdown("## WIN_RATE_OPTIMIZED V2 PREMIUM Calibration")
    st.markdown("*Per-pair calibration with circuit breakers*")
    
    if not calibration:
        st.warning("Calibration data not available")
        return
    
    data = []
    for symbol, cal in calibration.items():
        tier = cal.tier.value if hasattr(cal.tier, 'value') else str(cal.tier)
        
        if tier == 'EXCLUDED':
            continue
        
        data.append({
            'Symbol': symbol,
            'Tier': tier,
            'Stop Loss': f"{cal.stop_loss_pct * 100:.1f}%",
            'Take Profit': f"{cal.take_profit_pct * 100:.1f}%",
            'R:R Ratio': f"{cal.risk_reward_ratio:.2f}",
            'Max Position': f"${cal.max_position_usd:,.0f}",
            'Portfolio Weight': f"{cal.portfolio_weight * 100:.0f}%",
            'Circuit Breaker': f"{cal.max_daily_drawdown_pct * 100:.1f}%"
        })
    
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Portfolio Allocation")
        weights = [cal.portfolio_weight for cal in calibration.values() if hasattr(cal.tier, 'value') and cal.tier.value != 'EXCLUDED']
        labels = [s for s, cal in calibration.items() if hasattr(cal.tier, 'value') and cal.tier.value != 'EXCLUDED']
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=weights,
            hole=0.4,
            marker_colors=[DARK_THEME['positive'], DARK_THEME['blue'], '#9B59B6', '#FFD93D']
        )])
        fig.update_layout(
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            height=300
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### Circuit Breaker Limits")
        for symbol, cal in calibration.items():
            if hasattr(cal.tier, 'value') and cal.tier.value != 'EXCLUDED':
                dd_limit = cal.max_daily_drawdown_pct * 100
                color = DARK_THEME['positive'] if dd_limit >= 2.0 else DARK_THEME['warning']
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; padding: 10px; border-bottom: 1px solid #3D4460;">
                    <span>{symbol}</span>
                    <span style="color: {color}; font-weight: bold;">{dd_limit:.1f}% max DD/day</span>
                </div>
                """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
