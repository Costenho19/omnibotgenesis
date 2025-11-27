#!/usr/bin/env python3
"""
🔬 OMNIX V6.0 ULTRA - Professional Strategy Validation Script
Ejecuta validación completa anti-overfitting para estrategias ARES

USO:
    python omnix_testing/run_professional_validation.py

SALIDA:
    - Reporte de validación en consola
    - Métricas honestas para inversores
    - Detección de overfitting
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from datetime import datetime, timedelta
from typing import List, Dict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

from omnix_testing.professional_validator import (
    ProfessionalValidator,
    CostModel
)


def simple_momentum_strategy(data: List[Dict]) -> str:
    """
    Estrategia de momentum simple para testing
    
    Compra cuando precio > SMA20, vende cuando precio < SMA20
    """
    if len(data) < 20:
        return 'hold'
    
    closes = [c['close'] for c in data]
    sma_20 = sum(closes[-20:]) / 20
    current_price = closes[-1]
    prev_price = closes[-2] if len(closes) > 1 else current_price
    
    if current_price > sma_20 and prev_price <= sma_20:
        return 'buy'
    elif current_price < sma_20 and prev_price >= sma_20:
        return 'sell'
    
    return 'hold'


def generate_sample_data(days: int = 365) -> List[Dict]:
    """Genera datos de muestra para testing (cuando Kraken API no está disponible)"""
    import random
    
    data = []
    base_price = 50000.0
    current_price = base_price
    
    start_timestamp = int(datetime.now().timestamp()) - (days * 24 * 3600)
    
    for i in range(days):
        change = random.gauss(0, 0.02)
        current_price = current_price * (1 + change)
        
        high = current_price * (1 + abs(random.gauss(0, 0.01)))
        low = current_price * (1 - abs(random.gauss(0, 0.01)))
        open_price = current_price * (1 + random.gauss(0, 0.005))
        
        data.append({
            'timestamp': start_timestamp + (i * 24 * 3600),
            'open': open_price,
            'high': max(high, open_price, current_price),
            'low': min(low, open_price, current_price),
            'close': current_price,
            'volume': random.uniform(100, 1000)
        })
    
    return data


def main():
    """Ejecutar validación profesional"""
    print("\n" + "=" * 70)
    print("🔬 OMNIX V6.0 ULTRA - PROFESSIONAL STRATEGY VALIDATION")
    print("=" * 70)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("🎯 Purpose: Eliminate overfitting, generate honest investor metrics")
    print("=" * 70 + "\n")
    
    cost_model = CostModel(
        maker_fee=0.0016,    # 0.16% Kraken maker
        taker_fee=0.0026,    # 0.26% Kraken taker
        slippage_bps=5,      # 0.05% slippage
        spread_bps=10        # 0.10% spread
    )
    
    validator = ProfessionalValidator(cost_model=cost_model)
    
    print("📊 Generating sample data for validation...")
    sample_data = generate_sample_data(days=365)
    print(f"   ✅ Generated {len(sample_data)} data points (1 year)\n")
    
    print("🔄 Running Full Validation Suite...")
    print("-" * 50)
    
    report = validator.run_full_validation(
        strategy_name="Momentum Strategy (Sample)",
        strategy=simple_momentum_strategy,
        data=sample_data,
        initial_balance=10000.0
    )
    
    print("\n" + "=" * 70)
    print(report.investor_summary)
    print("=" * 70)
    
    print("\n📋 SUMMARY:")
    print(f"   • Strategy: {report.strategy_name}")
    print(f"   • Overall Grade: {report.overall_score}")
    print(f"   • Validation Date: {report.validation_date.strftime('%Y-%m-%d %H:%M')}")
    
    print("\n🎯 HONEST EXPECTATIONS (For Investors):")
    for key, value in report.honest_expectations.items():
        if key != 'disclaimer':
            print(f"   • {key.replace('_', ' ').title()}: {value}")
    
    print("\n" + "=" * 70)
    print("✅ VALIDATION COMPLETE")
    print("=" * 70 + "\n")
    
    return report


if __name__ == "__main__":
    main()
