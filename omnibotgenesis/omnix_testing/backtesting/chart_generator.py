#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMNIX V6.0 ULTRA - Professional Chart Generator
Generador de gráficos premium institucionales para reportes de inversión

Features:
- Equity curve con zonas de drawdown
- Drawdown analysis detallado
- Distribución de trades (wins/losses)
- Monthly returns heatmap
- Rolling metrics (Sharpe, win rate)
- Exportación a PNG y HTML de alta calidad
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ChartGenerator:
    """
    Professional chart generator para backtesting results
    
    Genera gráficos de calidad institucional optimizados para:
    - Reportes PDF para inversionistas
    - Presentaciones ejecutivas
    - Dashboards web interactivos
    """
    
    # OMNIX Brand Colors (Premium Dark Theme)
    COLORS = {
        'primary': '#00D4FF',      # Cyan eléctrico (OMNIX signature)
        'success': '#00FF88',      # Verde neón (profits)
        'danger': '#FF3366',       # Rojo premium (losses)
        'warning': '#FFB800',      # Amarillo dorado (warnings)
        'background': '#0A0E27',   # Azul oscuro profundo
        'surface': '#1A1F3A',      # Superficie elevada
        'text': '#E0E6ED',         # Texto principal
        'text_secondary': '#8B93A7', # Texto secundario
        'grid': '#2A2F4A',         # Grid lines
        'equity_line': '#00D4FF',  # Línea equity curve
        'benchmark': '#FFB800',    # Línea benchmark
        'underwater': '#FF3366',   # Underwater equity
    }
    
    def __init__(self, output_dir: str = "omnix_testing/reports/charts"):
        """
        Initialize Chart Generator
        
        Args:
            output_dir: Directory para guardar gráficos generados
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure default template
        self.template = self._create_template()
        
        logger.info(f"📊 Chart Generator inicializado")
        logger.info(f"   📂 Output directory: {self.output_dir}")
    
    def _create_template(self) -> dict:
        """Create custom Plotly template with OMNIX branding"""
        return {
            'layout': {
                'font': {'family': 'Arial, sans-serif', 'color': self.COLORS['text']},
                'paper_bgcolor': self.COLORS['background'],
                'plot_bgcolor': self.COLORS['surface'],
                'xaxis': {
                    'gridcolor': self.COLORS['grid'],
                    'linecolor': self.COLORS['grid'],
                    'zerolinecolor': self.COLORS['grid']
                },
                'yaxis': {
                    'gridcolor': self.COLORS['grid'],
                    'linecolor': self.COLORS['grid'],
                    'zerolinecolor': self.COLORS['grid']
                },
                'title': {
                    'font': {'size': 24, 'color': self.COLORS['text']},
                    'x': 0.5,
                    'xanchor': 'center'
                },
                'legend': {
                    'bgcolor': 'rgba(26, 31, 58, 0.8)',
                    'bordercolor': self.COLORS['grid'],
                    'borderwidth': 1
                },
                'hovermode': 'x unified'
            }
        }
    
    def generate_equity_curve(
        self,
        equity_data: pd.DataFrame,
        title: str = "OMNIX V6.0 ULTRA - Equity Curve",
        benchmark_data: Optional[pd.DataFrame] = None,
        show_drawdowns: bool = True,
        save_path: Optional[str] = None
    ) -> go.Figure:
        """
        Generate professional equity curve chart
        
        Args:
            equity_data: DataFrame con columns ['timestamp', 'equity']
            title: Chart title
            benchmark_data: Optional benchmark para comparación (e.g., Buy & Hold)
            show_drawdowns: Highlight períodos de drawdown
            save_path: Path para guardar (si None, usa nombre auto)
            
        Returns:
            Plotly Figure object
        """
        logger.info("📈 Generando Equity Curve...")
        
        fig = go.Figure()
        
        # Main equity curve
        fig.add_trace(go.Scatter(
            x=equity_data['timestamp'],
            y=equity_data['equity'],
            name='OMNIX Strategy',
            line=dict(color=self.COLORS['equity_line'], width=3),
            fill='tonexty',
            fillcolor=f'rgba(0, 212, 255, 0.1)',
            hovertemplate='<b>Equity:</b> $%{y:,.2f}<br><b>Date:</b> %{x}<extra></extra>'
        ))
        
        # Benchmark (if provided)
        if benchmark_data is not None:
            fig.add_trace(go.Scatter(
                x=benchmark_data['timestamp'],
                y=benchmark_data['equity'],
                name='Buy & Hold',
                line=dict(color=self.COLORS['benchmark'], width=2, dash='dash'),
                hovertemplate='<b>Benchmark:</b> $%{y:,.2f}<extra></extra>'
            ))
        
        # Drawdown zones (if enabled)
        if show_drawdowns and 'drawdown_pct' in equity_data.columns:
            # Identificar períodos de drawdown significativo (>5%)
            in_drawdown = equity_data['drawdown_pct'] < -5
            
            # Crear zonas sombreadas para drawdowns
            drawdown_periods = []
            start_idx = None
            
            for idx, is_dd in enumerate(in_drawdown):
                if is_dd and start_idx is None:
                    start_idx = idx
                elif not is_dd and start_idx is not None:
                    drawdown_periods.append((start_idx, idx - 1))
                    start_idx = None
            
            # Agregar última zona si termina en drawdown
            if start_idx is not None:
                drawdown_periods.append((start_idx, len(equity_data) - 1))
            
            # Dibujar zonas de drawdown
            for start, end in drawdown_periods:
                fig.add_vrect(
                    x0=equity_data['timestamp'].iloc[start],
                    x1=equity_data['timestamp'].iloc[end],
                    fillcolor=self.COLORS['danger'],
                    opacity=0.1,
                    layer='below',
                    line_width=0,
                )
        
        # Layout configuration
        fig.update_layout(
            template=self.template,
            title=title,
            xaxis_title='Date',
            yaxis_title='Portfolio Value ($)',
            hovermode='x unified',
            height=600,
            showlegend=True,
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1
            )
        )
        
        # Format Y axis as currency
        fig.update_yaxes(tickformat='$,.0f')
        
        # Save if path provided
        if save_path is None:
            save_path = self.output_dir / "equity_curve.png"
        else:
            save_path = Path(save_path)
        
        fig.write_image(str(save_path), width=1920, height=1080, scale=2)
        fig.write_html(str(save_path).replace('.png', '.html'))
        
        logger.info(f"   ✅ Equity curve guardada: {save_path}")
        
        return fig
    
    def generate_drawdown_chart(
        self,
        equity_data: pd.DataFrame,
        title: str = "Drawdown Analysis",
        save_path: Optional[str] = None
    ) -> go.Figure:
        """
        Generate underwater equity chart (drawdown visualization)
        
        Args:
            equity_data: DataFrame con columns ['timestamp', 'drawdown_pct']
            title: Chart title
            save_path: Save path
            
        Returns:
            Plotly Figure
        """
        logger.info("📉 Generando Drawdown Chart...")
        
        fig = go.Figure()
        
        # Drawdown area chart
        fig.add_trace(go.Scatter(
            x=equity_data['timestamp'],
            y=equity_data['drawdown_pct'],
            name='Drawdown',
            fill='tozeroy',
            fillcolor=f'rgba(255, 51, 102, 0.3)',
            line=dict(color=self.COLORS['underwater'], width=2),
            hovertemplate='<b>Drawdown:</b> %{y:.2f}%<br><b>Date:</b> %{x}<extra></extra>'
        ))
        
        # Zero line
        fig.add_hline(
            y=0,
            line_dash='dash',
            line_color=self.COLORS['text_secondary'],
            opacity=0.5
        )
        
        # Layout
        fig.update_layout(
            template=self.template,
            title=title,
            xaxis_title='Date',
            yaxis_title='Drawdown (%)',
            height=400,
            showlegend=False
        )
        
        # Format Y axis as percentage
        fig.update_yaxes(tickformat='.1f', ticksuffix='%')
        
        # Save
        if save_path is None:
            save_path = self.output_dir / "drawdown_chart.png"
        else:
            save_path = Path(save_path)
        
        fig.write_image(str(save_path), width=1920, height=720, scale=2)
        fig.write_html(str(save_path).replace('.png', '.html'))
        
        logger.info(f"   ✅ Drawdown chart guardado: {save_path}")
        
        return fig
    
    def generate_trade_distribution(
        self,
        trades: pd.DataFrame,
        title: str = "Trade Distribution Analysis",
        save_path: Optional[str] = None
    ) -> go.Figure:
        """
        Generate win/loss distribution chart
        
        Args:
            trades: DataFrame con column 'pnl'
            title: Chart title
            save_path: Save path
            
        Returns:
            Plotly Figure
        """
        logger.info("📊 Generando Trade Distribution...")
        
        # Separate wins and losses
        wins = trades[trades['pnl'] > 0]['pnl']
        losses = trades[trades['pnl'] <= 0]['pnl']
        
        # Create subplots
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Winning Trades', 'Losing Trades'),
            specs=[[{'type': 'histogram'}, {'type': 'histogram'}]]
        )
        
        # Wins histogram
        fig.add_trace(
            go.Histogram(
                x=wins,
                name='Wins',
                marker_color=self.COLORS['success'],
                opacity=0.7,
                nbinsx=30,
                hovertemplate='<b>Profit:</b> $%{x:.2f}<br><b>Count:</b> %{y}<extra></extra>'
            ),
            row=1, col=1
        )
        
        # Losses histogram
        fig.add_trace(
            go.Histogram(
                x=losses,
                name='Losses',
                marker_color=self.COLORS['danger'],
                opacity=0.7,
                nbinsx=30,
                hovertemplate='<b>Loss:</b> $%{x:.2f}<br><b>Count:</b> %{y}<extra></extra>'
            ),
            row=1, col=2
        )
        
        # Layout
        fig.update_layout(
            template=self.template,
            title_text=title,
            height=500,
            showlegend=False
        )
        
        fig.update_xaxes(title_text="Profit ($)", row=1, col=1, tickformat='$,.0f')
        fig.update_xaxes(title_text="Loss ($)", row=1, col=2, tickformat='$,.0f')
        fig.update_yaxes(title_text="Number of Trades", row=1, col=1)
        fig.update_yaxes(title_text="Number of Trades", row=1, col=2)
        
        # Save
        if save_path is None:
            save_path = self.output_dir / "trade_distribution.png"
        else:
            save_path = Path(save_path)
        
        fig.write_image(str(save_path), width=1920, height=900, scale=2)
        fig.write_html(str(save_path).replace('.png', '.html'))
        
        logger.info(f"   ✅ Trade distribution guardado: {save_path}")
        
        return fig
    
    def generate_monthly_returns_heatmap(
        self,
        equity_data: pd.DataFrame,
        title: str = "Monthly Returns Heatmap",
        save_path: Optional[str] = None
    ) -> go.Figure:
        """
        Generate monthly returns heatmap
        
        Args:
            equity_data: DataFrame con columns ['timestamp', 'equity']
            title: Chart title
            save_path: Save path
            
        Returns:
            Plotly Figure
        """
        logger.info("🗓️ Generando Monthly Returns Heatmap...")
        
        # Calculate monthly returns
        df = equity_data.copy()
        df['year'] = df['timestamp'].dt.year
        df['month'] = df['timestamp'].dt.month
        
        # Group by month and calculate return
        monthly_equity = df.groupby(['year', 'month'])['equity'].last().reset_index()
        monthly_equity['return_pct'] = monthly_equity['equity'].pct_change() * 100
        
        # Pivot para heatmap
        pivot_table = monthly_equity.pivot(index='year', columns='month', values='return_pct')
        
        # Month names
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=pivot_table.values,
            x=month_names,
            y=pivot_table.index,
            colorscale=[
                [0, self.COLORS['danger']],
                [0.5, self.COLORS['text_secondary']],
                [1, self.COLORS['success']]
            ],
            zmid=0,
            text=pivot_table.values,
            texttemplate='%{text:.1f}%',
            textfont={'size': 12},
            hovertemplate='<b>%{y} %{x}</b><br>Return: %{z:.2f}%<extra></extra>',
            colorbar=dict(
                title='Return (%)',
                ticksuffix='%'
            )
        ))
        
        # Layout
        fig.update_layout(
            template=self.template,
            title=title,
            xaxis_title='Month',
            yaxis_title='Year',
            height=400
        )
        
        # Save
        if save_path is None:
            save_path = self.output_dir / "monthly_returns.png"
        else:
            save_path = Path(save_path)
        
        fig.write_image(str(save_path), width=1920, height=720, scale=2)
        fig.write_html(str(save_path).replace('.png', '.html'))
        
        logger.info(f"   ✅ Monthly returns heatmap guardado: {save_path}")
        
        return fig
    
    def generate_rolling_sharpe(
        self,
        equity_data: pd.DataFrame,
        window: int = 30,
        title: str = "Rolling Sharpe Ratio (30-day)",
        save_path: Optional[str] = None
    ) -> go.Figure:
        """
        Generate rolling Sharpe ratio chart
        
        Args:
            equity_data: DataFrame con columns ['timestamp', 'equity']
            window: Rolling window size (days)
            title: Chart title
            save_path: Save path
            
        Returns:
            Plotly Figure
        """
        logger.info("📈 Generando Rolling Sharpe Ratio...")
        
        # Calculate returns
        df = equity_data.copy()
        df['returns'] = df['equity'].pct_change()
        
        # Calculate rolling Sharpe (assuming 252 trading days/year)
        rolling_mean = df['returns'].rolling(window=window).mean()
        rolling_std = df['returns'].rolling(window=window).std()
        df['rolling_sharpe'] = (rolling_mean / rolling_std) * np.sqrt(252)
        
        # Create chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['rolling_sharpe'],
            name=f'{window}-day Sharpe',
            line=dict(color=self.COLORS['primary'], width=2),
            fill='tozeroy',
            fillcolor=f'rgba(0, 212, 255, 0.1)',
            hovertemplate='<b>Sharpe:</b> %{y:.2f}<br><b>Date:</b> %{x}<extra></extra>'
        ))
        
        # Reference lines
        fig.add_hline(y=1.0, line_dash='dash', line_color=self.COLORS['text_secondary'], 
                     opacity=0.5, annotation_text='Good (1.0)')
        fig.add_hline(y=2.0, line_dash='dash', line_color=self.COLORS['success'], 
                     opacity=0.5, annotation_text='Excellent (2.0)')
        
        # Layout
        fig.update_layout(
            template=self.template,
            title=title,
            xaxis_title='Date',
            yaxis_title='Sharpe Ratio',
            height=400,
            showlegend=False
        )
        
        # Save
        if save_path is None:
            save_path = self.output_dir / "rolling_sharpe.png"
        else:
            save_path = Path(save_path)
        
        fig.write_image(str(save_path), width=1920, height=720, scale=2)
        fig.write_html(str(save_path).replace('.png', '.html'))
        
        logger.info(f"   ✅ Rolling Sharpe guardado: {save_path}")
        
        return fig
    
    def generate_full_report_charts(
        self,
        equity_data: pd.DataFrame,
        trades: pd.DataFrame,
        benchmark_data: Optional[pd.DataFrame] = None
    ) -> Dict[str, go.Figure]:
        """
        Generate complete set of charts para reporte profesional
        
        Args:
            equity_data: DataFrame con equity curve data
            trades: DataFrame con trade history
            benchmark_data: Optional benchmark data
            
        Returns:
            Dictionary con todos los charts generados
        """
        logger.info("=" * 70)
        logger.info("🎨 GENERANDO SUITE COMPLETA DE GRÁFICOS PREMIUM")
        logger.info("=" * 70)
        
        charts = {}
        
        # 1. Equity Curve
        charts['equity_curve'] = self.generate_equity_curve(
            equity_data, 
            benchmark_data=benchmark_data,
            show_drawdowns=True
        )
        
        # 2. Drawdown Chart
        charts['drawdown'] = self.generate_drawdown_chart(equity_data)
        
        # 3. Trade Distribution
        charts['trade_distribution'] = self.generate_trade_distribution(trades)
        
        # 4. Monthly Returns Heatmap
        charts['monthly_returns'] = self.generate_monthly_returns_heatmap(equity_data)
        
        # 5. Rolling Sharpe
        charts['rolling_sharpe'] = self.generate_rolling_sharpe(equity_data)
        
        logger.info("=" * 70)
        logger.info(f"✅ {len(charts)} gráficos premium generados exitosamente")
        logger.info(f"📂 Guardados en: {self.output_dir}")
        logger.info("=" * 70)
        
        return charts


if __name__ == "__main__":
    # Demo de capacidades del Chart Generator
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    print("\n" + "=" * 70)
    print("📊 OMNIX V6.0 ULTRA - Chart Generator Demo")
    print("=" * 70)
    
    # Create dummy data para demo
    dates = pd.date_range(start='2024-01-01', end='2024-12-01', freq='D')
    np.random.seed(42)
    
    # Simulate equity curve
    returns = np.random.normal(0.001, 0.02, len(dates))
    equity = 10000 * (1 + returns).cumprod()
    
    equity_df = pd.DataFrame({
        'timestamp': dates,
        'equity': equity
    })
    
    # Calculate drawdown
    running_max = equity_df['equity'].cummax()
    equity_df['drawdown_pct'] = ((equity_df['equity'] - running_max) / running_max) * 100
    
    # Simulate trades
    num_trades = 100
    trades_df = pd.DataFrame({
        'pnl': np.random.normal(50, 200, num_trades)
    })
    
    # Generate charts
    generator = ChartGenerator()
    charts = generator.generate_full_report_charts(equity_df, trades_df)
    
    print(f"\n✅ Demo completado: {len(charts)} gráficos generados")
    print("=" * 70)
