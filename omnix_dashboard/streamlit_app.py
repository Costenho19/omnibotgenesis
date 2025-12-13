"""
OMNIX V6.5.4 INSTITUTIONAL+ PREMIUM
Streamlit Dashboard - Investor-Grade Visualization

Para presentaciones a inversores UAE/GCC.
Métricas Sharpe, Sortino, Calmar con visualización profesional.

DEPLOYMENT:
- Development: streamlit run omnix_dashboard/streamlit_app.py --server.port 8501
- Railway: railway up --service omnix-dashboard
- Set OMNIX_API_URL to point to the Flask API service
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from omnix_dashboard.api_client import get_api_client
from omnix_config import VERSION_BANNER

st.set_page_config(
    page_title=f"OMNIX {VERSION_BANNER}",
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
        client = get_api_client()
        response = client.get_institutional_metrics()
        
        if not response.get('success'):
            return None
        
        return response.get('metrics')
        
    except Exception as e:
        st.error(f"Error loading metrics: {e}")
        return None


def load_calibration():
    try:
        client = get_api_client()
        response = client.get_calibration()
        
        if not response.get('success'):
            return {}
        
        return response.get('calibration', {})
        
    except Exception as e:
        st.error(f"Error loading calibration: {e}")
        return {}


def main():
    st.markdown(f'<p class="header-title">OMNIX {VERSION_BANNER}</p>', unsafe_allow_html=True)
    st.markdown("### Investor-Grade Trading Analytics Dashboard")
    st.markdown("---")
    
    with st.sidebar:
        st.markdown(f"""
        <div style="padding: 10px 0; margin-bottom: 15px;">
            <span style="font-size: 28px; font-weight: 800; 
                background: linear-gradient(90deg, #00D4AA, #4DABF7);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;">
                OMNIX
            </span>
            <span style="font-size: 12px; color: #8B92A5; margin-left: 5px;">{VERSION_BANNER}</span>
        </div>
        """, unsafe_allow_html=True)
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
    
    total_trades = metrics.get('total_trades', 0)
    win_rate = metrics.get('win_rate', 0)
    total_pnl = metrics.get('total_pnl', 0)
    sharpe_ratio = metrics.get('sharpe_ratio', 0)
    pair_metrics = metrics.get('pair_metrics', {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Trades",
            f"{total_trades:,}",
            delta=f"+{total_trades}" if total_trades > 0 else None
        )
    
    with col2:
        color = "normal" if win_rate >= 55 else "inverse"
        st.metric(
            "Win Rate",
            f"{win_rate:.1f}%",
            delta=f"{win_rate - 50:.1f}% vs 50%" if win_rate != 50 else None,
            delta_color=color
        )
    
    with col3:
        pnl_color = "normal" if total_pnl >= 0 else "inverse"
        st.metric(
            "Total P&L",
            f"${total_pnl:,.2f}",
            delta_color=pnl_color
        )
    
    with col4:
        sharpe_color = "normal" if sharpe_ratio >= 1.0 else "inverse"
        st.metric(
            "Sharpe Ratio",
            f"{sharpe_ratio:.3f}",
            delta="Good" if sharpe_ratio >= 1.5 else "Needs work" if sharpe_ratio < 1.0 else "Acceptable",
            delta_color=sharpe_color
        )
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### P&L by Pair")
        if pair_metrics:
            pairs = list(pair_metrics.keys())
            pnls = [pm.get('total_pnl', 0) for pm in pair_metrics.values()]
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
        if pair_metrics:
            pairs = list(pair_metrics.keys())
            win_rates = [pm.get('win_rate', 0) for pm in pair_metrics.values()]
            
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
    
    sharpe_ratio = metrics.get('sharpe_ratio', 0)
    sortino_ratio = metrics.get('sortino_ratio', 0)
    calmar_ratio = metrics.get('calmar_ratio', 0)
    max_drawdown = metrics.get('max_drawdown', 0)
    profit_factor = metrics.get('profit_factor', 0)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="metric-card sharpe-card">
            <p class="metric-label">Sharpe Ratio</p>
            <p class="metric-value">{:.3f}</p>
            <p style="color: #8B92A5; font-size: 12px;">Return / Total Risk</p>
        </div>
        """.format(sharpe_ratio), unsafe_allow_html=True)
        
        interpretation = "Excellent" if sharpe_ratio >= 2.0 else \
                        "Good" if sharpe_ratio >= 1.0 else \
                        "Fair" if sharpe_ratio >= 0.5 else "Poor"
        st.info(f"Interpretation: **{interpretation}**")
    
    with col2:
        st.markdown("""
        <div class="metric-card sortino-card">
            <p class="metric-label">Sortino Ratio</p>
            <p class="metric-value" style="color: #4DABF7;">{:.3f}</p>
            <p style="color: #8B92A5; font-size: 12px;">Return / Downside Risk</p>
        </div>
        """.format(sortino_ratio), unsafe_allow_html=True)
        
        interpretation = "Excellent" if sortino_ratio >= 3.0 else \
                        "Good" if sortino_ratio >= 1.5 else \
                        "Fair" if sortino_ratio >= 0.5 else "Poor"
        st.info(f"Interpretation: **{interpretation}**")
    
    with col3:
        st.markdown("""
        <div class="metric-card calmar-card">
            <p class="metric-label">Calmar Ratio</p>
            <p class="metric-value" style="color: #9B59B6;">{:.3f}</p>
            <p style="color: #8B92A5; font-size: 12px;">Annualized Return / Max DD</p>
        </div>
        """.format(calmar_ratio), unsafe_allow_html=True)
        
        interpretation = "Excellent" if calmar_ratio >= 3.0 else \
                        "Good" if calmar_ratio >= 1.0 else \
                        "Fair" if calmar_ratio >= 0.5 else "Needs work"
        st.info(f"Interpretation: **{interpretation}**")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Risk Indicators")
        st.metric("Max Drawdown", f"{max_drawdown:.2f}%")
        st.metric("Profit Factor", f"{profit_factor:.2f}")
    
    with col2:
        st.markdown("### Performance Grade")
        grade = 'A' if sharpe_ratio >= 2.0 else \
                'B' if sharpe_ratio >= 1.0 else \
                'C' if sharpe_ratio >= 0.5 else 'D'
        
        grade_colors = {'A': '#00D4AA', 'B': '#4DABF7', 'C': '#FFD93D', 'D': '#FF6B6B'}
        
        st.markdown(f"""
        <div style="text-align: center; padding: 40px;">
            <div style="font-size: 120px; font-weight: bold; color: {grade_colors[grade]};">{grade}</div>
            <p style="color: #8B92A5;">Overall Performance Grade</p>
        </div>
        """, unsafe_allow_html=True)


def render_pair_analysis(metrics):
    st.markdown("## Per-Pair Performance Analysis")
    
    pair_metrics = metrics.get('pair_metrics', {}) if metrics else {}
    
    if not pair_metrics:
        st.warning("No pair data available")
        return
    
    data = []
    for symbol, pm in pair_metrics.items():
        data.append({
            'Symbol': symbol,
            'Trades': pm.get('total_trades', 0),
            'Win Rate': f"{pm.get('win_rate', 0):.1f}%",
            'Total P&L': f"${pm.get('total_pnl', 0):.2f}",
            'Sharpe': f"{pm.get('sharpe_ratio', 0):.3f}",
            'Sortino': f"{pm.get('sortino_ratio', 0):.3f}",
            'Calmar': f"{pm.get('calmar_ratio', 0):.3f}",
            'Profit Factor': f"{pm.get('profit_factor', 0):.2f}",
            'Max DD': f"{pm.get('max_drawdown', 0):.2f}%"
        })
    
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    symbols = list(pair_metrics.keys())
    selected = st.selectbox("Select pair for detailed analysis", symbols)
    
    if selected:
        pm = pair_metrics[selected]
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Avg Win", f"${pm.get('avg_win', 0):.2f}")
        with col2:
            st.metric("Avg Loss", f"${pm.get('avg_loss', 0):.2f}")
        with col3:
            st.metric("Largest Win", f"${pm.get('largest_win', 0):.2f}")
        with col4:
            st.metric("Largest Loss", f"${pm.get('largest_loss', 0):.2f}")


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
