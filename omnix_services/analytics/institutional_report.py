"""
OMNIX V6.5.4 INSTITUTIONAL+ PREMIUM
Institutional Report Generator - PDF for Investors

Genera informes PDF profesionales para presentaciones a inversores.
Incluye métricas Sharpe/Sortino/Calmar, análisis por par, y gráficos.
"""

import io
import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

logger = logging.getLogger(__name__)

OMNIX_GREEN = colors.HexColor('#00D4AA')
OMNIX_BLUE = colors.HexColor('#4DABF7')
OMNIX_DARK = colors.HexColor('#0E1117')
OMNIX_CARD = colors.HexColor('#1E2130')
OMNIX_RED = colors.HexColor('#FF6B6B')


class InstitutionalReportGenerator:
    """
    V6.5.4 INSTITUTIONAL+ PREMIUM
    
    Genera informes PDF de calidad institucional para inversores.
    Formato compatible con presentaciones a fondos UAE/GCC.
    """
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        logger.info("📄 InstitutionalReportGenerator V6.5.4 PREMIUM inicializado")
    
    def _setup_custom_styles(self):
        self.styles.add(ParagraphStyle(
            'Title_Custom',
            parent=self.styles['Title'],
            fontSize=28,
            textColor=OMNIX_GREEN,
            spaceAfter=20,
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            'Heading_Custom',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=OMNIX_BLUE,
            spaceBefore=20,
            spaceAfter=10
        ))
        
        self.styles.add(ParagraphStyle(
            'Body_Custom',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.black,
            spaceAfter=8
        ))
        
        self.styles.add(ParagraphStyle(
            'Metric_Value',
            parent=self.styles['Normal'],
            fontSize=24,
            textColor=OMNIX_GREEN,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            'Metric_Label',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.gray,
            alignment=TA_CENTER
        ))
    
    def generate_report(
        self,
        metrics: Dict[str, Any],
        calibration: Dict[str, Any] = None,
        company_name: str = "OMNIX V6.5.4 INSTITUTIONAL+",
        period: str = "All Time"
    ) -> bytes:
        buffer = io.BytesIO()
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        story = []
        
        story.extend(self._build_header(company_name, period))
        
        story.extend(self._build_executive_summary(metrics))
        
        story.extend(self._build_risk_metrics(metrics))
        
        if metrics.get('pair_metrics'):
            story.extend(self._build_pair_analysis(metrics['pair_metrics']))
        
        if calibration:
            story.extend(self._build_calibration_section(calibration))
        
        story.extend(self._build_footer())
        
        doc.build(story)
        
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        logger.info(f"📄 Informe PDF generado: {len(pdf_bytes)} bytes")
        return pdf_bytes
    
    def _build_header(self, company_name: str, period: str) -> List:
        elements = []
        
        elements.append(Paragraph(company_name, self.styles['Title_Custom']))
        elements.append(Paragraph(
            f"Institutional Performance Report",
            self.styles['Heading1']
        ))
        
        elements.append(Spacer(1, 10))
        
        generated = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
        elements.append(Paragraph(
            f"<b>Period:</b> {period} | <b>Generated:</b> {generated}",
            self.styles['Body_Custom']
        ))
        
        elements.append(HRFlowable(
            width="100%",
            thickness=2,
            color=OMNIX_GREEN,
            spaceBefore=15,
            spaceAfter=15
        ))
        
        return elements
    
    def _build_executive_summary(self, metrics: Dict[str, Any]) -> List:
        elements = []
        
        elements.append(Paragraph("Executive Summary", self.styles['Heading_Custom']))
        
        summary_data = [
            ['Metric', 'Value', 'Industry Benchmark', 'Status'],
            [
                'Total Trades',
                str(metrics.get('total_trades', 0)),
                '500+ for credibility',
                'On Track' if metrics.get('total_trades', 0) >= 50 else 'Building'
            ],
            [
                'Win Rate',
                f"{metrics.get('win_rate', 0):.1f}%",
                '55%+',
                'PASS' if metrics.get('win_rate', 0) >= 55 else 'NEEDS WORK'
            ],
            [
                'Total P&L',
                f"${metrics.get('total_pnl', 0):,.2f}",
                'Positive',
                'PASS' if metrics.get('total_pnl', 0) > 0 else 'LOSS'
            ],
            [
                'Sharpe Ratio',
                f"{metrics.get('sharpe_ratio', 0):.3f}",
                '1.0+',
                'EXCELLENT' if metrics.get('sharpe_ratio', 0) >= 2.0 else 'GOOD' if metrics.get('sharpe_ratio', 0) >= 1.0 else 'FAIR'
            ],
            [
                'Max Drawdown',
                f"{metrics.get('max_drawdown', 0):.2f}%",
                '<20%',
                'PASS' if metrics.get('max_drawdown', 0) < 20 else 'HIGH'
            ],
        ]
        
        table = Table(summary_data, colWidths=[1.8*inch, 1.5*inch, 1.8*inch, 1.2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), OMNIX_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _build_risk_metrics(self, metrics: Dict[str, Any]) -> List:
        elements = []
        
        elements.append(Paragraph("Risk-Adjusted Performance", self.styles['Heading_Custom']))
        
        elements.append(Paragraph(
            "These metrics are industry-standard for institutional fund evaluation. "
            "Used by Citadel, Millennium, Point72, and Two Sigma.",
            self.styles['Body_Custom']
        ))
        
        risk_data = [
            ['Metric', 'Value', 'Description', 'Interpretation'],
            [
                'Sharpe Ratio',
                f"{metrics.get('sharpe_ratio', 0):.3f}",
                'Return / Total Volatility',
                self._interpret_sharpe(metrics.get('sharpe_ratio', 0))
            ],
            [
                'Sortino Ratio',
                f"{metrics.get('sortino_ratio', 0):.3f}",
                'Return / Downside Risk Only',
                self._interpret_sortino(metrics.get('sortino_ratio', 0))
            ],
            [
                'Calmar Ratio',
                f"{metrics.get('calmar_ratio', 0):.3f}",
                'Annual Return / Max Drawdown',
                self._interpret_calmar(metrics.get('calmar_ratio', 0))
            ],
            [
                'Profit Factor',
                f"{metrics.get('profit_factor', 0):.2f}",
                'Gross Profit / Gross Loss',
                'Good' if metrics.get('profit_factor', 0) >= 1.5 else 'Fair'
            ],
        ]
        
        table = Table(risk_data, colWidths=[1.4*inch, 1*inch, 2.2*inch, 1.4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), OMNIX_GREEN),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _build_pair_analysis(self, pair_metrics: Dict[str, Any]) -> List:
        elements = []
        
        elements.append(Paragraph("Per-Pair Performance Analysis", self.styles['Heading_Custom']))
        
        header = ['Symbol', 'Trades', 'Win Rate', 'P&L', 'Sharpe', 'Sortino', 'Calmar']
        data = [header]
        
        for symbol, pm in pair_metrics.items():
            if isinstance(pm, dict):
                row = [
                    symbol,
                    str(pm.get('total_trades', 0)),
                    f"{pm.get('win_rate', 0):.1f}%",
                    f"${pm.get('total_pnl', 0):.2f}",
                    f"{pm.get('sharpe_ratio', 0):.2f}",
                    f"{pm.get('sortino_ratio', 0):.2f}",
                    f"{pm.get('calmar_ratio', 0):.2f}"
                ]
            else:
                row = [
                    symbol,
                    str(pm.total_trades),
                    f"{pm.win_rate * 100:.1f}%",
                    f"${pm.total_pnl:.2f}",
                    f"{pm.sharpe_ratio:.2f}",
                    f"{pm.sortino_ratio:.2f}",
                    f"{pm.calmar_ratio:.2f}"
                ]
            data.append(row)
        
        table = Table(data, colWidths=[1.1*inch, 0.8*inch, 0.9*inch, 1*inch, 0.8*inch, 0.8*inch, 0.8*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), OMNIX_DARK),
            ('TEXTCOLOR', (0, 0), (-1, 0), OMNIX_GREEN),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _build_calibration_section(self, calibration: Dict[str, Any]) -> List:
        elements = []
        
        elements.append(PageBreak())
        elements.append(Paragraph("WIN_RATE_OPTIMIZED V2 PREMIUM Calibration", self.styles['Heading_Custom']))
        
        elements.append(Paragraph(
            "Per-pair calibration system with institutional-grade risk controls. "
            "Each pair has customized SL/TP, position limits, and circuit breakers.",
            self.styles['Body_Custom']
        ))
        
        header = ['Symbol', 'Tier', 'SL', 'TP', 'Max USD', 'Weight', 'Circuit Breaker']
        data = [header]
        
        for symbol, cal in calibration.items():
            tier = cal.tier.value if hasattr(cal.tier, 'value') else str(cal.tier)
            if tier == 'EXCLUDED':
                continue
            
            row = [
                symbol,
                tier,
                f"{cal.stop_loss_pct * 100:.1f}%",
                f"{cal.take_profit_pct * 100:.1f}%",
                f"${cal.max_position_usd:,.0f}",
                f"{cal.portfolio_weight * 100:.0f}%",
                f"{cal.max_daily_drawdown_pct * 100:.1f}%"
            ]
            data.append(row)
        
        table = Table(data, colWidths=[1*inch, 1*inch, 0.7*inch, 0.7*inch, 1*inch, 0.8*inch, 1.1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), OMNIX_GREEN),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _build_footer(self) -> List:
        elements = []
        
        elements.append(Spacer(1, 30))
        elements.append(HRFlowable(
            width="100%",
            thickness=1,
            color=colors.lightgrey,
            spaceBefore=10,
            spaceAfter=10
        ))
        
        elements.append(Paragraph(
            "<i>This report is generated automatically by OMNIX V6.5.4 INSTITUTIONAL+ trading system. "
            "Past performance is not indicative of future results. "
            "Trading cryptocurrencies involves significant risk.</i>",
            ParagraphStyle(
                'Footer',
                parent=self.styles['Normal'],
                fontSize=8,
                textColor=colors.gray,
                alignment=TA_CENTER
            )
        ))
        
        elements.append(Paragraph(
            f"<b>CONFIDENTIAL</b> - For authorized recipients only",
            ParagraphStyle(
                'Confidential',
                parent=self.styles['Normal'],
                fontSize=9,
                textColor=OMNIX_RED,
                alignment=TA_CENTER,
                spaceBefore=10
            )
        ))
        
        return elements
    
    def _interpret_sharpe(self, value: float) -> str:
        if value >= 3.0:
            return "Exceptional"
        elif value >= 2.0:
            return "Excellent"
        elif value >= 1.0:
            return "Good"
        elif value >= 0.5:
            return "Fair"
        else:
            return "Needs Work"
    
    def _interpret_sortino(self, value: float) -> str:
        if value >= 4.0:
            return "Exceptional"
        elif value >= 2.5:
            return "Excellent"
        elif value >= 1.5:
            return "Good"
        elif value >= 0.75:
            return "Fair"
        else:
            return "Needs Work"
    
    def _interpret_calmar(self, value: float) -> str:
        if value >= 5.0:
            return "Exceptional"
        elif value >= 3.0:
            return "Excellent"
        elif value >= 1.0:
            return "Good"
        elif value >= 0.5:
            return "Fair"
        else:
            return "Needs Work"
    
    def save_to_file(self, pdf_bytes: bytes, filename: str = None) -> str:
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"OMNIX_Institutional_Report_{timestamp}.pdf"
        
        reports_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        
        filepath = os.path.join(reports_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(pdf_bytes)
        
        logger.info(f"📄 Informe guardado: {filepath}")
        return filepath


_report_instance: Optional[InstitutionalReportGenerator] = None


def get_report_generator() -> InstitutionalReportGenerator:
    global _report_instance
    if _report_instance is None:
        _report_instance = InstitutionalReportGenerator()
    return _report_instance
