"""
🚀 STOCK STRATEGY ENGINE V6.2 PREMIUM
Orquestador principal para estrategias avanzadas de acciones
Nivel institucional - Paridad con módulo crypto

Arquitectura:
MarketDataAdapter → RegimeDetector (HMM) → SignalEngines (ARES, MonteCarlo, Kalman) 
→ MemoryKernel (NonMarkovian) → DecisionGovernor (Coherence) → RiskGuardianBridge
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    BULL = "bull"
    BEAR = "bear"
    SIDEWAYS = "sideways"
    CRISIS = "crisis"
    UNKNOWN = "unknown"


class SignalType(Enum):
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


@dataclass
class StockSignal:
    symbol: str
    signal_type: SignalType
    confidence: float
    regime: MarketRegime
    sources: Dict[str, float]
    fundamental_score: float
    technical_score: float
    memory_coherence: float
    risk_approved: bool
    veto_reasons: List[str]
    timestamp: datetime
    
    def to_dict(self) -> Dict:
        return {
            'symbol': self.symbol,
            'signal': self.signal_type.value,
            'confidence': round(self.confidence, 2),
            'regime': self.regime.value,
            'sources': self.sources,
            'fundamental_score': round(self.fundamental_score, 2),
            'technical_score': round(self.technical_score, 2),
            'memory_coherence': round(self.memory_coherence, 2),
            'risk_approved': self.risk_approved,
            'veto_reasons': self.veto_reasons,
            'timestamp': self.timestamp.isoformat()
        }


class StockStrategyEngine:
    """
    Motor de estrategias premium para acciones - Nivel institucional
    
    Características:
    - Monte Carlo Simulations (2000 paths)
    - Dual Kalman Filter (adaptado para volatilidad diaria)
    - HMM Regime Detection (4 estados: bull/bear/sideways/crisis)
    - ARES-STOCK V1/V2 (parámetros ajustados para menor volatilidad)
    - Non-Markovian Memory Kernel (patrones de mercado tradicional)
    - Coherence Engine Integration (6-tier veto)
    - AI Risk Guardian (umbrales específicos para acciones)
    """
    
    STOCK_PARAMS = {
        'lookback_period': 120,
        'volatility_floor': 0.006,
        'max_leverage': 2.0,
        'monte_carlo_paths': 2000,
        'kalman_process_noise': 0.001,
        'hmm_states': 4,
        'memory_decay_days': 60,
        'max_drawdown_daily': 0.03,
        'max_drawdown_swing': 0.08,
        'confidence_threshold': 0.65,
        'veto_threshold': 0.4,
    }
    
    def __init__(
        self,
        stock_analyzer=None,
        fundamental_analyzer=None,
        alpaca_service=None,
        market_hours=None,
        coherence_engine=None,
        risk_guardian=None,
        database_service=None
    ):
        self.stock_analyzer = stock_analyzer
        self.fundamental_analyzer = fundamental_analyzer
        self.alpaca_service = alpaca_service
        self.market_hours = market_hours
        self.coherence_engine = coherence_engine
        self.risk_guardian = risk_guardian
        self.database_service = database_service
        
        self.monte_carlo = None
        self.kalman_filter = None
        self.hmm_detector = None
        self.ares_stock = None
        self.memory_kernel = None
        
        self._init_modules()
        
        logger.info("🚀 Stock Strategy Engine V6.2 PREMIUM inicializado")
        logger.info(f"   📊 Lookback: {self.STOCK_PARAMS['lookback_period']} barras")
        logger.info(f"   🎲 Monte Carlo: {self.STOCK_PARAMS['monte_carlo_paths']} paths")
        logger.info(f"   🧠 HMM Estados: {self.STOCK_PARAMS['hmm_states']}")
        logger.info(f"   💾 Memory Decay: {self.STOCK_PARAMS['memory_decay_days']} días")
    
    def _init_modules(self):
        """Inicializar módulos premium"""
        try:
            from .modules.monte_carlo import StockMonteCarlo
            self.monte_carlo = StockMonteCarlo(
                n_paths=self.STOCK_PARAMS['monte_carlo_paths'],
                volatility_floor=self.STOCK_PARAMS['volatility_floor']
            )
            logger.info("   ✅ Monte Carlo inicializado")
        except Exception as e:
            logger.warning(f"   ⚠️ Monte Carlo no disponible: {e}")
        
        try:
            from .modules.kalman_filter import StockKalmanFilter
            self.kalman_filter = StockKalmanFilter(
                process_noise=self.STOCK_PARAMS['kalman_process_noise']
            )
            logger.info("   ✅ Kalman Filter inicializado")
        except Exception as e:
            logger.warning(f"   ⚠️ Kalman Filter no disponible: {e}")
        
        try:
            from .modules.hmm_regime import StockHMMRegime
            self.hmm_detector = StockHMMRegime(
                n_states=self.STOCK_PARAMS['hmm_states']
            )
            logger.info("   ✅ HMM Regime Detector inicializado")
        except Exception as e:
            logger.warning(f"   ⚠️ HMM Regime Detector no disponible: {e}")
        
        try:
            from .modules.ares_stock import ARESStock
            self.ares_stock = ARESStock(
                volatility_floor=self.STOCK_PARAMS['volatility_floor'],
                max_leverage=self.STOCK_PARAMS['max_leverage']
            )
            logger.info("   ✅ ARES-STOCK inicializado")
        except Exception as e:
            logger.warning(f"   ⚠️ ARES-STOCK no disponible: {e}")
        
        try:
            from .modules.non_markovian_memory import StockMemoryKernel
            self.memory_kernel = StockMemoryKernel(
                decay_days=self.STOCK_PARAMS['memory_decay_days']
            )
            logger.info("   ✅ Non-Markovian Memory Kernel inicializado")
        except Exception as e:
            logger.warning(f"   ⚠️ Non-Markovian Memory Kernel no disponible: {e}")
    
    def analyze(self, symbol: str, include_fundamental: bool = True) -> Optional[StockSignal]:
        """
        Análisis completo de una acción con todas las estrategias premium
        
        Args:
            symbol: Símbolo de la acción (ej: AAPL, MSFT)
            include_fundamental: Incluir análisis fundamental
            
        Returns:
            StockSignal con señal consolidada y metadatos
        """
        try:
            logger.info(f"📊 Analizando {symbol} con estrategias premium...")
            
            if not self._check_market_hours():
                logger.info(f"⏰ Mercado cerrado - análisis en modo offline")
            
            prices = self._get_price_data(symbol)
            if not prices or len(prices) < self.STOCK_PARAMS['lookback_period']:
                logger.warning(f"⚠️ Datos insuficientes para {symbol}")
                return None
            
            regime = self._detect_regime(prices)
            logger.info(f"   🎯 Régimen detectado: {regime.value}")
            
            signals = {}
            
            if self.monte_carlo:
                mc_signal = self.monte_carlo.analyze(prices)
                if mc_signal:
                    signals['monte_carlo'] = mc_signal
                    logger.info(f"   🎲 Monte Carlo: {mc_signal:.2f}")
            
            if self.kalman_filter:
                kf_signal = self.kalman_filter.analyze(prices)
                if kf_signal:
                    signals['kalman'] = kf_signal
                    logger.info(f"   📈 Kalman Filter: {kf_signal:.2f}")
            
            if self.ares_stock:
                ares_signal = self.ares_stock.analyze(prices, regime)
                if ares_signal:
                    signals['ares'] = ares_signal
                    logger.info(f"   🧬 ARES-STOCK: {ares_signal:.2f}")
            
            if self.stock_analyzer:
                closes = [p['close'] for p in prices]
                rsi = self.stock_analyzer.calculate_rsi(closes)
                macd = self.stock_analyzer.calculate_macd(closes)
                if rsi:
                    rsi_signal = (50 - rsi) / 50
                    signals['rsi'] = rsi_signal
                if macd:
                    macd_signal = np.tanh(macd['histogram'] * 10)
                    signals['macd'] = macd_signal
            
            fundamental_score = 0.5
            if include_fundamental and self.fundamental_analyzer:
                fund_analysis = self.fundamental_analyzer.analyze_fundamentals(symbol)
                if fund_analysis:
                    fundamental_score = fund_analysis.get('score', 50) / 100
                    logger.info(f"   📈 Fundamental Score: {fundamental_score:.2f}")
            
            memory_coherence = 0.5
            if self.memory_kernel:
                memory_coherence = self.memory_kernel.get_coherence(symbol, prices)
                logger.info(f"   🧠 Memory Coherence: {memory_coherence:.2f}")
            
            technical_score = np.mean(list(signals.values())) if signals else 0
            
            combined_signal = self._combine_signals(
                signals, 
                fundamental_score, 
                memory_coherence,
                regime
            )
            
            signal_type = self._classify_signal(combined_signal)
            confidence = abs(combined_signal)
            
            risk_approved = True
            veto_reasons = []
            
            if self.coherence_engine:
                coherence_result = self._check_coherence(signals, regime)
                if not coherence_result['approved']:
                    veto_reasons.extend(coherence_result['reasons'])
                    if coherence_result['severity'] >= self.STOCK_PARAMS['veto_threshold']:
                        risk_approved = False
            
            if self.risk_guardian:
                risk_result = self._check_risk(symbol, signal_type, confidence)
                if not risk_result['approved']:
                    veto_reasons.extend(risk_result['reasons'])
                    risk_approved = False
            
            stock_signal = StockSignal(
                symbol=symbol,
                signal_type=signal_type,
                confidence=confidence,
                regime=regime,
                sources=signals,
                fundamental_score=fundamental_score,
                technical_score=technical_score,
                memory_coherence=memory_coherence,
                risk_approved=risk_approved,
                veto_reasons=veto_reasons,
                timestamp=datetime.now()
            )
            
            logger.info(f"✅ Análisis completado: {signal_type.value} (conf: {confidence:.2f})")
            if veto_reasons:
                logger.info(f"   ⚠️ Vetos: {', '.join(veto_reasons)}")
            
            return stock_signal
            
        except Exception as e:
            logger.error(f"❌ Error analizando {symbol}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _get_price_data(self, symbol: str) -> Optional[List[Dict]]:
        """Obtener datos de precios históricos"""
        if self.stock_analyzer:
            return self.stock_analyzer.fetch_historical_data(
                symbol, 
                interval='daily',
                outputsize='full'
            )
        return None
    
    def _detect_regime(self, prices: List[Dict]) -> MarketRegime:
        """Detectar régimen de mercado con HMM"""
        if self.hmm_detector:
            try:
                return self.hmm_detector.detect(prices)
            except:
                pass
        
        if len(prices) < 20:
            return MarketRegime.UNKNOWN
        
        closes = [p['close'] for p in prices[-60:]]
        returns = np.diff(closes) / closes[:-1]
        
        avg_return = np.mean(returns)
        volatility = np.std(returns)
        
        if volatility > 0.03:
            return MarketRegime.CRISIS
        elif avg_return > 0.001:
            return MarketRegime.BULL
        elif avg_return < -0.001:
            return MarketRegime.BEAR
        else:
            return MarketRegime.SIDEWAYS
    
    def _combine_signals(
        self, 
        signals: Dict[str, float],
        fundamental_score: float,
        memory_coherence: float,
        regime: MarketRegime
    ) -> float:
        """Combinar señales con pesos adaptativos según régimen"""
        if not signals:
            return 0
        
        weights = {
            'monte_carlo': 0.20,
            'kalman': 0.20,
            'ares': 0.25,
            'rsi': 0.10,
            'macd': 0.10,
            'fundamental': 0.15
        }
        
        if regime == MarketRegime.CRISIS:
            weights['monte_carlo'] = 0.30
            weights['ares'] = 0.15
        elif regime == MarketRegime.SIDEWAYS:
            weights['rsi'] = 0.20
            weights['macd'] = 0.15
        
        weighted_sum = 0
        total_weight = 0
        
        for source, signal in signals.items():
            weight = weights.get(source, 0.1)
            weighted_sum += signal * weight
            total_weight += weight
        
        weighted_sum += fundamental_score * weights['fundamental']
        total_weight += weights['fundamental']
        
        base_signal = weighted_sum / total_weight if total_weight > 0 else 0
        
        coherence_factor = 0.5 + (memory_coherence * 0.5)
        final_signal = base_signal * coherence_factor
        
        return np.clip(final_signal, -1, 1)
    
    def _classify_signal(self, combined_signal: float) -> SignalType:
        """Clasificar señal combinada"""
        if combined_signal > 0.6:
            return SignalType.STRONG_BUY
        elif combined_signal > 0.2:
            return SignalType.BUY
        elif combined_signal < -0.6:
            return SignalType.STRONG_SELL
        elif combined_signal < -0.2:
            return SignalType.SELL
        else:
            return SignalType.HOLD
    
    def _check_market_hours(self) -> bool:
        """Verificar si el mercado está abierto"""
        if self.market_hours:
            return self.market_hours.is_market_open()
        
        now = datetime.now()
        if now.weekday() >= 5:
            return False
        hour = now.hour
        return 14 <= hour <= 21
    
    def _check_coherence(self, signals: Dict[str, float], regime: MarketRegime) -> Dict:
        """Verificar coherencia entre señales"""
        if not signals or len(signals) < 2:
            return {'approved': True, 'reasons': [], 'severity': 0}
        
        values = list(signals.values())
        signs = [1 if v > 0 else -1 for v in values if abs(v) > 0.1]
        
        if not signs:
            return {'approved': True, 'reasons': [], 'severity': 0}
        
        agreement = abs(sum(signs)) / len(signs)
        
        reasons = []
        severity = 0
        
        if agreement < 0.5:
            reasons.append(f"Señales contradictorias ({agreement:.0%} acuerdo)")
            severity = 0.3
        
        if regime == MarketRegime.CRISIS:
            if np.mean(values) > 0.3:
                reasons.append("Señal bullish en régimen de crisis")
                severity = max(severity, 0.5)
        
        return {
            'approved': severity < self.STOCK_PARAMS['veto_threshold'],
            'reasons': reasons,
            'severity': severity
        }
    
    def _check_risk(self, symbol: str, signal_type: SignalType, confidence: float) -> Dict:
        """Verificar con Risk Guardian"""
        reasons = []
        approved = True
        
        if confidence < self.STOCK_PARAMS['confidence_threshold']:
            if signal_type in [SignalType.STRONG_BUY, SignalType.STRONG_SELL]:
                reasons.append(f"Confianza baja ({confidence:.0%}) para señal fuerte")
                approved = False
        
        return {'approved': approved, 'reasons': reasons}
    
    def get_portfolio_analysis(self, symbols: List[str]) -> Dict:
        """Analizar múltiples acciones para portfolio"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'symbols_analyzed': 0,
            'signals': {},
            'strong_buys': [],
            'strong_sells': [],
            'holds': [],
            'summary': {}
        }
        
        for symbol in symbols:
            signal = self.analyze(symbol)
            if signal:
                results['symbols_analyzed'] += 1
                results['signals'][symbol] = signal.to_dict()
                
                if signal.signal_type == SignalType.STRONG_BUY and signal.risk_approved:
                    results['strong_buys'].append(symbol)
                elif signal.signal_type == SignalType.STRONG_SELL and signal.risk_approved:
                    results['strong_sells'].append(symbol)
                else:
                    results['holds'].append(symbol)
        
        results['summary'] = {
            'total': results['symbols_analyzed'],
            'strong_buys': len(results['strong_buys']),
            'strong_sells': len(results['strong_sells']),
            'holds': len(results['holds'])
        }
        
        return results
    
    def get_status(self) -> Dict:
        """Obtener estado del motor"""
        return {
            'engine': 'Stock Strategy Engine V6.2 PREMIUM',
            'modules': {
                'monte_carlo': self.monte_carlo is not None,
                'kalman_filter': self.kalman_filter is not None,
                'hmm_detector': self.hmm_detector is not None,
                'ares_stock': self.ares_stock is not None,
                'memory_kernel': self.memory_kernel is not None,
                'coherence_engine': self.coherence_engine is not None,
                'risk_guardian': self.risk_guardian is not None
            },
            'parameters': self.STOCK_PARAMS,
            'market_open': self._check_market_hours()
        }
