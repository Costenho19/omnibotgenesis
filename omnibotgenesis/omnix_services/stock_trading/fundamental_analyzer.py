"""
📈 Fundamental Analyzer
P/E ratios, earnings, financial metrics analysis
"""

import logging
import requests
from typing import Dict, Optional
import os

logger = logging.getLogger(__name__)


class FundamentalAnalyzer:
    """
    Analyze fundamental metrics for stocks
    P/E ratio, earnings, revenue, debt levels
    """
    
    def __init__(self):
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')
        self.fmp_key = os.getenv('FMP_API_KEY', '')  # Financial Modeling Prep (optional)
    
    def get_company_overview(self, symbol: str) -> Optional[Dict]:
        """
        Get company overview including P/E, market cap, etc.
        Uses Alpha Vantage API
        """
        try:
            params = {
                'function': 'OVERVIEW',
                'symbol': symbol,
                'apikey': self.alpha_vantage_key
            }
            
            response = requests.get(
                'https://www.alphavantage.co/query',
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'Symbol' not in data:
                    return None
                
                return {
                    'symbol': data.get('Symbol'),
                    'name': data.get('Name'),
                    'sector': data.get('Sector'),
                    'industry': data.get('Industry'),
                    'market_cap': self._parse_number(data.get('MarketCapitalization')),
                    'pe_ratio': self._parse_number(data.get('PERatio')),
                    'peg_ratio': self._parse_number(data.get('PEGRatio')),
                    'book_value': self._parse_number(data.get('BookValue')),
                    'dividend_yield': self._parse_number(data.get('DividendYield')),
                    'eps': self._parse_number(data.get('EPS')),
                    'revenue_per_share': self._parse_number(data.get('RevenuePerShareTTM')),
                    'profit_margin': self._parse_number(data.get('ProfitMargin')),
                    'operating_margin': self._parse_number(data.get('OperatingMarginTTM')),
                    'roe': self._parse_number(data.get('ReturnOnEquityTTM')),
                    'roa': self._parse_number(data.get('ReturnOnAssetsTTM')),
                    'debt_to_equity': self._parse_number(data.get('DebtToEquityRatio')),
                    'beta': self._parse_number(data.get('Beta')),
                    '52_week_high': self._parse_number(data.get('52WeekHigh')),
                    '52_week_low': self._parse_number(data.get('52WeekLow'))
                }
        
        except Exception as e:
            logger.error(f"Error fetching overview for {symbol}: {e}")
            return None
    
    def get_earnings_calendar(self, symbol: str) -> Optional[Dict]:
        """Get upcoming earnings date"""
        try:
            params = {
                'function': 'EARNINGS_CALENDAR',
                'symbol': symbol,
                'apikey': self.alpha_vantage_key
            }
            
            response = requests.get(
                'https://www.alphavantage.co/query',
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                # Parse CSV response
                lines = response.text.strip().split('\n')
                if len(lines) > 1:
                    headers = lines[0].split(',')
                    values = lines[1].split(',')
                    return dict(zip(headers, values))
        
        except Exception as e:
            logger.error(f"Error fetching earnings for {symbol}: {e}")
        
        return None
    
    def analyze_fundamentals(self, symbol: str) -> Optional[Dict]:
        """
        Complete fundamental analysis
        Returns score and recommendation
        """
        overview = self.get_company_overview(symbol)
        
        if not overview:
            return None
        
        score = 0
        max_score = 0
        reasons = []
        
        # P/E Ratio analysis
        if overview['pe_ratio']:
            max_score += 20
            pe = overview['pe_ratio']
            if 10 <= pe <= 25:
                score += 20
                reasons.append(f"✅ P/E saludable: {pe}")
            elif 5 <= pe < 10:
                score += 15
                reasons.append(f"🟡 P/E bajo (valor potencial): {pe}")
            elif pe > 35:
                score += 5
                reasons.append(f"⚠️ P/E alto (sobrevalorado): {pe}")
        
        # Profit Margin
        if overview['profit_margin']:
            max_score += 20
            margin = overview['profit_margin'] * 100
            if margin > 15:
                score += 20
                reasons.append(f"✅ Margen de ganancia fuerte: {margin:.1f}%")
            elif margin > 5:
                score += 10
                reasons.append(f"🟡 Margen moderado: {margin:.1f}%")
        
        # ROE (Return on Equity)
        if overview['roe']:
            max_score += 20
            roe = overview['roe'] * 100
            if roe > 15:
                score += 20
                reasons.append(f"✅ ROE excelente: {roe:.1f}%")
            elif roe > 8:
                score += 10
                reasons.append(f"🟡 ROE moderado: {roe:.1f}%")
        
        # Debt to Equity
        if overview['debt_to_equity']:
            max_score += 20
            de = overview['debt_to_equity']
            if de < 0.5:
                score += 20
                reasons.append(f"✅ Deuda baja: {de:.2f}")
            elif de < 1.5:
                score += 10
                reasons.append(f"🟡 Deuda moderada: {de:.2f}")
            else:
                score += 5
                reasons.append(f"⚠️ Deuda alta: {de:.2f}")
        
        # Dividend Yield
        if overview['dividend_yield']:
            max_score += 10
            div = overview['dividend_yield'] * 100
            if div > 2:
                score += 10
                reasons.append(f"✅ Dividendos: {div:.2f}%")
        
        # Beta (volatility)
        if overview['beta']:
            max_score += 10
            beta = overview['beta']
            if 0.8 <= beta <= 1.2:
                score += 10
                reasons.append(f"✅ Volatilidad moderada: β={beta:.2f}")
            elif beta < 0.8:
                score += 7
                reasons.append(f"🟡 Baja volatilidad: β={beta:.2f}")
        
        # Calculate percentage score
        if max_score > 0:
            score_pct = (score / max_score) * 100
        else:
            score_pct = 0
        
        # Generate recommendation
        if score_pct >= 75:
            recommendation = "COMPRA FUERTE"
            emoji = "🟢"
        elif score_pct >= 60:
            recommendation = "COMPRA"
            emoji = "🟢"
        elif score_pct >= 40:
            recommendation = "NEUTRAL/HOLD"
            emoji = "🟡"
        else:
            recommendation = "EVITAR"
            emoji = "🔴"
        
        return {
            'symbol': symbol,
            'name': overview['name'],
            'sector': overview['sector'],
            'score': round(score_pct, 1),
            'recommendation': recommendation,
            'emoji': emoji,
            'reasons': reasons,
            'overview': overview
        }
    
    def _parse_number(self, value: str) -> Optional[float]:
        """Parse string to float, return None if invalid"""
        if not value or value == 'None' or value == '-':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
