"""
OMNIX V6.5.4 INSTITUTIONAL+ PREMIUM
Streamlit Dashboard - Investor-Grade Visualization

For investor presentations in UAE/GCC.
Sharpe, Sortino, Calmar metrics with professional visualization.

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


@st.cache_data(ttl=60)
def load_metrics():
    """Load institutional metrics with 60s cache for faster loading"""
    try:
        client = get_api_client()
        response = client.get_institutional_metrics()
        
        if not response.get('success'):
            return None
        
        return response.get('metrics')
        
    except Exception as e:
        st.error(f"Error loading metrics: {e}")
        return None


@st.cache_data(ttl=60)
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


@st.cache_data(ttl=60)
def load_quarantine():
    """Load quarantine data with 60s cache"""
    try:
        client = get_api_client()
        response = client.get_quarantine()
        
        if not response.get('success'):
            return {}
        
        return response.get('quarantine', {})
        
    except Exception as e:
        st.error(f"Error loading quarantine data: {e}")
        return {}


@st.cache_data(ttl=60)
def load_shadow_portfolio():
    """Load shadow portfolio with 60s cache"""
    try:
        client = get_api_client()
        response = client.get_shadow_portfolio()
        
        if not response.get('success'):
            return {}
        
        return response.get('shadow_portfolio', {})
        
    except Exception as e:
        st.error(f"Error loading shadow portfolio data: {e}")
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
        page = st.radio("", ["Overview", "Risk Metrics", "Expectancy", "Pair Analysis", "Shadow Analytics", "Shadow Portfolio", "Asset Quarantine", "Calibration"])
        st.markdown("---")
        st.markdown("**Last Updated**")
        st.markdown(f"🕐 {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    
    metrics = load_metrics()
    calibration = load_calibration()
    quarantine = load_quarantine()
    shadow_portfolio = load_shadow_portfolio()
    
    if page == "Overview":
        render_overview(metrics, quarantine)
    elif page == "Risk Metrics":
        render_risk_metrics(metrics)
    elif page == "Expectancy":
        render_expectancy()
    elif page == "Pair Analysis":
        render_pair_analysis(metrics)
    elif page == "Shadow Analytics":
        render_shadow_analytics()
    elif page == "Shadow Portfolio":
        render_shadow_portfolio(shadow_portfolio)
    elif page == "Asset Quarantine":
        render_quarantine(quarantine)
    elif page == "Calibration":
        render_calibration(calibration)


@st.cache_data(ttl=300)
def load_shadow_analytics_data():
    """Load shadow analytics data from v_shadow_trade_metrics VIEW (ADR-021).
    
    Single data source for all shadow analytics:
    - decision_trace is treated as semi-structured historical text
    - regex parsing is intentionally permissive (see ADR-021)
    """
    from omnix_dashboard.utils.database import get_db_connection
    
    data = {
        'overview': {},
        'wr_histogram': [],
        'coherence_by_symbol': [],
        'coherence_vs_dci': [],
        'ecw_waiting_events': [],
        'low_coherence_events': [],
        'top_vetos': [],
        'data_timestamp': None,
        'error': None
    }
    
    try:
        with get_db_connection() as conn:
            if not conn:
                data['error'] = "Database connection unavailable"
                return data
            
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_events,
                    ROUND(AVG(mc_win_rate), 2) as avg_wr,
                    ROUND(AVG(coherence_score), 2) as avg_coherence,
                    ROUND(100.0 * COUNT(CASE WHEN ecw_status = 'WAITING' THEN 1 END) / NULLIF(COUNT(*), 0), 2) as pct_ecw_blocked,
                    MAX(created_at) as last_event
                FROM v_shadow_trade_metrics
            """)
            row = cursor.fetchone()
            if row:
                data['overview'] = {
                    'total_events': row[0] or 0,
                    'avg_wr': float(row[1]) if row[1] else 50.0,
                    'avg_coherence': float(row[2]) if row[2] else 0.0,
                    'pct_ecw_blocked': float(row[3]) if row[3] else 0.0
                }
                data['data_timestamp'] = row[4]
            
            cursor.execute("""
                SELECT 
                    FLOOR(mc_win_rate / 5) * 5 as wr_bucket,
                    COUNT(*) as event_count
                FROM v_shadow_trade_metrics
                WHERE mc_win_rate IS NOT NULL
                GROUP BY FLOOR(mc_win_rate / 5) * 5
                ORDER BY wr_bucket
            """)
            data['wr_histogram'] = [{'bucket': row[0], 'count': row[1]} for row in cursor.fetchall()]
            
            cursor.execute("""
                SELECT 
                    symbol,
                    ROUND(AVG(coherence_score), 1) as avg_coherence,
                    COUNT(*) as events
                FROM v_shadow_trade_metrics
                GROUP BY symbol
                ORDER BY avg_coherence DESC
            """)
            data['coherence_by_symbol'] = [
                {'symbol': row[0], 'avg_coherence': float(row[1]) if row[1] else 0, 'events': row[2]}
                for row in cursor.fetchall()
            ]
            
            cursor.execute("""
                SELECT coherence_score, approx_dci, symbol
                FROM v_shadow_trade_metrics
                WHERE coherence_score IS NOT NULL AND approx_dci IS NOT NULL
                ORDER BY RANDOM()
                LIMIT 500
            """)
            data['coherence_vs_dci'] = [
                {'coherence': float(row[0]), 'dci': float(row[1]), 'symbol': row[2]}
                for row in cursor.fetchall()
            ]
            
            cursor.execute("""
                SELECT symbol, created_at, mc_win_rate, mc_expected_return, ecw_cycles, blocked_capital
                FROM v_shadow_trade_metrics
                WHERE ecw_status = 'WAITING'
                ORDER BY created_at DESC
                LIMIT 20
            """)
            data['ecw_waiting_events'] = [
                {
                    'symbol': row[0],
                    'created_at': row[1],
                    'mc_win_rate': float(row[2]) if row[2] else 50.0,
                    'mc_expected_return': float(row[3]) if row[3] else 0.0,
                    'ecw_cycles': row[4] or 0,
                    'blocked_capital': float(row[5]) if row[5] else 0.0
                }
                for row in cursor.fetchall()
            ]
            
            cursor.execute("""
                SELECT symbol, created_at, coherence_score, approx_dci, mc_win_rate, veto_type
                FROM v_shadow_trade_metrics
                WHERE coherence_score < 40
                ORDER BY created_at DESC
                LIMIT 20
            """)
            data['low_coherence_events'] = [
                {
                    'symbol': row[0],
                    'created_at': row[1],
                    'coherence': float(row[2]) if row[2] else 0,
                    'dci': float(row[3]) if row[3] else 0,
                    'wr': float(row[4]) if row[4] else 50.0,
                    'veto_type': row[5]
                }
                for row in cursor.fetchall()
            ]
            
            cursor.execute("""
                SELECT 
                    veto_type,
                    COUNT(*) as count,
                    ROUND(SUM(blocked_capital), 2) as total_blocked
                FROM v_shadow_trade_metrics
                WHERE veto_type IS NOT NULL AND veto_type != ''
                GROUP BY veto_type
                ORDER BY count DESC
                LIMIT 10
            """)
            data['top_vetos'] = [
                {'veto_type': row[0], 'count': row[1], 'blocked': float(row[2]) if row[2] else 0}
                for row in cursor.fetchall()
            ]
            
    except Exception as e:
        data['error'] = str(e)
    
    return data


def render_shadow_analytics():
    """Shadow Analytics Dashboard - ADR-021
    
    Answers: "How does OMNIX decide and why does it NOT trade?"
    Data source: v_shadow_trade_metrics VIEW (read-only, non-operational)
    """
    st.markdown("## Shadow Analytics")
    st.markdown("*Non-operational decision analysis - How OMNIX decides and why it does NOT trade*")
    
    data = load_shadow_analytics_data()
    
    if data.get('error'):
        st.error(f"Unable to load shadow analytics: {data['error']}")
        return
    
    overview = data.get('overview', {})
    
    st.markdown("### System Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Shadow Events",
            f"{overview.get('total_events', 0):,}",
            delta="ANALYTICAL",
            delta_color="off"
        )
    
    with col2:
        wr = overview.get('avg_wr', 50.0)
        color = "normal" if wr >= 50 else "inverse"
        st.metric(
            "Avg Win Rate (Parsed)",
            f"{wr:.1f}%",
            delta="From decision_trace",
            delta_color=color
        )
    
    with col3:
        coh = overview.get('avg_coherence', 0)
        color = "normal" if coh >= 40 else "inverse"
        st.metric(
            "Avg Coherence Score",
            f"{coh:.1f}%",
            delta="Signal quality",
            delta_color=color
        )
    
    with col4:
        blocked = overview.get('pct_ecw_blocked', 0)
        st.metric(
            "% ECW Blocked",
            f"{blocked:.1f}%",
            delta="Capital preservation",
            delta_color="normal"
        )
    
    if data.get('data_timestamp'):
        ts = data['data_timestamp']
        if hasattr(ts, 'strftime'):
            ts_str = ts.strftime('%Y-%m-%d %H:%M UTC')
        else:
            ts_str = str(ts)
        st.caption(f"Data as of: {ts_str}")
    
    st.markdown("---")
    
    st.markdown("### Decision Quality Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Win Rate Distribution")
        wr_data = data.get('wr_histogram', [])
        if wr_data:
            buckets = [f"{int(d['bucket'])}-{int(d['bucket']+5)}%" for d in wr_data]
            counts = [d['count'] for d in wr_data]
            
            fig = go.Figure(data=[
                go.Bar(x=buckets, y=counts, marker_color=DARK_THEME['blue'])
            ])
            fig.add_vline(x="50-55%", line_dash="dash", line_color=DARK_THEME['positive'], 
                         annotation_text="50% threshold")
            fig.update_layout(
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=300,
                xaxis_title="Win Rate Bucket",
                yaxis_title="Event Count",
                margin=dict(l=20, r=20, t=20, b=40)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No win rate data available")
    
    with col2:
        st.markdown("#### Coherence by Symbol")
        coh_data = data.get('coherence_by_symbol', [])
        if coh_data:
            symbols = [d['symbol'] for d in coh_data]
            coherences = [d['avg_coherence'] for d in coh_data]
            colors = [DARK_THEME['positive'] if c >= 50 else DARK_THEME['warning'] if c >= 40 else DARK_THEME['negative'] for c in coherences]
            
            fig = go.Figure(data=[
                go.Bar(x=symbols, y=coherences, marker_color=colors)
            ])
            fig.add_hline(y=40, line_dash="dash", line_color=DARK_THEME['warning'], 
                         annotation_text="Min threshold 40%")
            fig.update_layout(
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=300,
                xaxis_title="Symbol",
                yaxis_title="Avg Coherence %",
                margin=dict(l=20, r=20, t=20, b=40)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No coherence data available")
    
    st.markdown("#### Coherence vs DCI (Decision Contradiction Index)")
    scatter_data = data.get('coherence_vs_dci', [])
    if scatter_data:
        coherences = [d['coherence'] for d in scatter_data]
        dcis = [d['dci'] for d in scatter_data]
        symbols = [d['symbol'] for d in scatter_data]
        
        symbol_colors = {s: c for s, c in zip(set(symbols), [DARK_THEME['positive'], DARK_THEME['blue'], '#9B59B6', DARK_THEME['warning']])}
        colors = [symbol_colors.get(s, DARK_THEME['blue']) for s in symbols]
        
        fig = go.Figure(data=[
            go.Scatter(
                x=coherences, y=dcis, mode='markers',
                marker=dict(color=colors, size=6, opacity=0.6),
                text=symbols, hovertemplate='%{text}<br>Coherence: %{x:.1f}%<br>DCI: %{y:.1f}<extra></extra>'
            )
        ])
        fig.add_hline(y=70, line_dash="dash", line_color=DARK_THEME['negative'], 
                     annotation_text="DCI ≥70 = CONTRADICTORY")
        fig.add_hline(y=35, line_dash="dash", line_color=DARK_THEME['warning'], 
                     annotation_text="DCI 35-69 = TENSIONED")
        fig.update_layout(
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=400,
            xaxis_title="Coherence Score %",
            yaxis_title="DCI (Decision Contradiction Index)",
            margin=dict(l=20, r=20, t=20, b=40)
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("""
        **Reading the scatter:**
        - **Bottom-left**: Low coherence + Low DCI → Weak but aligned signals
        - **Top-left**: Low coherence + High DCI → CONTRADICTORY (system should HOLD)
        - **Bottom-right**: High coherence + Low DCI → ALIGNED (best conditions)
        - **Top-right**: High coherence + High DCI → Rare, signals conflict despite strength
        """)
    else:
        st.info("No coherence vs DCI data available")
    
    st.markdown("---")
    
    st.markdown("### Governance & Risk Tables")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### ECW Waiting Events (Blocked)")
        ecw_events = data.get('ecw_waiting_events', [])
        if ecw_events:
            df_ecw = pd.DataFrame(ecw_events)
            df_ecw['created_at'] = pd.to_datetime(df_ecw['created_at']).dt.strftime('%m-%d %H:%M')
            df_ecw = df_ecw.rename(columns={
                'created_at': 'Time',
                'symbol': 'Symbol',
                'mc_win_rate': 'WR%',
                'mc_expected_return': 'ER%',
                'ecw_cycles': 'Cycles',
                'blocked_capital': 'Blocked$'
            })
            st.dataframe(df_ecw[['Time', 'Symbol', 'WR%', 'ER%', 'Cycles', 'Blocked$']], 
                        use_container_width=True, hide_index=True, height=300)
        else:
            st.success("No ECW waiting events - edge confirmation active")
    
    with col2:
        st.markdown("#### Low Coherence Events (<40%)")
        low_coh = data.get('low_coherence_events', [])
        if low_coh:
            df_low = pd.DataFrame(low_coh)
            df_low['created_at'] = pd.to_datetime(df_low['created_at']).dt.strftime('%m-%d %H:%M')
            df_low = df_low.rename(columns={
                'created_at': 'Time',
                'symbol': 'Symbol',
                'coherence': 'Coh%',
                'dci': 'DCI',
                'wr': 'WR%',
                'veto_type': 'Veto'
            })
            st.dataframe(df_low[['Time', 'Symbol', 'Coh%', 'DCI', 'WR%', 'Veto']], 
                        use_container_width=True, hide_index=True, height=300)
        else:
            st.success("No low coherence events - signal quality maintained")
    
    st.markdown("#### Top Veto Signals")
    top_vetos = data.get('top_vetos', [])
    if top_vetos:
        df_vetos = pd.DataFrame(top_vetos)
        df_vetos = df_vetos.rename(columns={
            'veto_type': 'Veto Type',
            'count': 'Events',
            'blocked': 'Capital Blocked ($)'
        })
        st.dataframe(df_vetos, use_container_width=True, hide_index=True)
    else:
        st.info("No veto signal data available")
    
    st.markdown("---")
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                border: 1px solid #3D4460; border-radius: 8px; padding: 15px; margin-top: 20px;">
        <p style="color: #8B92A5; font-size: 12px; margin: 0;">
            <strong>DATA SOURCE DISCLAIMER:</strong> This dashboard reflects non-operational shadow analytics 
            derived from historical decision traces (<code>v_shadow_trade_metrics</code> VIEW, ADR-021). 
            No live trading or execution logic is connected to this view. 
            Regex parsing is intentionally permissive to preserve forward compatibility of decision_trace semantics.
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_shadow_portfolio(shadow_portfolio):
    st.markdown("## Shadow Portfolio Analysis")
    st.markdown("*Counterfactual analysis of vetoed trades - Filter Learning System*")
    
    if not shadow_portfolio:
        st.info("No shadow portfolio data available yet. The system will populate this after analyzing vetoed trades.")
        st.markdown("""
        **How it works:**
        1. When a trade is blocked by a veto (Monte Carlo, Coherence, Black Swan, etc.), the system logs the trade details
        2. After 24+ hours, the Shadow Portfolio Runner analyzes what would have happened
        3. This data helps calibrate filters to optimize the balance between protection and opportunity
        """)
        return
    
    summary = shadow_portfolio.get('summary', {})
    veto_accuracy = shadow_portfolio.get('veto_accuracy', [])
    missed_opportunities = shadow_portfolio.get('missed_opportunities', [])
    calibration = shadow_portfolio.get('calibration_recommendations', [])
    
    total_analyzed = summary.get('total_analyzed', 0)
    correct_vetos = summary.get('correct_vetos', 0)
    incorrect_vetos = summary.get('incorrect_vetos', 0)
    accuracy_pct = summary.get('accuracy_pct', 0)
    potential_missed = summary.get('potential_profit_missed', 0)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Trades Analyzed",
            f"{total_analyzed:,}",
            delta="COUNTERFACTUAL",
            delta_color="off"
        )
    
    with col2:
        color = "normal" if accuracy_pct >= 60 else "inverse"
        st.metric(
            "Veto Accuracy",
            f"{accuracy_pct:.1f}%",
            delta=f"{correct_vetos} correct / {incorrect_vetos} incorrect",
            delta_color=color
        )
    
    with col3:
        st.metric(
            "Correct Vetos",
            f"{correct_vetos:,}",
            delta="CAPITAL SAVED",
            delta_color="normal"
        )
    
    with col4:
        st.metric(
            "Potential Missed",
            f"{potential_missed:.1f}%",
            delta="OPPORTUNITY COST",
            delta_color="inverse" if potential_missed > 10 else "normal"
        )
    
    st.markdown("---")
    
    if veto_accuracy:
        st.markdown("### Accuracy by Veto Type")
        
        veto_types = [v['veto_type'] for v in veto_accuracy]
        accuracies = [v['accuracy_pct'] for v in veto_accuracy]
        totals = [v['total'] for v in veto_accuracy]
        
        colors = [DARK_THEME['positive'] if a >= 60 else DARK_THEME['warning'] if a >= 40 else DARK_THEME['negative'] for a in accuracies]
        
        fig = go.Figure(data=[
            go.Bar(
                x=veto_types,
                y=accuracies,
                marker_color=colors,
                text=[f"{a:.1f}%<br>({t} trades)" for a, t in zip(accuracies, totals)],
                textposition='auto'
            )
        ])
        fig.add_hline(y=60, line_dash="dash", line_color=DARK_THEME['positive'], annotation_text="Target 60%")
        fig.update_layout(
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=350,
            yaxis_title="Accuracy %",
            xaxis_title="Veto Type",
            margin=dict(l=20, r=20, t=20, b=40)
        )
        st.plotly_chart(fig, use_container_width=True)
        
        for v in veto_accuracy:
            if v['accuracy_pct'] < 50:
                st.warning(f"**{v['veto_type']}** has low accuracy ({v['accuracy_pct']:.1f}%) - consider loosening threshold")
    
    st.markdown("---")
    
    if missed_opportunities:
        st.markdown("### Top Missed Opportunities")
        st.markdown("*Trades that were blocked but would have been profitable*")
        
        for opp in missed_opportunities[:5]:
            symbol = opp.get('symbol', 'Unknown')
            action = opp.get('action', 'BUY')
            gain = opp.get('would_have_gained_pct', 0)
            blocked_by = opp.get('blocked_by', 'UNKNOWN')
            
            color = DARK_THEME['positive'] if gain > 3 else DARK_THEME['blue']
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #1a2a1a 0%, #2a3a2a 100%); 
                        border: 1px solid {color}; border-radius: 10px; padding: 15px; margin: 10px 0;">
                <span style="font-size: 18px; font-weight: bold; color: {color};">{symbol} {action}</span>
                <span style="float: right; color: #888;">Blocked by {blocked_by}</span>
                <br/>
                <span style="color: {DARK_THEME['positive']}; font-weight: bold; font-size: 24px;">+{gain:.2f}%</span>
                <span style="color: #888; margin-left: 10px;">would have gained</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("No significant missed opportunities detected - filters are well calibrated!")
    
    st.markdown("---")
    
    if calibration:
        st.markdown("### Filter Calibration Recommendations")
        
        data = []
        for cal in calibration:
            data.append({
                'Filter': cal.get('filter', 'Unknown'),
                'Current': f"{cal.get('current', 0):.2f}" if cal.get('current') else '--',
                'Recommended': f"{cal.get('recommended', 0):.2f}" if cal.get('recommended') else '--',
                'Action': cal.get('action', 'KEEP'),
                'Accuracy': f"{cal.get('accuracy_pct', 0):.1f}%",
                'Trades': cal.get('trades_analyzed', 0)
            })
        
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.markdown("### Why This Matters for Investors")
    st.markdown("""
    The **Shadow Portfolio System** implements institutional-grade counterfactual analysis:
    
    - **Every blocked trade is tracked** and analyzed 24-30 days later
    - **Veto accuracy** shows whether our risk filters are protecting capital effectively
    - **Missed opportunities** identify if filters are too conservative
    - **Calibration recommendations** use data to optimize filter thresholds
    
    This data-driven approach ensures our risk management evolves based on real market outcomes,
    not just theoretical models. The system **learns from its own decisions**.
    """)


def render_quarantine(quarantine):
    st.markdown("## Asset Quarantine")
    st.markdown("*Assets blocked from trading due to poor performance - Capital Protection System*")
    
    if not quarantine:
        st.warning("No quarantine data available")
        return
    
    total_blocked = quarantine.get('total_blocked', 0)
    total_avoided = quarantine.get('total_loss_avoided', 0)
    assets = quarantine.get('assets', [])
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Assets Blocked",
            f"{total_blocked}",
            delta="QUARANTINED",
            delta_color="normal"
        )
    
    with col2:
        st.metric(
            "Loss Avoided",
            f"${total_avoided:,.2f}",
            delta="FROM QUARANTINED ASSETS",
            delta_color="normal",
            help="Actual losses from trades on quarantined assets before they were blocked."
        )
    
    with col3:
        st.metric(
            "Protection Status",
            "ACTIVE",
            delta="24/7 MONITORING",
            delta_color="normal"
        )
    
    st.markdown("---")
    st.markdown("### Blocked Assets Detail")
    
    if assets:
        for asset in assets:
            symbol = asset.get('symbol', 'Unknown')
            reason = asset.get('reason', 'Performance issue')
            loss = asset.get('loss_avoided', 0)
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #2a1a1a 0%, #3a1a1a 100%); 
                        border: 1px solid #ff4b4b; border-radius: 10px; padding: 15px; margin: 10px 0;">
                <span style="font-size: 18px; font-weight: bold; color: #ff6b6b;">🚫 {symbol}</span>
                <br/>
                <span style="color: #888;">{reason}</span>
                <br/>
                <span style="color: #00D4AA; font-weight: bold;">Loss Avoided: ${loss:,.2f}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No assets currently in quarantine")
    
    st.markdown("---")
    st.markdown("### Why This Matters for Investors")
    st.markdown("""
    The **Asset Quarantine System** automatically identifies and blocks underperforming assets based on:
    - Historical win rate analysis
    - Cumulative loss tracking
    - Volatility assessment
    
    This institutional-grade risk management prevents the portfolio from taking positions in assets 
    that have demonstrated poor performance, protecting investor capital.
    """)


def render_expectancy():
    """Operation Lucidity: Segmented expectancy analysis"""
    st.markdown("## Segmented Expectancy Analysis")
    st.markdown("*Operation Lucidity - Know WHERE the system wins*")
    
    try:
        client = get_api_client()
        response = client.get_segmented_expectancy()
        
        if not response.get('success'):
            st.warning(f"Unable to load expectancy data: {response.get('error', 'Unknown error')}")
            return
        
        total_trades = response.get('total_trades', 0)
        overall_exp = response.get('overall_expectancy', 0)
        best_segment = response.get('best_segment')
        best_exp = response.get('best_expectancy')
        profitable_count = response.get('profitable_segment_count', 0)
        segments = response.get('segments', [])
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Closed Trades Analyzed", f"{total_trades:,}")
        
        with col2:
            exp_color = "normal" if overall_exp >= 0 else "inverse"
            st.metric("Overall Expectancy", f"${overall_exp:.2f}", delta_color=exp_color)
        
        with col3:
            st.metric("Profitable Segments", f"{profitable_count}", delta="Edge detected" if profitable_count > 0 else None)
        
        with col4:
            if best_segment and best_exp is not None:
                short_segment = best_segment[:20] if len(best_segment) > 20 else best_segment
                st.metric("Best Segment", short_segment, delta=f"E=${best_exp:.2f}")
            else:
                st.metric("Best Segment", "Insufficient data")
        
        st.markdown("---")
        st.markdown("### Expectancy by Segment")
        st.markdown("*E = (Win% × AvgWin) - (Loss% × |AvgLoss|)*")
        
        if segments:
            data = []
            for seg in segments:
                exp_val = seg.get('expectancy', 0)
                is_profit = exp_val > 0
                
                data.append({
                    'HMM Regime': seg.get('regime', 'UNKNOWN'),
                    'Coherence': seg.get('coherence_bucket', 'N/A'),
                    'Trades': seg.get('trade_count', 0),
                    'Win Rate': f"{seg.get('win_rate', 0):.1f}%",
                    'Avg Win': f"${seg.get('avg_win', 0):.2f}",
                    'Avg Loss': f"${seg.get('avg_loss', 0):.2f}",
                    'Expectancy': f"${exp_val:.2f}",
                    'Status': 'PROFITABLE' if is_profit else 'LOSING'
                })
            
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.markdown("### Segment Heatmap")
            
            profitable = [s for s in segments if s.get('expectancy', 0) > 0 and s.get('trade_count', 0) >= 5]
            losing = [s for s in segments if s.get('expectancy', 0) <= 0 and s.get('trade_count', 0) >= 5]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Edge Segments (E > 0)")
                if profitable:
                    for seg in sorted(profitable, key=lambda x: x.get('expectancy', 0), reverse=True):
                        regime = seg.get('regime', 'UNKNOWN')
                        coh = seg.get('coherence_bucket', 'N/A')
                        exp = seg.get('expectancy', 0)
                        trades = seg.get('trade_count', 0)
                        
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #1a472a 0%, #2d5a3d 100%); 
                                    border: 1px solid #00D4AA; border-radius: 8px; padding: 12px; margin: 8px 0;">
                            <span style="font-weight: bold; color: #00D4AA;">{regime}</span>
                            <span style="color: #888;"> + </span>
                            <span style="color: #4DABF7;">{coh}</span>
                            <br/>
                            <span style="font-size: 24px; font-weight: bold; color: #00D4AA;">E = ${exp:.2f}</span>
                            <span style="color: #888; margin-left: 10px;">({trades} trades)</span>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No profitable segments with 5+ trades yet")
            
            with col2:
                st.markdown("#### Losing Segments (E <= 0)")
                if losing:
                    for seg in sorted(losing, key=lambda x: x.get('expectancy', 0)):
                        regime = seg.get('regime', 'UNKNOWN')
                        coh = seg.get('coherence_bucket', 'N/A')
                        exp = seg.get('expectancy', 0)
                        trades = seg.get('trade_count', 0)
                        
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #4a1a1a 0%, #5a2d2d 100%); 
                                    border: 1px solid #ff6b6b; border-radius: 8px; padding: 12px; margin: 8px 0;">
                            <span style="font-weight: bold; color: #ff6b6b;">{regime}</span>
                            <span style="color: #888;"> + </span>
                            <span style="color: #888;">{coh}</span>
                            <br/>
                            <span style="font-size: 24px; font-weight: bold; color: #ff6b6b;">E = ${exp:.2f}</span>
                            <span style="color: #888; margin-left: 10px;">({trades} trades)</span>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No losing segments with 5+ trades yet")
        else:
            st.info("No segment data available. Trades with telemetry will appear here after execution.")
        
        st.markdown("---")
        st.markdown("### What This Means for Investors")
        st.markdown("""
        **Operation Lucidity** segments performance by market regime (BULLISH/BEARISH/RANGING) and 
        signal coherence (LOW/MED/HIGH) to identify WHERE the system has a statistical edge.
        
        - **Positive Expectancy (E > 0)**: The system has proven edge in these conditions
        - **Negative Expectancy (E < 0)**: These conditions should be avoided or filtered
        - **5+ trades minimum**: Required for statistical significance
        
        This analysis enables regime-aware filtering to concentrate trading in profitable conditions.
        """)
        
    except Exception as e:
        st.error(f"Error loading expectancy data: {e}")


def render_overview(metrics, quarantine=None):
    st.markdown("## Portfolio Overview")
    
    if not metrics:
        st.warning("No trade data available. Run some trades to see metrics.")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Trades", "--")
        with col2:
            st.metric("Win Rate", "--")
        with col3:
            st.metric("Total P&L", "--")
        with col4:
            st.metric("Sharpe Ratio", "--")
        return
    
    total_trades = metrics.get('total_trades', 0)
    win_rate_net = metrics.get('win_rate_net', metrics.get('win_rate', 0))
    win_rate_dir = metrics.get('win_rate_directional', 0)
    fee_eroded = metrics.get('fee_eroded_trades', 0)
    total_pnl = metrics.get('total_pnl', 0)
    sharpe_ratio = metrics.get('sharpe_ratio', 0)
    pair_metrics = metrics.get('pair_metrics', {})
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Total Trades",
            f"{total_trades:,}",
            delta=f"+{total_trades}" if total_trades > 0 else None
        )
    
    with col2:
        color = "normal" if win_rate_dir >= 40 else "inverse"
        st.metric(
            "WR Directional",
            f"{win_rate_dir:.1f}%",
            delta="Price prediction",
            delta_color=color,
            help="Percentage of trades where price moved in the predicted direction"
        )
    
    with col3:
        color = "normal" if win_rate_net >= 40 else "inverse"
        st.metric(
            "WR Net",
            f"{win_rate_net:.1f}%",
            delta=f"{fee_eroded} fee-eroded" if fee_eroded > 0 else None,
            delta_color="inverse" if fee_eroded > 0 else "off",
            help="Percentage of trades profitable after Kraken fees (~0.26%)"
        )
    
    with col4:
        pnl_color = "normal" if total_pnl >= 0 else "inverse"
        st.metric(
            "Total P&L",
            f"${total_pnl:,.2f}",
            delta_color=pnl_color
        )
    
    with col5:
        sharpe_color = "normal" if sharpe_ratio >= 1.0 else "inverse"
        st.metric(
            "Sharpe Ratio",
            f"{sharpe_ratio:.3f}",
            delta="Good" if sharpe_ratio >= 1.5 else "Needs work" if sharpe_ratio < 1.0 else "Acceptable",
            delta_color=sharpe_color
        )
    
    if quarantine:
        total_avoided = quarantine.get('total_loss_avoided', 0)
        total_blocked = quarantine.get('total_blocked', 0)
        if total_avoided > 0:
            st.markdown("---")
            st.markdown("### Capital Protection Active")
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    "Loss Avoided",
                    f"${total_avoided:,.2f}",
                    delta=f"{total_blocked} assets quarantined",
                    delta_color="normal",
                    help="Actual losses from trades on quarantined assets before they were blocked."
                )
            with col2:
                st.info("The Asset Quarantine System has blocked underperforming assets, preventing potential losses. See **Asset Quarantine** tab for details.")
    
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
