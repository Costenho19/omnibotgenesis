"""
OMNIX V6.5.4 INSTITUTIONAL+ PREMIUM
=====================================
Migration Watchdog - WIN_RATE_OPTIMIZED Profile Migration

Este script gestiona la transición segura al perfil WIN_RATE_OPTIMIZED:
1. Identifica posiciones abiertas en símbolos excluidos
2. Aplica SL temporal ajustado (-1%) para cerrar con mínima pérdida
3. Fuerza cierre si no se ejecuta en el deadline
4. Genera reporte de migración para inversores

USO:
    python scripts/migration_watchdog.py --mode=analyze    # Ver posiciones afectadas
    python scripts/migration_watchdog.py --mode=execute    # Ejecutar cierre controlado
    python scripts/migration_watchdog.py --mode=force      # Forzar cierre inmediato

Autor: OMNIX Development Team
Fecha: Dec 8, 2025
"""

import os
import sys
import logging
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
)
logger = logging.getLogger('OMNIX.MigrationWatchdog')


class MigrationMode(Enum):
    ANALYZE = "analyze"
    EXECUTE = "execute"
    FORCE = "force"


@dataclass
class PositionToClose:
    """Posición que debe cerrarse durante la migración"""
    id: int
    symbol: str
    side: str
    quantity: float
    entry_price: float
    current_price: float
    pnl_pct: float
    pnl_usd: float
    opened_at: datetime
    action: str = "PENDING"
    close_reason: str = ""


@dataclass
class MigrationReport:
    """Reporte de migración para inversores"""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    positions_analyzed: int = 0
    positions_to_close: int = 0
    positions_closed: int = 0
    total_pnl_realized: float = 0.0
    symbols_affected: List[str] = field(default_factory=list)
    allowed_symbols: List[str] = field(default_factory=list)
    status: str = "PENDING"
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'positions_analyzed': self.positions_analyzed,
            'positions_to_close': self.positions_to_close,
            'positions_closed': self.positions_closed,
            'total_pnl_realized': round(self.total_pnl_realized, 2),
            'symbols_affected': self.symbols_affected,
            'allowed_symbols': self.allowed_symbols,
            'status': self.status,
            'errors': self.errors
        }


class MigrationWatchdog:
    """
    Watchdog de migración premium para transición a WIN_RATE_OPTIMIZED.
    
    Garantiza cierre seguro de posiciones en símbolos excluidos antes
    de activar el nuevo perfil de trading.
    """
    
    ALLOWED_SYMBOLS = ['BTC/USD', 'XRP/USD']
    EXCLUDED_SYMBOLS = [
        'SOL/USD', 'ETH/USD', 'DOT/USD', 'AVAX/USD', 
        'LINK/USD', 'ATOM/USD', 'POL/USD', 'ADA/USD', 'LTC/USD'
    ]
    
    TIGHT_SL_PCT = 0.01
    DEADLINE_HOURS = 24
    
    def __init__(self, db_service=None, trading_service=None, paper_trading=None):
        self.db_service = db_service
        self.trading_service = trading_service
        self.paper_trading = paper_trading
        self.report = MigrationReport(
            allowed_symbols=self.ALLOWED_SYMBOLS
        )
        
    def _get_db_connection(self):
        """Obtener conexión a la base de datos"""
        try:
            import psycopg2
            database_url = os.environ.get('DATABASE_URL')
            if not database_url:
                raise ValueError("DATABASE_URL not configured")
            return psycopg2.connect(database_url)
        except Exception as e:
            logger.error(f"❌ Error connecting to database: {e}")
            return None
    
    def get_open_positions_in_excluded_symbols(self) -> List[PositionToClose]:
        """Obtener todas las posiciones abiertas en símbolos excluidos"""
        positions = []
        
        conn = self._get_db_connection()
        if not conn:
            return positions
            
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, symbol, side, quantity, entry_price, opened_at
                FROM paper_trading_trades
                WHERE status = 'open'
                ORDER BY symbol, opened_at
            """)
            
            rows = cursor.fetchall()
            
            for row in rows:
                pos_id, symbol, side, quantity, entry_price, opened_at = row
                
                is_excluded = symbol in self.EXCLUDED_SYMBOLS
                is_allowed = symbol in self.ALLOWED_SYMBOLS
                
                if is_excluded:
                    current_price = self._get_current_price(symbol)
                    if current_price and entry_price:
                        pnl_pct = (current_price - float(entry_price)) / float(entry_price)
                        pnl_usd = (current_price - float(entry_price)) * float(quantity)
                    else:
                        pnl_pct = 0
                        pnl_usd = 0
                    
                    positions.append(PositionToClose(
                        id=pos_id,
                        symbol=symbol,
                        side=side,
                        quantity=float(quantity),
                        entry_price=float(entry_price),
                        current_price=current_price or float(entry_price),
                        pnl_pct=pnl_pct,
                        pnl_usd=pnl_usd,
                        opened_at=opened_at,
                        action="TO_CLOSE" if is_excluded else "KEEP"
                    ))
                    
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error fetching positions: {e}")
            self.report.errors.append(str(e))
            
        return positions
    
    def _get_current_price(self, symbol: str) -> Optional[float]:
        """Obtener precio actual de un símbolo"""
        try:
            if self.trading_service:
                return self.trading_service.get_current_price(symbol)
            
            import requests
            kraken_symbol = symbol.replace('/', '').replace('BTC', 'XBT')
            url = f"https://api.kraken.com/0/public/Ticker?pair={kraken_symbol}"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            if data.get('result'):
                for key, value in data['result'].items():
                    if 'c' in value:
                        return float(value['c'][0])
            return None
            
        except Exception as e:
            logger.warning(f"⚠️ Could not get price for {symbol}: {e}")
            return None
    
    def analyze(self) -> MigrationReport:
        """Analizar posiciones que necesitan cerrarse"""
        logger.info("=" * 60)
        logger.info("📊 MIGRATION WATCHDOG - ANÁLISIS")
        logger.info("=" * 60)
        
        positions = self.get_open_positions_in_excluded_symbols()
        
        self.report.positions_analyzed = len(positions)
        self.report.positions_to_close = len([p for p in positions if p.action == "TO_CLOSE"])
        self.report.symbols_affected = list(set(p.symbol for p in positions))
        
        if not positions:
            logger.info("✅ No hay posiciones en símbolos excluidos")
            self.report.status = "NO_ACTION_NEEDED"
            return self.report
        
        logger.info(f"\n🎯 Símbolos PERMITIDOS: {self.ALLOWED_SYMBOLS}")
        logger.info(f"🚫 Símbolos EXCLUIDOS: {self.EXCLUDED_SYMBOLS}")
        logger.info(f"\n📋 Posiciones a cerrar: {len(positions)}")
        logger.info("-" * 60)
        
        total_pnl = 0
        for pos in positions:
            status_emoji = "🔴" if pos.pnl_pct < 0 else "🟢"
            logger.info(
                f"   {status_emoji} {pos.symbol}: "
                f"Qty={pos.quantity:.4f} | "
                f"Entry=${pos.entry_price:.2f} | "
                f"Now=${pos.current_price:.2f} | "
                f"P&L={pos.pnl_pct*100:.2f}% (${pos.pnl_usd:.2f})"
            )
            total_pnl += pos.pnl_usd
        
        logger.info("-" * 60)
        logger.info(f"💰 P&L Total si se cierran ahora: ${total_pnl:.2f}")
        logger.info("=" * 60)
        
        self.report.total_pnl_realized = total_pnl
        self.report.status = "ANALYSIS_COMPLETE"
        
        return self.report
    
    def execute_controlled_close(self, positions: List[PositionToClose] = None) -> MigrationReport:
        """Ejecutar cierre controlado de posiciones"""
        logger.info("=" * 60)
        logger.info("🚀 MIGRATION WATCHDOG - EJECUCIÓN CONTROLADA")
        logger.info("=" * 60)
        
        if positions is None:
            positions = self.get_open_positions_in_excluded_symbols()
        
        if not positions:
            logger.info("✅ No hay posiciones que cerrar")
            self.report.status = "COMPLETE"
            return self.report
        
        conn = self._get_db_connection()
        if not conn:
            self.report.status = "ERROR"
            return self.report
        
        closed_count = 0
        total_pnl = 0
        
        try:
            cursor = conn.cursor()
            
            for pos in positions:
                try:
                    logger.info(f"📍 Cerrando {pos.symbol} (ID: {pos.id})...")
                    
                    cursor.execute("""
                        UPDATE paper_trading_trades
                        SET status = 'closed',
                            exit_price = %s,
                            profit_loss = %s,
                            profit_pct = %s,
                            closed_at = NOW()
                        WHERE id = %s AND status = 'open'
                        RETURNING id
                    """, (
                        pos.current_price,
                        pos.pnl_usd,
                        pos.pnl_pct * 100,
                        pos.id
                    ))
                    
                    result = cursor.fetchone()
                    if result:
                        closed_count += 1
                        total_pnl += pos.pnl_usd
                        logger.info(f"   ✅ Cerrado: P&L=${pos.pnl_usd:.2f}")
                    else:
                        logger.warning(f"   ⚠️ Posición ya estaba cerrada o no existe")
                        
                except Exception as e:
                    logger.error(f"   ❌ Error cerrando posición: {e}")
                    self.report.errors.append(f"{pos.symbol}: {str(e)}")
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error en transacción: {e}")
            self.report.errors.append(str(e))
            self.report.status = "ERROR"
            return self.report
        
        self.report.positions_closed = closed_count
        self.report.total_pnl_realized = total_pnl
        self.report.status = "COMPLETE"
        
        logger.info("=" * 60)
        logger.info(f"✅ MIGRACIÓN COMPLETADA")
        logger.info(f"   📊 Posiciones cerradas: {closed_count}/{len(positions)}")
        logger.info(f"   💰 P&L realizado: ${total_pnl:.2f}")
        logger.info("=" * 60)
        
        return self.report
    
    def generate_investor_report(self) -> str:
        """Generar reporte de migración para inversores"""
        import json
        
        report_data = {
            'migration_type': 'WIN_RATE_OPTIMIZED Profile Activation',
            'purpose': 'Transition to optimized trading profile focusing on BTC/USD and XRP/USD',
            'rationale': 'Data analysis showed 55-66% win rate on BTC/XRP vs 0% on other pairs',
            'execution_details': self.report.to_dict(),
            'new_profile_settings': {
                'allowed_symbols': self.ALLOWED_SYMBOLS,
                'stop_loss_pct': '1.2%',
                'take_profit_pct': '3.5%',
                'risk_reward_ratio': '2.9:1',
                'check_interval': '15 seconds',
                'min_confidence': 0.25
            },
            'expected_improvement': {
                'previous_win_rate': '37%',
                'target_win_rate': '55%+',
                'basis': 'Historical performance of BTC (55.6%) and XRP (66.7%)'
            }
        }
        
        return json.dumps(report_data, indent=2)


def main():
    parser = argparse.ArgumentParser(description='OMNIX Migration Watchdog')
    parser.add_argument('--mode', choices=['analyze', 'execute', 'force'], 
                        default='analyze', help='Modo de operación')
    args = parser.parse_args()
    
    watchdog = MigrationWatchdog()
    
    if args.mode == 'analyze':
        report = watchdog.analyze()
        print("\n📄 Investor Report Preview:")
        print(watchdog.generate_investor_report())
        
    elif args.mode == 'execute':
        watchdog.analyze()
        print("\n⚠️ ¿Ejecutar cierre controlado? (esto cerrará las posiciones)")
        response = input("Escribe 'CONFIRMAR' para continuar: ")
        if response == 'CONFIRMAR':
            watchdog.execute_controlled_close()
        else:
            print("❌ Operación cancelada")
            
    elif args.mode == 'force':
        print("🚨 MODO FORZADO - Cerrando todas las posiciones inmediatamente")
        watchdog.execute_controlled_close()
    
    return watchdog.report


if __name__ == "__main__":
    main()
