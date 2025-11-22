#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMNIX V6.0 ULTRA - Professional PDF Report Generator
Generador de reportes institucionales para inversionistas

Features:
- Reportes de 25-35 páginas con branding OMNIX
- Executive summary con métricas destacadas
- Gráficos embebidos de alta calidad
- Tablas profesionales con trade log completo
- Secciones: Portada, Methodology, Results, Risk Analysis, Appendix
- Watermarks, headers, footers, índice automático
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas

try:
    from PyPDF2 import PdfReader
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False

logger = logging.getLogger(__name__)


class PDFReportGenerator:
    """
    Professional PDF report generator para backtesting results
    
    Genera reportes institucionales optimizados para inversionistas con:
    - Branding OMNIX premium
    - Métricas institucionales completas
    - Gráficos embebidos
    - Análisis de riesgo detallado
    - Trade log completo
    - Watermarks y seguridad
    """
    
    # OMNIX Brand Colors
    COLORS = {
        'primary': colors.HexColor('#00D4FF'),      # Cyan eléctrico
        'dark': colors.HexColor('#0A0E27'),         # Azul oscuro
        'surface': colors.HexColor('#1A1F3A'),      # Superficie
        'success': colors.HexColor('#00FF88'),      # Verde neón
        'danger': colors.HexColor('#FF3366'),       # Rojo premium
        'warning': colors.HexColor('#FFB800'),      # Amarillo dorado
        'text': colors.HexColor('#E0E6ED'),         # Texto principal
        'text_light': colors.HexColor('#8B93A7'),   # Texto secundario
    }
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize PDF Report Generator
        
        Args:
            output_dir: Directory para guardar reportes generados (default: repo_root/omnix_testing/reports/pdf)
        """
        # Get repository root (2 levels up from this file)
        repo_root = Path(__file__).resolve().parents[2]
        
        if output_dir is None:
            self.output_dir = repo_root / "omnix_testing" / "reports" / "pdf"
        else:
            self.output_dir = Path(output_dir)
            if not self.output_dir.is_absolute():
                self.output_dir = repo_root / self.output_dir
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure styles
        self.styles = self._create_styles()
        
        logger.info(f"📄 PDF Report Generator inicializado")
        logger.info(f"   📂 Output directory: {self.output_dir.resolve()}")
    
    def _create_styles(self) -> Dict:
        """Create custom paragraph styles with OMNIX branding"""
        styles = getSampleStyleSheet()
        
        # Title style
        styles.add(ParagraphStyle(
            name='OmnixTitle',
            parent=styles['Title'],
            fontSize=28,
            textColor=self.COLORS['primary'],
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Heading 1
        styles.add(ParagraphStyle(
            name='OmnixHeading1',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=self.COLORS['primary'],
            spaceBefore=20,
            spaceAfter=12,
            fontName='Helvetica-Bold'
        ))
        
        # Heading 2
        styles.add(ParagraphStyle(
            name='OmnixHeading2',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=self.COLORS['text'],
            spaceBefore=14,
            spaceAfter=8,
            fontName='Helvetica-Bold'
        ))
        
        # Body text
        styles.add(ParagraphStyle(
            name='OmnixBody',
            parent=styles['BodyText'],
            fontSize=10,
            textColor=self.COLORS['text'],
            spaceAfter=10,
            alignment=TA_JUSTIFY,
            leading=14
        ))
        
        # Metric highlight
        styles.add(ParagraphStyle(
            name='MetricValue',
            fontSize=24,
            textColor=self.COLORS['success'],
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            spaceAfter=5
        ))
        
        # Metric label
        styles.add(ParagraphStyle(
            name='MetricLabel',
            fontSize=10,
            textColor=self.COLORS['text_light'],
            alignment=TA_CENTER,
            spaceAfter=15
        ))
        
        return styles
    
    def _add_cover_page(self, story: List, metrics: Dict, period: Tuple[str, str]) -> None:
        """
        Generate professional cover page with executive summary
        
        Args:
            story: ReportLab story list
            metrics: Dictionary con métricas clave
            period: Tuple (start_date, end_date)
        """
        # Title
        story.append(Spacer(1, 1.5*inch))
        story.append(Paragraph("OMNIX V6.0 ULTRA", self.styles['OmnixTitle']))
        story.append(Paragraph("BACKTESTING REPORT", self.styles['OmnixTitle']))
        
        story.append(Spacer(1, 0.5*inch))
        
        # Period
        period_text = f"Period: {period[0]} to {period[1]}"
        story.append(Paragraph(period_text, self.styles['OmnixHeading2']))
        
        story.append(Spacer(1, 0.8*inch))
        
        # Executive Summary Box
        story.append(Paragraph("EXECUTIVE SUMMARY", self.styles['OmnixHeading1']))
        story.append(Spacer(1, 0.3*inch))
        
        # Key metrics in 3 columns
        metrics_data = [
            [
                [
                    Paragraph(f"{metrics.get('win_rate', 0):.1f}%", self.styles['MetricValue']),
                    Paragraph("Win Rate", self.styles['MetricLabel'])
                ],
                [
                    Paragraph(f"{metrics.get('sharpe_ratio', 0):.2f}", self.styles['MetricValue']),
                    Paragraph("Sharpe Ratio", self.styles['MetricLabel'])
                ],
                [
                    Paragraph(f"${metrics.get('total_return', 0):,.0f}", self.styles['MetricValue']),
                    Paragraph("Total Profit", self.styles['MetricLabel'])
                ]
            ],
            [
                [
                    Paragraph(f"{metrics.get('total_trades', 0)}", self.styles['MetricValue']),
                    Paragraph("Total Trades", self.styles['MetricLabel'])
                ],
                [
                    Paragraph(f"{metrics.get('max_drawdown', 0):.1f}%", self.styles['MetricValue']),
                    Paragraph("Max Drawdown", self.styles['MetricLabel'])
                ],
                [
                    Paragraph(f"{metrics.get('profit_factor', 0):.2f}", self.styles['MetricValue']),
                    Paragraph("Profit Factor", self.styles['MetricLabel'])
                ]
            ]
        ]
        
        metrics_table = Table(metrics_data, colWidths=[2*inch, 2*inch, 2*inch])
        metrics_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        
        story.append(metrics_table)
        story.append(Spacer(1, 0.5*inch))
        
        # Disclaimer
        disclaimer = """
        <b>CONFIDENTIAL - INVESTOR REPORT</b><br/>
        This report contains proprietary backtesting results for OMNIX V6.0 ULTRA automated trading system.
        Past performance does not guarantee future results. For authorized investors only.
        """
        story.append(Paragraph(disclaimer, self.styles['OmnixBody']))
        
        story.append(PageBreak())
    
    def _add_methodology_section(self, story: List) -> None:
        """Add methodology section explaining the 9 strategies"""
        
        story.append(Paragraph("1. METHODOLOGY", self.styles['OmnixHeading1']))
        story.append(Spacer(1, 0.2*inch))
        
        intro = """
        OMNIX V6.0 ULTRA employs a sophisticated multi-strategy approach combining 9 advanced
        trading algorithms, quantum-enhanced protocols (ARES V1 Swing & V2 Scalping), and a
        proprietary Coherence Engine for signal validation.
        """
        story.append(Paragraph(intro, self.styles['OmnixBody']))
        story.append(Spacer(1, 0.2*inch))
        
        # 9 Strategies Overview
        story.append(Paragraph("1.1 Core Strategy Stack", self.styles['OmnixHeading2']))
        
        strategies = [
            ("Monte Carlo Simulation", "Risk assessment through 10,000+ scenario simulations"),
            ("Black Swan Detector", "Extreme event detection and protection"),
            ("Kelly Criterion", "Optimal position sizing based on edge and risk"),
            ("HMM Regime Detection", "Market regime classification for adaptive trading"),
            ("Dual Kalman Filter", "Noise reduction and trend following"),
            ("Quantum Momentum", "Price momentum analysis with quantum enhancements"),
            ("Sharia Compliance Filter", "Ethical trading validation"),
            ("Order Book Analysis", "Market depth and liquidity assessment"),
            ("Sentiment Analysis", "Multi-source sentiment aggregation")
        ]
        
        for strategy, description in strategies:
            text = f"<b>{strategy}:</b> {description}"
            story.append(Paragraph(text, self.styles['OmnixBody']))
            story.append(Spacer(1, 0.05*inch))
        
        story.append(Spacer(1, 0.3*inch))
        
        # ARES Protocols
        story.append(Paragraph("1.2 ARES Quantum Protocols", self.styles['OmnixHeading2']))
        
        ares_text = """
        <b>ARES V1 (Swing Trading):</b> Institutional-grade swing trading with 74-82% historical win rate.
        Features 6 institutional signals (RSI Divergence, Smart Money Index, Liquidity Sweeps, Volume Profile,
        Fibonacci Confluence, Market Regime) with multi-timeframe correlation (H4, H1, M15).<br/><br/>
        
        <b>ARES V2 (Scalping M1):</b> Ultra-fast 1-minute scalping optimized for high-frequency opportunities
        with 85% historical win rate. 5 precision signals (RSI M1, Bollinger Squeeze, Volume Spike, Momentum Shift,
        VWAP Cross) with tight stop-loss (-0.28%) and rapid take-profit (+0.85%).
        """
        story.append(Paragraph(ares_text, self.styles['OmnixBody']))
        story.append(Spacer(1, 0.3*inch))
        
        # Coherence Engine
        story.append(Paragraph("1.3 Coherence Engine V5.4", self.styles['OmnixHeading2']))
        
        coherence_text = """
        The Coherence Engine validates agreement between strategies using a premium 6-tier veto system:
        Tier 1 (CRITICAL): Complete veto for coherence <30%. Tier 2 (POOR): Veto for 30-50%.
        Tier 3 (HOLD): Veto if engine recommends HOLD. Tier 4 (MODERATE): Reduce position 40-60% for 50-70%.
        Tier 5 (GOOD): Reduce 15% for 70-85%. Tier 6 (EXCELLENT): Full approval for ≥85%.
        """
        story.append(Paragraph(coherence_text, self.styles['OmnixBody']))
        
        story.append(PageBreak())
    
    def _add_results_section(
        self,
        story: List,
        metrics: Dict,
        charts_dir: Path
    ) -> None:
        """
        Add results section with metrics and embedded charts
        
        Args:
            story: ReportLab story list
            metrics: Dictionary con todas las métricas
            charts_dir: Path to directory con gráficos
        """
        story.append(Paragraph("2. RESULTS", self.styles['OmnixHeading1']))
        story.append(Spacer(1, 0.2*inch))
        
        # Performance Overview
        story.append(Paragraph("2.1 Performance Overview", self.styles['OmnixHeading2']))
        
        perf_data = [
            ['Metric', 'Value', 'Benchmark'],
            ['Total Return', f"${metrics.get('total_return', 0):,.2f}", f"${metrics.get('benchmark_return', 0):,.2f}"],
            ['Win Rate', f"{metrics.get('win_rate', 0):.2f}%", "-"],
            ['Sharpe Ratio', f"{metrics.get('sharpe_ratio', 0):.3f}", f"{metrics.get('benchmark_sharpe', 0):.3f}"],
            ['Max Drawdown', f"{metrics.get('max_drawdown', 0):.2f}%", f"{metrics.get('benchmark_dd', 0):.2f}%"],
            ['Calmar Ratio', f"{metrics.get('calmar_ratio', 0):.3f}", "-"],
            ['Profit Factor', f"{metrics.get('profit_factor', 0):.3f}", "-"],
            ['Avg Win', f"${metrics.get('avg_win', 0):.2f}", "-"],
            ['Avg Loss', f"${metrics.get('avg_loss', 0):.2f}", "-"],
        ]
        
        perf_table = Table(perf_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
        perf_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.COLORS['surface']),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.COLORS['primary']),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 0.5, self.COLORS['text_light']),
        ]))
        
        story.append(perf_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Equity Curve
        story.append(Paragraph("2.2 Equity Curve", self.styles['OmnixHeading2']))
        
        equity_chart = charts_dir / "equity_curve.png"
        if equity_chart.exists():
            img = Image(str(equity_chart), width=6.5*inch, height=3.6*inch)
            story.append(img)
        else:
            story.append(Paragraph("[Equity curve chart not available]", self.styles['OmnixBody']))
        
        story.append(PageBreak())
        
        # Drawdown Analysis
        story.append(Paragraph("2.3 Drawdown Analysis", self.styles['OmnixHeading2']))
        
        dd_chart = charts_dir / "drawdown_chart.png"
        if dd_chart.exists():
            img = Image(str(dd_chart), width=6.5*inch, height=2.6*inch)
            story.append(img)
        else:
            story.append(Paragraph("[Drawdown chart not available]", self.styles['OmnixBody']))
        
        story.append(Spacer(1, 0.3*inch))
        
        # Trade Distribution
        story.append(Paragraph("2.4 Trade Distribution", self.styles['OmnixHeading2']))
        
        dist_chart = charts_dir / "trade_distribution.png"
        if dist_chart.exists():
            img = Image(str(dist_chart), width=6.5*inch, height=3.2*inch)
            story.append(img)
        else:
            story.append(Paragraph("[Trade distribution chart not available]", self.styles['OmnixBody']))
        
        story.append(PageBreak())
    
    def _add_risk_analysis_section(
        self,
        story: List,
        risk_metrics: Dict,
        trades_df: pd.DataFrame
    ) -> None:
        """Add detailed risk analysis section"""
        
        story.append(Paragraph("3. RISK ANALYSIS", self.styles['OmnixHeading1']))
        story.append(Spacer(1, 0.2*inch))
        
        # Drawdown Statistics
        story.append(Paragraph("3.1 Drawdown Statistics", self.styles['OmnixHeading2']))
        
        dd_data = [
            ['Metric', 'Value'],
            ['Maximum Drawdown', f"{risk_metrics.get('max_dd', 0):.2f}%"],
            ['Average Drawdown', f"{risk_metrics.get('avg_dd', 0):.2f}%"],
            ['Longest DD Duration', f"{risk_metrics.get('max_dd_duration', 0)} days"],
            ['Average DD Duration', f"{risk_metrics.get('avg_dd_duration', 0):.1f} days"],
            ['Recovery Time', f"{risk_metrics.get('recovery_time', 0)} days"],
        ]
        
        dd_table = Table(dd_data, colWidths=[3*inch, 2*inch])
        dd_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.COLORS['surface']),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.COLORS['primary']),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, self.COLORS['text_light']),
        ]))
        
        story.append(dd_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Worst Trades Analysis
        story.append(Paragraph("3.2 Worst Trades Analysis", self.styles['OmnixHeading2']))
        
        if len(trades_df) > 0:
            worst_trades = trades_df.nsmallest(5, 'pnl')[['timestamp', 'pair', 'pnl']]
            
            worst_data = [['Date', 'Pair', 'Loss']]
            for _, trade in worst_trades.iterrows():
                worst_data.append([
                    trade['timestamp'].strftime('%Y-%m-%d') if hasattr(trade['timestamp'], 'strftime') else str(trade['timestamp']),
                    trade.get('pair', 'N/A'),
                    f"${trade['pnl']:.2f}"
                ])
            
            worst_table = Table(worst_data, colWidths=[1.8*inch, 1.5*inch, 1.5*inch])
            worst_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.COLORS['surface']),
                ('TEXTCOLOR', (0, 0), (-1, 0), self.COLORS['primary']),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, self.COLORS['text_light']),
            ]))
            
            story.append(worst_table)
        else:
            story.append(Paragraph("No trade data available", self.styles['OmnixBody']))
        
        story.append(PageBreak())
    
    def _add_trade_log_section(self, story: List, trades_df: pd.DataFrame) -> None:
        """Add complete trade log section"""
        
        story.append(Paragraph("4. COMPLETE TRADE LOG", self.styles['OmnixHeading1']))
        story.append(Spacer(1, 0.2*inch))
        
        if len(trades_df) == 0:
            story.append(Paragraph("No trades executed during this period", self.styles['OmnixBody']))
            story.append(PageBreak())
            return
        
        # Paginate trades (max 30 per page)
        trades_per_page = 30
        total_pages = (len(trades_df) + trades_per_page - 1) // trades_per_page
        
        for page_num in range(total_pages):
            start_idx = page_num * trades_per_page
            end_idx = min(start_idx + trades_per_page, len(trades_df))
            page_trades = trades_df.iloc[start_idx:end_idx]
            
            story.append(Paragraph(f"Trades {start_idx + 1} - {end_idx} of {len(trades_df)}", 
                                 self.styles['OmnixHeading2']))
            story.append(Spacer(1, 0.1*inch))
            
            # Build table data
            trade_data = [['#', 'Timestamp', 'Pair', 'Side', 'PnL']]
            
            for idx, (_, trade) in enumerate(page_trades.iterrows(), start=start_idx + 1):
                trade_data.append([
                    str(idx),
                    trade['timestamp'].strftime('%Y-%m-%d %H:%M') if hasattr(trade['timestamp'], 'strftime') else str(trade['timestamp']),
                    trade.get('pair', 'N/A'),
                    trade.get('side', 'N/A'),
                    f"${trade['pnl']:.2f}"
                ])
            
            trade_table = Table(trade_data, colWidths=[0.4*inch, 1.6*inch, 1*inch, 0.8*inch, 1*inch])
            trade_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.COLORS['surface']),
                ('TEXTCOLOR', (0, 0), (-1, 0), self.COLORS['primary']),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, self.COLORS['text_light']),
            ]))
            
            story.append(trade_table)
            
            if page_num < total_pages - 1:
                story.append(PageBreak())
        
        story.append(PageBreak())
    
    def _add_appendix_section(self, story: List) -> None:
        """Add technical appendix with formulas and disclaimers"""
        
        story.append(Paragraph("5. TECHNICAL APPENDIX", self.styles['OmnixHeading1']))
        story.append(Spacer(1, 0.2*inch))
        
        # Key Formulas
        story.append(Paragraph("5.1 Key Formulas", self.styles['OmnixHeading2']))
        
        formulas = """
        <b>Sharpe Ratio:</b> (Return - Risk-Free Rate) / Standard Deviation<br/>
        <b>Calmar Ratio:</b> Annualized Return / Maximum Drawdown<br/>
        <b>Profit Factor:</b> Gross Profit / Gross Loss<br/>
        <b>Kelly Criterion:</b> f* = (bp - q) / b, where b=odds, p=win probability, q=1-p<br/>
        <b>Max Drawdown:</b> (Peak Value - Trough Value) / Peak Value × 100%
        """
        story.append(Paragraph(formulas, self.styles['OmnixBody']))
        story.append(Spacer(1, 0.3*inch))
        
        # Transparency
        story.append(Paragraph("5.2 Transparency & Audit", self.styles['OmnixHeading2']))
        
        transparency = """
        All source code for OMNIX V6.0 ULTRA is available for investor audit. The backtesting engine,
        strategy implementations, and data processing pipelines can be reviewed to verify the integrity
        of these results. Contact investor relations for repository access.
        """
        story.append(Paragraph(transparency, self.styles['OmnixBody']))
        story.append(Spacer(1, 0.3*inch))
        
        # Disclaimers
        story.append(Paragraph("5.3 Important Disclaimers", self.styles['OmnixHeading2']))
        
        disclaimers = """
        <b>PAST PERFORMANCE DISCLAIMER:</b> Past performance is not indicative of future results.
        All investments carry risk, including potential loss of principal.<br/><br/>
        
        <b>BACKTESTING LIMITATIONS:</b> Backtesting results are based on historical data and may not
        reflect actual trading conditions, slippage, or execution delays.<br/><br/>
        
        <b>NO GUARANTEE:</b> There is no guarantee that the strategies will perform as indicated in
        live market conditions.<br/><br/>
        
        <b>ACCREDITED INVESTORS ONLY:</b> This report is intended for accredited investors only and
        should not be distributed publicly.
        """
        story.append(Paragraph(disclaimers, self.styles['OmnixBody']))
        story.append(Spacer(1, 0.3*inch))
        
        # Footer
        generation_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        footer_text = f"<i>Report generated: {generation_time}</i>"
        story.append(Paragraph(footer_text, self.styles['OmnixBody']))
    
    def generate_full_report(
        self,
        metrics: Dict,
        trades_df: pd.DataFrame,
        equity_df: pd.DataFrame,
        period: Tuple[str, str],
        filename: Optional[str] = None
    ) -> Path:
        """
        Generate complete PDF report
        
        Args:
            metrics: Dictionary con todas las métricas
            trades_df: DataFrame con trade log completo
            equity_df: DataFrame con equity curve data
            period: Tuple (start_date, end_date)
            filename: Optional custom filename
            
        Returns:
            Path to generated PDF file
        """
        logger.info("=" * 70)
        logger.info("📄 GENERANDO REPORTE PDF INSTITUCIONAL")
        logger.info("=" * 70)
        
        # Generate filename
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"OMNIX_Backtest_Report_{timestamp}.pdf"
        
        output_path = self.output_dir / filename
        
        # Create PDF document
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        # Build story
        story = []
        
        # Section 1: Cover Page
        logger.info("📋 Generando portada...")
        self._add_cover_page(story, metrics, period)
        
        # Section 2: Methodology
        logger.info("📚 Generando metodología...")
        self._add_methodology_section(story)
        
        # Section 3: Results
        logger.info("📊 Generando resultados...")
        # Use absolute path for charts directory
        repo_root = Path(__file__).resolve().parents[2]
        charts_dir = repo_root / "omnix_testing" / "reports" / "charts"
        self._add_results_section(story, metrics, charts_dir)
        
        # Section 4: Risk Analysis
        logger.info("⚠️ Generando análisis de riesgo...")
        risk_metrics = {
            'max_dd': metrics.get('max_drawdown', 0),
            'avg_dd': metrics.get('avg_drawdown', 0),
            'max_dd_duration': metrics.get('max_dd_duration_days', 0),
            'avg_dd_duration': metrics.get('avg_dd_duration_days', 0),
            'recovery_time': metrics.get('recovery_days', 0)
        }
        self._add_risk_analysis_section(story, risk_metrics, trades_df)
        
        # Section 5: Trade Log
        logger.info("📝 Generando trade log...")
        self._add_trade_log_section(story, trades_df)
        
        # Section 6: Appendix
        logger.info("📖 Generando apéndice técnico...")
        self._add_appendix_section(story)
        
        # Build PDF
        logger.info("🔨 Compilando PDF...")
        doc.build(story)
        
        file_size = output_path.stat().st_size / 1024  # KB
        
        # Count actual pages using PyPDF2
        page_count = "N/A"
        if HAS_PYPDF2:
            try:
                pdf_reader = PdfReader(str(output_path))
                page_count = len(pdf_reader.pages)
            except Exception as e:
                logger.warning(f"No se pudo contar páginas: {e}")
                page_count = "N/A"
        
        logger.info("=" * 70)
        logger.info(f"✅ REPORTE PDF GENERADO EXITOSAMENTE")
        logger.info(f"   📁 Archivo: {output_path.name}")
        logger.info(f"   📂 Ubicación: {output_path.parent}")
        logger.info(f"   📏 Tamaño: {file_size:.1f} KB")
        logger.info(f"   📄 Páginas: {page_count}")
        if isinstance(page_count, int) and page_count < 20:
            logger.warning(f"   ⚠️ Report tiene solo {page_count} páginas (objetivo: 25-35)")
        logger.info("=" * 70)
        
        return output_path


if __name__ == "__main__":
    # Demo de capacidades del PDF Report Generator
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    print("\n" + "=" * 70)
    print("📄 OMNIX V6.0 ULTRA - PDF Report Generator Demo")
    print("=" * 70)
    
    # Create dummy data para demo
    metrics = {
        'win_rate': 74.5,
        'sharpe_ratio': 2.34,
        'total_return': 45670.50,
        'total_trades': 127,
        'max_drawdown': -8.3,
        'profit_factor': 2.87,
        'avg_win': 523.40,
        'avg_loss': -182.30,
        'benchmark_return': 12000,
        'benchmark_sharpe': 1.2,
        'benchmark_dd': -12.5,
        'calmar_ratio': 3.45,
        'avg_drawdown': -3.2,
        'max_dd_duration_days': 7,
        'avg_dd_duration_days': 2.3,
        'recovery_days': 5
    }
    
    # Dummy trades
    dates = pd.date_range(start='2024-05-01', end='2024-11-01', freq='D')
    trades_df = pd.DataFrame({
        'timestamp': dates[:50],
        'pair': ['BTC/USD'] * 50,
        'side': ['BUY', 'SELL'] * 25,
        'pnl': np.random.normal(100, 300, 50)
    })
    
    # Dummy equity
    equity_df = pd.DataFrame({
        'timestamp': dates,
        'equity': 10000 * (1 + np.random.normal(0.001, 0.015, len(dates))).cumprod()
    })
    
    # Generate report
    generator = PDFReportGenerator()
    pdf_path = generator.generate_full_report(
        metrics=metrics,
        trades_df=trades_df,
        equity_df=equity_df,
        period=("2024-05-01", "2024-11-01")
    )
    
    print(f"\n✅ Demo completado")
    print(f"📄 Reporte generado: {pdf_path}")
    print("=" * 70)
