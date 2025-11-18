#!/usr/bin/env python3
"""
🏆 ESTRATEGIA PROFESIONAL - 73% WIN RATE
Carga automática de parámetros optimizados para OMNIX

Basado en: https://www.quantifiedstrategies.com/macd-and-rsi-strategy/
Desarrollado por: Harold Nunes - Noviembre 2025
"""

import sys
from datetime import datetime

# Propuestas de la estrategia profesional del 73% Win Rate
PROFESSIONAL_PROPOSALS = [
    {
        'param_name': 'rsi_threshold_oversold',
        'new_value': 30,
        'current_value': 14,
        'video_url': 'https://www.quantifiedstrategies.com/macd-and-rsi-strategy/',
        'timestamp': datetime.now().isoformat(),
        'confidence': 0.95,
        'reason': '🏆 Estrategia Triple Indicador - 73% Win Rate comprobado. RSI sobreventa estándar en 30'
    },
    {
        'param_name': 'rsi_threshold_overbought',
        'new_value': 70,
        'current_value': 86,
        'video_url': 'https://www.quantifiedstrategies.com/macd-and-rsi-strategy/',
        'timestamp': datetime.now().isoformat(),
        'confidence': 0.95,
        'reason': '🏆 RSI sobrecompra estándar en 70 - Comprobado en 235 trades'
    },
    {
        'param_name': 'ema_fast_period',
        'new_value': 9,
        'current_value': 8,
        'video_url': 'https://www.quantifiedstrategies.com/macd-and-rsi-strategy/',
        'timestamp': datetime.now().isoformat(),
        'confidence': 0.95,
        'reason': '🏆 EMA rápida en 9 períodos - Señales más precisas según backtesting'
    },
    {
        'param_name': 'ema_medium_period',
        'new_value': 21,
        'current_value': 21,
        'video_url': 'https://www.quantifiedstrategies.com/macd-and-rsi-strategy/',
        'timestamp': datetime.now().isoformat(),
        'confidence': 0.95,
        'reason': '✅ EMA media en 21 períodos - Ya optimizado'
    },
    {
        'param_name': 'ema_slow_period',
        'new_value': 50,
        'current_value': 55,
        'video_url': 'https://www.quantifiedstrategies.com/macd-and-rsi-strategy/',
        'timestamp': datetime.now().isoformat(),
        'confidence': 0.92,
        'reason': '🏆 EMA lenta en 50 períodos - Filtro de tendencia largo plazo'
    }
]

def main():
    """
    Carga las propuestas profesionales en el sistema
    """
    print("\n" + "="*70)
    print("🏆 ESTRATEGIA PROFESIONAL - 73% WIN RATE")
    print("="*70)
    print("\n📊 PARÁMETROS OPTIMIZADOS:\n")
    
    # Importar el sistema global
    try:
        # Intentar importar desde main.py
        import main
        
        if hasattr(main, 'global_pending_proposals'):
            # Limpiar propuestas anteriores
            main.global_pending_proposals.clear()
            
            # Agregar nuevas propuestas
            for prop in PROFESSIONAL_PROPOSALS:
                main.global_pending_proposals.append(prop)
                
                param_name = prop['param_name'].replace('_', ' ').title()
                print(f"✅ {param_name}")
                print(f"   Actual: {prop['current_value']} → Nuevo: {prop['new_value']}")
                print(f"   {prop['reason']}\n")
            
            print(f"💾 {len(PROFESSIONAL_PROPOSALS)} propuestas cargadas exitosamente")
            print("\n📱 PRÓXIMOS PASOS:")
            print("1. Abre Telegram")
            print("2. Envía: /ver_propuestas")
            print("3. Revisa los cambios")
            print("4. Si te gustan, envía: /aprobar_ajustes")
            print("\n🚀 OMNIX V5.4 - Professional Strategy Loaded")
            print("="*70 + "\n")
            
        else:
            print("⚠️ Error: global_pending_proposals no encontrado en main.py")
            print("💡 El bot debe estar corriendo primero")
            
    except ImportError:
        print("⚠️ No se pudo importar main.py")
        print("\n💡 MÉTODO ALTERNATIVO:")
        print("Copia y pega esto en Telegram:\n")
        print("---")
        print("📊 ESTRATEGIA PROFESIONAL - 73% WIN RATE")
        print("\nPropuestas:")
        for i, prop in enumerate(PROFESSIONAL_PROPOSALS, 1):
            param_name = prop['param_name'].replace('_', ' ').title()
            print(f"{i}. {param_name}: {prop['current_value']} → {prop['new_value']}")
        print("\nFuente: https://www.quantifiedstrategies.com/macd-and-rsi-strategy/")
        print("---")

if __name__ == "__main__":
    main()
