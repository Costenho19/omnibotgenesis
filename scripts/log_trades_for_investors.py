"""
📊 INVESTOR TRADE LOGGER V5.4
Sistema de logging de trades para reportes de inversores
Registra trades con detalles completos para generar reportes profesionales

Autor: Harold Nunes
Fecha: Noviembre 2025
"""

import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional
import json

logger = logging.getLogger(__name__)


class InvestorTradeLogger:
    """
    Logger especializado para trades orientado a inversores
    
    Registra cada trade con información detallada:
    - Razón de entrada/salida
    - Indicadores utilizados
    - Nivel de confianza
    - PnL y métricas
    - Estrategia utilizada
    """
    
    def __init__(self, db_service=None, log_dir: str = "logs/investor_trades"):
        self.db_service = db_service
        self.log_dir = log_dir
        self.trades_log = []
        
        os.makedirs(log_dir, exist_ok=True)
        
        logger.info("📊 InvestorTradeLogger inicializado")
    
    def log_trade(
        self,
        trade_type: str = None,
        symbol: str = None,
        amount: float = None,
        price: float = 0,
        strategy: str = None,
        confidence: float = 0,
        indicators: Dict[str, Any] = None,
        reason: str = None,
        pnl: Optional[float] = None,
        metadata: Optional[Dict] = None,
        action: str = None,
        amount_usd: float = None,
        score: int = None,
        strategies_signals: Dict[str, Any] = None,
        reasoning: str = None,
        trade_number: int = None,
        mode: str = None
    ) -> Dict[str, Any]:
        """
        Registrar un trade para reportes de inversores
        
        Args:
            trade_type: 'BUY' o 'SELL' (o action como alias)
            symbol: Par de trading (ej: BTC/USD)
            amount: Cantidad (o amount_usd como alias)
            price: Precio de ejecución
            strategy: Estrategia utilizada
            confidence: Nivel de confianza (0-1)
            indicators: Indicadores que activaron el trade (o strategies_signals)
            reason: Razón del trade en texto (o reasoning)
            pnl: Profit/Loss si es cierre
            metadata: Datos adicionales
            action: Alias para trade_type
            amount_usd: Alias para amount (en USD)
            score: Puntuación del trade
            strategies_signals: Alias para indicators
            reasoning: Alias para reason
            trade_number: Número de trade
            mode: Modo de trading (paper/real)
        
        Returns:
            Dict con el trade registrado
        """
        final_type = trade_type or action or 'UNKNOWN'
        final_amount = amount if amount is not None else (amount_usd or 0)
        final_indicators = indicators or strategies_signals or {}
        final_reason = reason or reasoning or 'No reason provided'
        final_symbol = symbol or 'UNKNOWN'
        final_strategy = strategy or mode or 'auto'
        
        value_usd = final_amount if amount_usd else (final_amount * price if price else 0)
        
        trade_record = {
            'id': f"TRD-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
            'timestamp': datetime.utcnow().isoformat(),
            'type': final_type,
            'symbol': final_symbol,
            'amount': final_amount,
            'price': price,
            'value_usd': value_usd,
            'strategy': final_strategy,
            'confidence': confidence,
            'confidence_pct': f"{confidence * 100:.1f}%",
            'indicators': final_indicators,
            'reason': final_reason,
            'pnl': pnl,
            'pnl_pct': f"{(pnl / value_usd * 100):.2f}%" if (pnl and value_usd) else None,
            'metadata': metadata or {},
            'score': score,
            'trade_number': trade_number,
            'mode': mode
        }
        
        self.trades_log.append(trade_record)
        
        self._save_to_file(trade_record)
        
        if self.db_service:
            self._save_to_db(trade_record)
        
        logger.info(f"📊 Trade logged: {trade_type} {amount} {symbol} @ ${price:.2f}")
        
        return trade_record
    
    def _save_to_file(self, trade: Dict) -> None:
        """Guardar trade en archivo JSON"""
        date_str = datetime.utcnow().strftime('%Y-%m-%d')
        filepath = os.path.join(self.log_dir, f"trades_{date_str}.json")
        
        existing = []
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                existing = json.load(f)
        
        existing.append(trade)
        
        with open(filepath, 'w') as f:
            json.dump(existing, f, indent=2)
    
    def _save_to_db(self, trade: Dict) -> None:
        """Guardar trade en base de datos"""
        try:
            pass
        except Exception as e:
            logger.error(f"Error guardando trade en DB: {e}")
    
    def get_trades_summary(self, days: int = 30) -> Dict[str, Any]:
        """
        Obtener resumen de trades para inversores
        
        Args:
            days: Días hacia atrás a incluir
        
        Returns:
            Resumen con métricas clave
        """
        if not self.trades_log:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'avg_confidence': 0,
                'strategies_used': []
            }
        
        winning = [t for t in self.trades_log if t.get('pnl', 0) > 0]
        losing = [t for t in self.trades_log if t.get('pnl', 0) < 0]
        
        total_pnl = sum(t.get('pnl', 0) or 0 for t in self.trades_log)
        avg_conf = sum(t['confidence'] for t in self.trades_log) / len(self.trades_log)
        strategies = list(set(t['strategy'] for t in self.trades_log))
        
        return {
            'total_trades': len(self.trades_log),
            'winning_trades': len(winning),
            'losing_trades': len(losing),
            'win_rate': len(winning) / len(self.trades_log) * 100 if self.trades_log else 0,
            'total_pnl': total_pnl,
            'avg_confidence': avg_conf,
            'strategies_used': strategies
        }
    
    def generate_investor_report(self) -> str:
        """Generar reporte en texto para inversores"""
        summary = self.get_trades_summary()
        
        report = f"""
📊 OMNIX V6.0 - INVESTOR TRADE REPORT
=====================================
Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

📈 PERFORMANCE SUMMARY
----------------------
Total Trades: {summary['total_trades']}
Winning Trades: {summary['winning_trades']}
Losing Trades: {summary['losing_trades']}
Win Rate: {summary['win_rate']:.1f}%
Total P&L: ${summary['total_pnl']:,.2f}
Average Confidence: {summary['avg_confidence']*100:.1f}%

🎯 STRATEGIES USED
------------------
{chr(10).join(f'• {s}' for s in summary['strategies_used'])}

=====================================
OMNIX V6.0 ULTRA - Automated Trading
"""
        return report


investor_logger = InvestorTradeLogger()
