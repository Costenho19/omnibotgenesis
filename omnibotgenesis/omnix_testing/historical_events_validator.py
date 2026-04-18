#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMNIX V6.0 ULTRA - Historical Events Validator
Sistema PREMIUM de validación con eventos críticos históricos
Genera pruebas verificables para inversionistas
Desarrollado por Harold Nunes - Noviembre 2025
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
import pandas as pd
import json
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class HistoricalEvent:
    """Evento histórico crítico para validación"""
    name: str
    description: str
    start_date: datetime
    end_date: datetime
    event_type: str  # 'crash', 'rally', 'volatility', 'recovery'
    expected_difficulty: str  # 'extreme', 'high', 'medium'
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'description': self.description,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'event_type': self.event_type,
            'expected_difficulty': self.expected_difficulty
        }


class HistoricalEventsValidator:
    """
    Sistema PREMIUM de validación con eventos históricos
    
    Valida rendimiento de OMNIX en:
    - COVID-19 Crash (Marzo 2020)
    - Bull Run 2021
    - China Ban (Mayo 2021)
    - Terra/Luna Collapse (Mayo 2022)
    - FTX Collapse (Noviembre 2022)
    - Bear Market 2022
    - Recovery 2023-2024
    """
    
    CRITICAL_EVENTS = [
        HistoricalEvent(
            name="COVID-19 Crash",
            description="Caída histórica del 50% en 2 días (12-13 Marzo 2020)",
            start_date=datetime(2020, 3, 8),
            end_date=datetime(2020, 3, 20),
            event_type='crash',
            expected_difficulty='extreme'
        ),
        HistoricalEvent(
            name="Post-COVID Recovery",
            description="Recuperación rápida después del crash COVID",
            start_date=datetime(2020, 3, 21),
            end_date=datetime(2020, 5, 15),
            event_type='recovery',
            expected_difficulty='medium'
        ),
        HistoricalEvent(
            name="Bull Run 2020-2021",
            description="Rally histórico de $10K a $64K",
            start_date=datetime(2020, 10, 1),
            end_date=datetime(2021, 4, 14),
            event_type='rally',
            expected_difficulty='medium'
        ),
        HistoricalEvent(
            name="China Mining Ban",
            description="Caída del 50% por prohibición de minería en China",
            start_date=datetime(2021, 5, 10),
            end_date=datetime(2021, 7, 25),
            event_type='crash',
            expected_difficulty='high'
        ),
        HistoricalEvent(
            name="ATH Rejection & Bear Start",
            description="Rechazo del ATH $69K e inicio del bear market",
            start_date=datetime(2021, 11, 1),
            end_date=datetime(2022, 1, 31),
            event_type='crash',
            expected_difficulty='high'
        ),
        HistoricalEvent(
            name="Terra/Luna Collapse",
            description="Colapso de Terra/Luna - contagio al mercado",
            start_date=datetime(2022, 5, 5),
            end_date=datetime(2022, 6, 30),
            event_type='crash',
            expected_difficulty='extreme'
        ),
        HistoricalEvent(
            name="FTX Collapse",
            description="Quiebra de FTX - caída a $15K",
            start_date=datetime(2022, 11, 1),
            end_date=datetime(2022, 12, 15),
            event_type='crash',
            expected_difficulty='extreme'
        ),
        HistoricalEvent(
            name="Bear Market 2022",
            description="Bear market completo - mínimo $15.5K",
            start_date=datetime(2022, 6, 1),
            end_date=datetime(2022, 12, 31),
            event_type='volatility',
            expected_difficulty='high'
        ),
        HistoricalEvent(
            name="2023 Recovery",
            description="Recuperación gradual de $15K a $30K",
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31),
            event_type='recovery',
            expected_difficulty='medium'
        ),
        HistoricalEvent(
            name="2024 Bull Run",
            description="Rally post-Halving hacia nuevos ATH",
            start_date=datetime(2024, 1, 1),
            end_date=datetime.now(),
            event_type='rally',
            expected_difficulty='medium'
        )
    ]
    
    def __init__(self, backtesting_engine=None):
        """
        Initialize Historical Events Validator
        
        Args:
            backtesting_engine: BacktestingEngine instance (optional)
        """
        self.backtesting_engine = backtesting_engine
        self.results = []
        
        # Create reports directory
        self.reports_dir = Path("omnix_testing/reports/validation")
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("=" * 70)
        logger.info("🎯 HISTORICAL EVENTS VALIDATOR INICIALIZADO")
        logger.info(f"   📊 {len(self.CRITICAL_EVENTS)} eventos históricos cargados")
        logger.info("=" * 70)
    
    def validate_all_events(
        self,
        strategy_name: str = "ares_v1_swing",
        interval: str = "4h",
        initial_capital: float = 10000.0
    ) -> Dict:
        """
        Valida rendimiento en TODOS los eventos históricos
        
        Args:
            strategy_name: Estrategia a validar
            interval: Timeframe
            initial_capital: Capital inicial
            
        Returns:
            Dictionary con resultados completos de validación
        """
        logger.info("=" * 70)
        logger.info("🚀 VALIDACIÓN HISTÓRICA COMPLETA")
        logger.info("=" * 70)
        logger.info(f"📊 Estrategia: {strategy_name}")
        logger.info(f"⏱️ Timeframe: {interval}")
        logger.info(f"💰 Capital: ${initial_capital:,.2f}")
        logger.info("=" * 70)
        
        if not self.backtesting_engine:
            logger.error("❌ BacktestingEngine no configurado")
            return {'error': 'No backtesting engine'}
        
        self.results = []
        
        for i, event in enumerate(self.CRITICAL_EVENTS, 1):
            logger.info(f"\n📍 EVENTO {i}/{len(self.CRITICAL_EVENTS)}: {event.name}")
            logger.info(f"   📅 {event.start_date.date()} → {event.end_date.date()}")
            logger.info(f"   🎯 Tipo: {event.event_type.upper()}")
            logger.info(f"   ⚠️ Dificultad: {event.expected_difficulty.upper()}")
            
            try:
                # Run backtest for this event
                result = self.backtesting_engine.run_backtest(
                    pair="XBTUSD",
                    interval=interval,
                    start_date=event.start_date,
                    end_date=event.end_date,
                    strategy_name=strategy_name
                )
                
                # Extract key metrics
                metrics = result.get('metrics', {})
                
                event_result = {
                    'event': event.to_dict(),
                    'metrics': {
                        'total_return': metrics.get('total_return', 0),
                        'win_rate': metrics.get('win_rate', 0),
                        'sharpe_ratio': metrics.get('sharpe_ratio', 0),
                        'max_drawdown': metrics.get('max_drawdown_pct', 0),
                        'total_trades': metrics.get('total_trades', 0),
                        'profit_factor': metrics.get('profit_factor', 0),
                        'final_capital': metrics.get('final_capital', 0)
                    },
                    'success': metrics.get('total_return', 0) > 0
                }
                
                self.results.append(event_result)
                
                # Log quick summary
                logger.info(f"   ✅ Return: {metrics.get('total_return', 0):.2f}%")
                logger.info(f"   ✅ Win Rate: {metrics.get('win_rate', 0):.1f}%")
                logger.info(f"   ✅ Max DD: {metrics.get('max_drawdown_pct', 0):.2f}%")
                
            except Exception as e:
                logger.error(f"   ❌ Error en evento {event.name}: {str(e)}")
                event_result = {
                    'event': event.to_dict(),
                    'error': str(e),
                    'success': False
                }
                self.results.append(event_result)
        
        # Generate summary
        summary = self._generate_summary()
        
        # Save results
        self._save_results(strategy_name)
        
        logger.info("\n" + "=" * 70)
        logger.info("✅ VALIDACIÓN HISTÓRICA COMPLETADA")
        logger.info("=" * 70)
        
        return {
            'strategy': strategy_name,
            'interval': interval,
            'initial_capital': initial_capital,
            'events_tested': len(self.CRITICAL_EVENTS),
            'results': self.results,
            'summary': summary
        }
    
    def validate_single_event(
        self,
        event_name: str,
        strategy_name: str = "ares_v1_swing",
        interval: str = "4h"
    ) -> Optional[Dict]:
        """
        Valida rendimiento en un evento específico
        
        Args:
            event_name: Nombre del evento a validar
            strategy_name: Estrategia a usar
            interval: Timeframe
            
        Returns:
            Dictionary con resultados del evento
        """
        # Find event
        event = None
        for e in self.CRITICAL_EVENTS:
            if e.name.lower() == event_name.lower():
                event = e
                break
        
        if not event:
            logger.error(f"❌ Evento '{event_name}' no encontrado")
            return None
        
        logger.info(f"🎯 Validando evento: {event.name}")
        logger.info(f"   📅 {event.start_date.date()} → {event.end_date.date()}")
        
        if not self.backtesting_engine:
            logger.error("❌ BacktestingEngine no configurado")
            return None
        
        result = self.backtesting_engine.run_backtest(
            pair="XBTUSD",
            interval=interval,
            start_date=event.start_date,
            end_date=event.end_date,
            strategy_name=strategy_name
        )
        
        return result
    
    def _generate_summary(self) -> Dict:
        """Generate summary statistics from all events"""
        if not self.results:
            return {}
        
        successful_events = [r for r in self.results if r.get('success', False)]
        total_events = len(self.results)
        success_rate = (len(successful_events) / total_events * 100) if total_events > 0 else 0
        
        # Calculate averages
        avg_return = sum(r['metrics']['total_return'] for r in successful_events) / len(successful_events) if successful_events else 0
        avg_win_rate = sum(r['metrics']['win_rate'] for r in successful_events) / len(successful_events) if successful_events else 0
        avg_sharpe = sum(r['metrics']['sharpe_ratio'] for r in successful_events) / len(successful_events) if successful_events else 0
        worst_drawdown = min((r['metrics']['max_drawdown'] for r in successful_events), default=0)
        
        # Count by event type
        crashes_survived = sum(1 for r in successful_events if r['event']['event_type'] == 'crash')
        total_crashes = sum(1 for r in self.results if r['event']['event_type'] == 'crash')
        
        summary = {
            'total_events': total_events,
            'successful_events': len(successful_events),
            'success_rate': success_rate,
            'avg_return': avg_return,
            'avg_win_rate': avg_win_rate,
            'avg_sharpe_ratio': avg_sharpe,
            'worst_drawdown': worst_drawdown,
            'crashes_tested': total_crashes,
            'crashes_survived': crashes_survived,
            'crash_survival_rate': (crashes_survived / total_crashes * 100) if total_crashes > 0 else 0
        }
        
        logger.info("\n📊 RESUMEN DE VALIDACIÓN:")
        logger.info(f"   ✅ Eventos exitosos: {len(successful_events)}/{total_events} ({success_rate:.1f}%)")
        logger.info(f"   📈 Return promedio: {avg_return:.2f}%")
        logger.info(f"   🎯 Win rate promedio: {avg_win_rate:.1f}%")
        logger.info(f"   📊 Sharpe promedio: {avg_sharpe:.3f}")
        logger.info(f"   💥 Crashes sobrevividos: {crashes_survived}/{total_crashes}")
        
        return summary
    
    def _save_results(self, strategy_name: str):
        """Save validation results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"validation_{strategy_name}_{timestamp}.json"
        filepath = self.reports_dir / filename
        
        data = {
            'timestamp': timestamp,
            'strategy': strategy_name,
            'results': self.results
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n💾 Resultados guardados: {filepath}")
    
    def get_event_names(self) -> List[str]:
        """Get list of all available event names"""
        return [event.name for event in self.CRITICAL_EVENTS]
    
    def print_events_summary(self):
        """Print summary of all available events"""
        print("\n" + "=" * 70)
        print("📅 EVENTOS HISTÓRICOS DISPONIBLES")
        print("=" * 70)
        
        for i, event in enumerate(self.CRITICAL_EVENTS, 1):
            duration = (event.end_date - event.start_date).days
            print(f"\n{i}. {event.name}")
            print(f"   📅 {event.start_date.date()} → {event.end_date.date()} ({duration} días)")
            print(f"   🎯 Tipo: {event.event_type.upper()}")
            print(f"   ⚠️ Dificultad: {event.expected_difficulty.upper()}")
            print(f"   📝 {event.description}")
        
        print("\n" + "=" * 70)


def main():
    """Main execution for testing"""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from omnix_testing.backtesting.backtesting_engine import BacktestingEngine
    
    # Initialize
    validator = HistoricalEventsValidator()
    validator.print_events_summary()
    
    print("\n🎯 Para validar, usa:")
    print("   validator.backtesting_engine = BacktestingEngine()")
    print("   results = validator.validate_all_events()")


if __name__ == "__main__":
    main()
