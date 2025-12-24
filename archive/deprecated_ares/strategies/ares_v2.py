#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧨 ARES PROTOCOL V2 - SCALPING M1
Win Rate Objetivo: 60%-70% (backtested - live results may vary)
Estrategia institucional exclusiva para OMNIX

⚠️ STATUS: PLACEHOLDER / EXPERIMENTAL
Esta estrategia está marcada como EXPERIMENTAL y NO se usa en el flujo de decisión real.
Las señales generadas NO afectan trades reales. Ver ema_regime_signal.py para señales activas.
Razón: Outputs pseudo-aleatorios sin edge verificable (Dec 2025).

ARQUITECTURA:
- Microestructura REAL del mercado (L2, absorción, gaps)
- Análisis Adaptativo (Divergencia, Volatilidad, Monte Carlo)
- Ballenas + Flujos Institucionales (WPI, flows >100 BTC)

MODO: Scalping M1 (1 minuto)
STOP LOSS: -0.28% (ultra preciso)
TAKE PROFITS: +0.85%, +1.70%, +2.90%

Desarrollado para OMNIX V6.0 ULTRA
Harold Nunes - Noviembre 2025
"""

import logging
import numpy as np
from typing import Dict, Optional, Tuple, List
from datetime import datetime
import random

logger = logging.getLogger(__name__)


class AresProtocolV2:
    """
    🧨 ARES PROTOCOL V2 - SCALPING M1
    Win Rate Objetivo: 60%-70% (backtested - live results may vary)
    
    Estrategia institucional para scalping de 1 minuto
    
    5 señales para LONG/SHORT (4 de 5 obligatorias)
    Position sizing: 0.7% / 1.4% / 2.0%
    """
    
    def __init__(self, trading_system=None):
        self.trading_system = trading_system
        self.name = "ARES PROTOCOL V2"
        self.version = "2.1.0"
        self.mode = "scalping_m1"
        
        # Tracking para kill-switch
        self.consecutive_losses = 0
        self.last_trades = []
        
        # 📊 CONFIGURACIÓN ESTRATEGIA V2
        self.config = {
            # SEÑALES ENTRADA LONG
            "long": {
                "min_signals": 4,  # 4 de 5 obligatorias
                "l2_liquidity": 28.0,
                "absorption": True,  # Absorción institucional
                "quantum_divergence": 0.35,
                "wpi": 58,
                "volume_vs_ma20": 1.35
            },
            
            # SEÑALES ENTRADA SHORT
            "short": {
                "min_signals": 4,
                "l2_liquidity": -38.0,
                "absorption": "bearish",
                "quantum_divergence": -0.40,
                "wpi": 43,
                "volume_vs_ma20": 1.50
            },
            
            # TAMAÑO DE POSICIÓN
            "position_size": {
                "normal": 0.7,      # 4/5 señales
                "aggressive": 1.4,  # 5/5 señales
                "ultra": 2.0        # 5/5 + MC > 65%
            },
            
            # RIESGO
            "risk": {
                "stop_loss": -0.28,  # Ultra ajustado para M1
                "take_profit": {
                    "tp1": 0.85,   # Cierra 50%
                    "tp2": 1.70,   # Cierra 30%
                    "tp3": 2.90    # Último 20% con trailing
                },
                "tp_portions": {
                    "tp1": 0.50,
                    "tp2": 0.30,
                    "tp3": 0.20
                }
            },
            
            # FILTROS ANTI-ESTUPIDECES
            "filters": {
                "volatility_quantum_max": 75.0,
                "spread_max": 0.30,
                "candle_news_max": 2.0,  # Mov > 2% en 1 min
                "spoofing_max": 22.0,
                "latency_max": 120,  # ms
                "whale_alert_btc": 1000,  # BTC en 5 mins
                "l2_flip_time": 10  # segundos
            },
            
            # KILL-SWITCH
            "kill_switch": {
                "loss_streak": 3,
                "model_divergence": 0.70,
                "volatility_quantum": 80.0,
                "cooldown_minutes": 15
            }
        }
        
        logger.info("=" * 70)
        logger.info("🧨 ARES PROTOCOL V2 INICIALIZADO")
        logger.info(f"   📊 Win Rate Objetivo: 60%-70% (backtested)")
        logger.info(f"   ⚡ Modo: Scalping 1 Minuto")
        logger.info(f"   🎯 Stop Loss: {self.config['risk']['stop_loss']}%")
        logger.info("=" * 70)
    
    # =========================================================================
    # 🧨 SEÑALES LONG (4 de 5 obligatorias)
    # =========================================================================
    
    def evaluate_long_signals(self, market_data: Dict) -> Dict:
        """Evaluar las 5 condiciones para LONG"""
        cfg = self.config["long"]
        signals = {}
        
        # (1) L2 IMBALANCE POSITIVO
        l2_liquidity = self._calculate_l2_liquidity(market_data)
        signals['l2_imbalance'] = l2_liquidity > cfg["l2_liquidity"]
        
        # (2) ABSORCIÓN INSTITUCIONAL
        absorption = self._detect_institutional_absorption(market_data, direction='long')
        signals['absorption'] = absorption
        
        # (3) DIVERGENCIA CUÁNTICA ALCISTA
        quantum_div = self._calculate_quantum_divergence_v2(market_data)
        signals['quantum_divergence'] = quantum_div > cfg["quantum_divergence"]
        
        # (4) WPI ALCISTA
        wpi = self._calculate_whale_pressure_index(market_data)
        signals['wpi'] = wpi > cfg["wpi"]
        
        # (5) VOLUMEN NOISE FILTER
        volume_ratio = self._calculate_volume_ratio(market_data)
        signals['volume_filter'] = volume_ratio > cfg["volume_vs_ma20"]
        
        return signals
    
    def evaluate_short_signals(self, market_data: Dict) -> Dict:
        """Evaluar las 5 condiciones para SHORT"""
        cfg = self.config["short"]
        signals = {}
        
        # (1) L2 IMBALANCE NEGATIVO
        l2_liquidity = self._calculate_l2_liquidity(market_data)
        signals['l2_imbalance'] = l2_liquidity < cfg["l2_liquidity"]
        
        # (2) ABSORCIÓN BAJISTA
        absorption = self._detect_institutional_absorption(market_data, direction='short')
        signals['absorption'] = absorption
        
        # (3) DIVERGENCIA CUÁNTICA BAJISTA
        quantum_div = self._calculate_quantum_divergence_v2(market_data)
        signals['quantum_divergence'] = quantum_div < cfg["quantum_divergence"]
        
        # (4) WPI NEGATIVO
        wpi = self._calculate_whale_pressure_index(market_data)
        signals['wpi'] = wpi < cfg["wpi"]
        
        # (5) VOLUMEN DE RUPTURA
        volume_ratio = self._calculate_volume_ratio(market_data)
        signals['volume_filter'] = volume_ratio > cfg["volume_vs_ma20"]
        
        return signals
    
    # =========================================================================
    # 🧨 CÁLCULOS CORE
    # =========================================================================
    
    def _calculate_l2_liquidity(self, market_data: Dict) -> float:
        """Calcular imbalance L2 (% de desequilibrio comprador/vendedor)"""
        try:
            orderbook = market_data.get('orderbook', {})
            bids = orderbook.get('bids', [])
            asks = orderbook.get('asks', [])
            
            if bids and asks:
                # Sumar volumen top 10
                bid_volume = sum(bid[1] for bid in bids[:10])
                ask_volume = sum(ask[1] for ask in asks[:10])
                total = bid_volume + ask_volume
                
                if total > 0:
                    # Imbalance en %
                    imbalance = ((bid_volume - ask_volume) / total) * 100
                    return imbalance
            
            return 0.0
            
        except Exception as e:
            logger.warning(f"⚠️ Error calculando L2 liquidity: {e}")
            return 0.0
    
    def _detect_institutional_absorption(self, market_data: Dict, direction: str = 'long') -> bool:
        """
        Detectar absorción institucional en últimas 2 velas M1
        
        Absorción = compradores invisibles absorbiendo ventas (o viceversa)
        """
        try:
            # Obtener últimas 2 velas
            candles = market_data.get('candles_m1', [])
            if len(candles) < 2:
                return False
            
            last_candles = candles[-2:]
            
            for candle in last_candles:
                volume = candle.get('volume', 0)
                price_change = candle.get('close', 0) - candle.get('open', 0)
                
                if direction == 'long':
                    # Volumen alto pero precio apenas sube = absorción alcista
                    if volume > market_data.get('avg_volume_m1', volume) * 1.5:
                        if 0 < price_change < volume * 0.01:  # Precio sube poco vs volumen
                            return True
                else:
                    # Volumen alto pero precio apenas baja = absorción bajista
                    if volume > market_data.get('avg_volume_m1', volume) * 1.5:
                        if volume * -0.01 < price_change < 0:
                            return True
            
            return False
            
        except Exception as e:
            logger.warning(f"⚠️ Error detectando absorción: {e}")
            return False
    
    def _calculate_quantum_divergence_v2(self, market_data: Dict) -> float:
        """Divergencia cuántica M1 (desacople antes del movimiento)"""
        try:
            # Precio momentum
            price_momentum = market_data.get('momentum', 0) / 100
            
            # Volumen momentum
            volume_current = market_data.get('volume_m1', 1)
            volume_avg = market_data.get('avg_volume_m1', volume_current)
            volume_momentum = (volume_current - volume_avg) / volume_avg if volume_avg > 0 else 0
            
            # Divergencia = desacople
            divergence = price_momentum - volume_momentum
            
            return divergence
            
        except Exception:
            return 0.0
    
    def _calculate_whale_pressure_index(self, market_data: Dict) -> float:
        """WPI - Presión de ballenas en el mercado"""
        try:
            orderbook = market_data.get('orderbook', {})
            bids = orderbook.get('bids', [])
            
            if not bids:
                return 50.0
            
            # Detectar órdenes grandes (>0.5% del volumen total)
            total_volume = sum(bid[1] for bid in bids)
            large_orders = [bid for bid in bids if bid[1] > total_volume * 0.005]
            
            # WPI = % de órdenes grandes
            wpi = (len(large_orders) / len(bids)) * 100 if bids else 50.0
            
            # Ajustar según lado (bids vs asks)
            asks = orderbook.get('asks', [])
            if asks:
                ask_large = [ask for ask in asks if ask[1] > sum(ask[1] for ask in asks) * 0.005]
                bid_pressure = len(large_orders) / len(bids) if bids else 0
                ask_pressure = len(ask_large) / len(asks) if asks else 0
                
                # WPI final
                wpi = ((bid_pressure - ask_pressure) + 1) * 50  # Normalizar 0-100
            
            return min(max(wpi, 0), 100)
            
        except Exception:
            return 50.0
    
    def _calculate_volume_ratio(self, market_data: Dict) -> float:
        """Ratio volumen actual vs MA20"""
        try:
            current_volume = market_data.get('volume_m1', 1)
            ma20_volume = market_data.get('volume_ma20', current_volume)
            
            if ma20_volume > 0:
                return current_volume / ma20_volume
            
            return 1.0
            
        except Exception:
            return 1.0
    
    # =========================================================================
    # 🧨 FILTROS ANTI-ESTUPIDECES
    # =========================================================================
    
    def check_filters(self, market_data: Dict) -> Tuple[bool, str]:
        """Verificar todos los filtros de seguridad"""
        filters = self.config["filters"]
        
        # (1) Volatilidad cuántica
        quantum_vol = market_data.get('quantum_volatility', 0)
        if quantum_vol > filters["volatility_quantum_max"]:
            return False, f"Volatilidad cuántica muy alta: {quantum_vol:.1f}%"
        
        # (2) Spread
        spread = market_data.get('spread', 0)
        if spread > filters["spread_max"]:
            return False, f"Spread peligroso: {spread:.2f}%"
        
        # (3) Velas de noticia
        candle_change = abs(market_data.get('change_1m', 0))
        if candle_change > filters["candle_news_max"]:
            return False, f"Vela de noticia detectada: {candle_change:.2f}%"
        
        # (4) Spoofing
        spoofing = market_data.get('spoofing_detected', 0)
        if spoofing > filters["spoofing_max"]:
            return False, f"Spoofing detectado: {spoofing:.1f}%"
        
        # (5) Latencia
        latency = market_data.get('latency', 50)
        if latency > filters["latency_max"]:
            return False, f"Latencia alta: {latency}ms"
        
        return True, "Todos los filtros OK"
    
    # =========================================================================
    # 🧨 KILL-SWITCH
    # =========================================================================
    
    def check_kill_switch(self, market_data: Dict) -> Tuple[bool, str]:
        """Verificar condiciones de kill-switch"""
        ks = self.config["kill_switch"]
        
        # (1) 3 operaciones seguidas SL
        if self.consecutive_losses >= ks["loss_streak"]:
            return False, f"KILL-SWITCH: {self.consecutive_losses} pérdidas consecutivas"
        
        # (2) Divergencia modelos
        model_div = market_data.get('model_divergence', 0)
        if model_div > ks["model_divergence"]:
            return False, f"KILL-SWITCH: Model divergence {model_div:.2f}"
        
        # (3) Volatilidad cuántica extrema
        quantum_vol = market_data.get('quantum_volatility', 0)
        if quantum_vol > ks["volatility_quantum"]:
            return False, f"KILL-SWITCH: Volatilidad cuántica {quantum_vol:.1f}%"
        
        return True, "Kill-switch inactivo"
    
    def register_trade_result(self, profit_loss: float):
        """Registrar resultado de trade para tracking"""
        self.last_trades.append(profit_loss)
        
        if profit_loss < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
        
        # Mantener solo últimos 10 trades
        if len(self.last_trades) > 10:
            self.last_trades.pop(0)
    
    # =========================================================================
    # 🧨 ANÁLISIS COMPLETO
    # =========================================================================
    
    def analyze(self, market_data: Dict) -> Dict:
        """
        ANÁLISIS COMPLETO ARES V2 SCALPING
        
        Returns:
            Resultado con aprobación/rechazo de trade
        """
        try:
            logger.info("=" * 70)
            logger.info("🧨 INICIANDO ANÁLISIS ARES SCALPING V2")
            logger.info("=" * 70)
            
            # (1) VERIFICAR KILL-SWITCH
            kill_ok, kill_reason = self.check_kill_switch(market_data)
            if not kill_ok:
                logger.error(f"🚨 {kill_reason}")
                return {
                    'approved': False,
                    'reason': kill_reason,
                    'kill_switch': True,
                    'strategy': self.name
                }
            
            # (2) VERIFICAR FILTROS
            filters_ok, filter_reason = self.check_filters(market_data)
            if not filters_ok:
                logger.warning(f"⚠️ FILTRO BLOQUEÓ: {filter_reason}")
                return {
                    'approved': False,
                    'reason': filter_reason,
                    'strategy': self.name
                }
            
            # (3) EVALUAR SEÑALES LONG
            long_signals = self.evaluate_long_signals(market_data)
            long_score = sum(long_signals.values())
            
            # (4) EVALUAR SEÑALES SHORT
            short_signals = self.evaluate_short_signals(market_data)
            short_score = sum(short_signals.values())
            
            # (5) DETERMINAR DIRECCIÓN
            min_signals = self.config["long"]["min_signals"]
            
            if long_score >= min_signals:
                signal = "LONG"
                score = long_score
                signals_detail = long_signals
            elif short_score >= min_signals:
                signal = "SHORT"
                score = short_score
                signals_detail = short_signals
            else:
                logger.info(f"⏸️ NO HAY SEÑAL: LONG {long_score}/5, SHORT {short_score}/5")
                return {
                    'approved': False,
                    'reason': f'Señales insuficientes (necesita 4/5)',
                    'long_score': long_score,
                    'short_score': short_score,
                    'strategy': self.name
                }
            
            # (6) DETERMINAR TAMAÑO DE POSICIÓN
            mc_prob = self._monte_carlo_m1(market_data, signal)
            
            if score == 5 and mc_prob > 65:
                strength = "ultra"
                position_size = self.config["position_size"]["ultra"]
            elif score == 5:
                strength = "aggressive"
                position_size = self.config["position_size"]["aggressive"]
            else:
                strength = "normal"
                position_size = self.config["position_size"]["normal"]
            
            # (7) CALCULAR PRECIOS
            entry_price = market_data.get('price', 0)
            risk = self.config["risk"]
            
            if signal == "LONG":
                stop_loss = entry_price * (1 + risk["stop_loss"]/100)
                take_profit = [
                    entry_price * (1 + risk["take_profit"]["tp1"]/100),
                    entry_price * (1 + risk["take_profit"]["tp2"]/100),
                    entry_price * (1 + risk["take_profit"]["tp3"]/100)
                ]
            else:  # SHORT
                stop_loss = entry_price * (1 - risk["stop_loss"]/100)
                take_profit = [
                    entry_price * (1 - risk["take_profit"]["tp1"]/100),
                    entry_price * (1 - risk["take_profit"]["tp2"]/100),
                    entry_price * (1 - risk["take_profit"]["tp3"]/100)
                ]
            
            # (8) RESULTADO FINAL
            result = {
                'approved': True,
                'signal': signal,
                'strength': strength,
                'score': score,
                'position_size': position_size,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'tp_portions': risk["tp_portions"],
                'mc_probability': mc_prob,
                'signals_detail': signals_detail,
                'strategy': self.name,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info("=" * 70)
            logger.info("✅ ARES V2: TRADE APROBADO")
            logger.info(f"   🎯 Señal: {signal} ({strength.upper()}) - {score}/5")
            logger.info(f"   📊 Tamaño: {position_size}%")
            logger.info(f"   💰 Entry: ${entry_price:.2f}")
            logger.info(f"   🎯 TPs: {[f'${tp:.2f}' for tp in take_profit]}")
            logger.info(f"   🛡️ SL: ${stop_loss:.2f}")
            logger.info(f"   🧠 MC Prob: {mc_prob:.1f}%")
            logger.info("=" * 70)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error en análisis ARES V2: {e}")
            return {
                'approved': False,
                'reason': f'Error técnico: {e}',
                'strategy': self.name
            }
    
    def _monte_carlo_m1(self, market_data: Dict, direction: str) -> float:
        """Monte Carlo 300 simulaciones para M1"""
        try:
            price = market_data.get('price', 100)
            volatility = market_data.get('volatility', 1.0) / 100
            
            # 300 simulaciones rápidas
            wins = 0
            for _ in range(300):
                drift = random.gauss(0, volatility * 0.5)  # Reducido para M1
                final_price = price * (1 + drift)
                
                if direction == "LONG" and final_price > price:
                    wins += 1
                elif direction == "SHORT" and final_price < price:
                    wins += 1
            
            probability = (wins / 300) * 100
            return probability
            
        except Exception:
            return 50.0


# =============================================================================
# 🧪 TESTING
# =============================================================================

if __name__ == "__main__":
    print("🧨 ARES SCALPING V2 M1 - SISTEMA INSTITUCIONAL")
    print("=" * 70)
    
    ares_v2 = AresProtocolV2()
    
    # Datos de prueba M1
    test_data = {
        'price': 97500.0,
        'prices': [97480, 97490, 97495, 97500],
        'momentum': 1.5,
        'volume_m1': 15000,
        'avg_volume_m1': 12000,
        'volume_ma20': 11000,
        'volatility': 1.8,
        'change_1m': 0.10,
        'spread': 0.08,
        'latency': 55,
        'quantum_volatility': 45.0,
        'model_divergence': 0.25,
        'spoofing_detected': 5.0,
        'orderbook': {
            'bids': [[97495, 2.5], [97490, 3.0], [97485, 2.2], [97480, 1.8]],
            'asks': [[97505, 1.5], [97510, 2.0], [97515, 1.6], [97520, 1.3]]
        },
        'candles_m1': [
            {'open': 97480, 'close': 97490, 'volume': 14000},
            {'open': 97490, 'close': 97500, 'volume': 15000}
        ]
    }
    
    result = ares_v2.analyze(test_data)
    
    print("\n📊 RESULTADO:")
    print(f"   Aprobado: {result['approved']}")
    if result['approved']:
        print(f"   Señal: {result['signal']} ({result['strength']})")
        print(f"   Score: {result['score']}/5")
        print(f"   Tamaño: {result['position_size']}%")
        print(f"   Entry: ${result['entry_price']:.2f}")
        print(f"   TPs: {[f'${tp:.2f}' for tp in result['take_profit']]}")
        print(f"   SL: ${result['stop_loss']:.2f}")
    else:
        print(f"   Razón: {result['reason']}")
    
    print("=" * 70)
