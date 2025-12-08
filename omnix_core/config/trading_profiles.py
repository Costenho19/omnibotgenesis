"""
OMNIX - Trading Profiles System
===============================

Sistema de perfiles de trading que permite cambiar fácilmente entre 
configuraciones conservadoras y más agresivas sin modificar el código.

USO:
    En Railway o .env, establecer:
    TRADING_PROFILE=INSTITUTIONAL     # Conservador (original)
    TRADING_PROFILE=PAPER_AGGRESSIVE  # Más trades para paper trading
    TRADING_PROFILE=BALANCED          # Término medio

CAMBIAR PERFIL:
    1. En Railway: Settings → Variables → TRADING_PROFILE
    2. Reiniciar el servicio
    3. El bot usará el nuevo perfil automáticamente

VOLVER AL ORIGINAL:
    TRADING_PROFILE=INSTITUTIONAL

Creado: Dec 4, 2025
Autor: OMNIX Development Team
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ProfileName(Enum):
    """Nombres de perfiles disponibles"""
    INSTITUTIONAL = "INSTITUTIONAL"
    PAPER_AGGRESSIVE = "PAPER_AGGRESSIVE"
    BALANCED = "BALANCED"
    PAPER_OPTIMIZED = "PAPER_OPTIMIZED"
    WIN_RATE_OPTIMIZED = "WIN_RATE_OPTIMIZED"


class VolatilityClass(Enum):
    """Clasificación de volatilidad por par"""
    HIGH = "HIGH"
    NORMAL = "NORMAL"


class CalibrationTier(Enum):
    """Tier de calibración basado en datos históricos"""
    PROVEN = "PROVEN"           # Historial probado con win rate > 50%
    CALIBRATING = "CALIBRATING" # Pocos datos, requiere protección extra
    EXCLUDED = "EXCLUDED"       # Excluido por mal rendimiento


@dataclass
class PairCalibration:
    """
    Calibración institucional por par de trading.
    
    V6.5.4 PREMIUM - Sistema de calibración cuantitativo basado en:
    - Volatilidad histórica del par
    - Win rate observado
    - Drawdown máximo registrado
    """
    symbol: str
    tier: CalibrationTier
    stop_loss_pct: float
    take_profit_pct: float
    min_confidence: float
    risk_reward_ratio: float
    max_position_pct: float = 0.10
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'tier': self.tier.value,
            'stop_loss_pct': self.stop_loss_pct,
            'take_profit_pct': self.take_profit_pct,
            'min_confidence': self.min_confidence,
            'risk_reward_ratio': self.risk_reward_ratio,
            'max_position_pct': self.max_position_pct,
            'notes': self.notes
        }


# ============================================================================
# CALIBRACIÓN PREMIUM POR PAR - WIN_RATE_OPTIMIZED V2
# ============================================================================
# Basado en análisis de 27 trades históricos (Dec 2025)
# Objetivo: Win Rate 55%+ con R:R mínimo 2.0:1
# ============================================================================

PAIR_CALIBRATIONS: Dict[str, PairCalibration] = {
    # TIER: PROVEN - Historial probado con win rate positivo
    "BTC/USD": PairCalibration(
        symbol="BTC/USD",
        tier=CalibrationTier.PROVEN,
        stop_loss_pct=0.012,      # 1.2%
        take_profit_pct=0.035,    # 3.5%
        min_confidence=0.25,
        risk_reward_ratio=2.92,   # 3.5/1.2 = 2.92
        notes="Win rate 55% histórico. Base sólida del portafolio."
    ),
    "XRP/USD": PairCalibration(
        symbol="XRP/USD",
        tier=CalibrationTier.PROVEN,
        stop_loss_pct=0.012,      # 1.2%
        take_profit_pct=0.035,    # 3.5%
        min_confidence=0.25,
        risk_reward_ratio=2.92,
        notes="Win rate 66% histórico. Mejor rendimiento del set."
    ),
    
    # TIER: CALIBRATING - Pocos datos, SL estricto como protección
    "ADA/USD": PairCalibration(
        symbol="ADA/USD",
        tier=CalibrationTier.CALIBRATING,
        stop_loss_pct=0.009,      # 0.9% - SL estricto
        take_profit_pct=0.020,    # 2.0%
        min_confidence=0.30,      # Mayor exigencia
        risk_reward_ratio=2.22,   # 2.0/0.9 = 2.22
        max_position_pct=0.08,    # Posición reducida
        notes="Solo 2 trades históricos. ADA es lenta y predecible."
    ),
    "LINK/USD": PairCalibration(
        symbol="LINK/USD",
        tier=CalibrationTier.CALIBRATING,
        stop_loss_pct=0.010,      # 1.0%
        take_profit_pct=0.025,    # 2.5%
        min_confidence=0.28,      # Mayor exigencia
        risk_reward_ratio=2.50,   # 2.5/1.0 = 2.50
        max_position_pct=0.08,    # Posición reducida
        notes="Solo 1 trade histórico. Volatilidad moderada."
    ),
    
    # TIER: EXCLUDED - No operar bajo ninguna circunstancia
    "SOL/USD": PairCalibration(
        symbol="SOL/USD",
        tier=CalibrationTier.EXCLUDED,
        stop_loss_pct=0.0,
        take_profit_pct=0.0,
        min_confidence=1.0,
        risk_reward_ratio=0.0,
        notes="EXCLUIDO: 0% win rate, -$1,952 pérdida (93% del total)"
    ),
    "ETH/USD": PairCalibration(
        symbol="ETH/USD",
        tier=CalibrationTier.EXCLUDED,
        stop_loss_pct=0.0,
        take_profit_pct=0.0,
        min_confidence=1.0,
        risk_reward_ratio=0.0,
        notes="EXCLUIDO: 0% win rate, alta volatilidad"
    ),
    "AVAX/USD": PairCalibration(
        symbol="AVAX/USD",
        tier=CalibrationTier.EXCLUDED,
        stop_loss_pct=0.0,
        take_profit_pct=0.0,
        min_confidence=1.0,
        risk_reward_ratio=0.0,
        notes="EXCLUIDO: 0% win rate, segundo peor rendimiento"
    ),
}


KRAKEN_SYMBOL_MAP: Dict[str, str] = {
    "XXBTZUSD": "BTC/USD",
    "XETHZUSD": "ETH/USD",
    "XXRPZUSD": "XRP/USD",
    "XLTCZUSD": "LTC/USD",
    "XXLMZUSD": "XLM/USD",
    "ADAUSD": "ADA/USD",
    "SOLUSD": "SOL/USD",
    "DOTUSD": "DOT/USD",
    "LINKUSD": "LINK/USD",
    "AVAXUSD": "AVAX/USD",
    "ATOMUSD": "ATOM/USD",
    "POLUSD": "POL/USD",
    "BTCUSD": "BTC/USD",
    "ETHUSD": "ETH/USD",
    "XRPUSD": "XRP/USD",
}


def normalize_symbol(symbol: str) -> str:
    """
    Normaliza símbolos de Kraken al formato estándar BASE/QUOTE.
    
    Ejemplos:
        XXBTZUSD -> BTC/USD
        XRPUSD -> XRP/USD
        BTC/USD -> BTC/USD
    """
    upper = symbol.upper().strip()
    
    if upper in KRAKEN_SYMBOL_MAP:
        return KRAKEN_SYMBOL_MAP[upper]
    
    if "/" in upper:
        return upper
    
    if upper.endswith("USD"):
        base = upper[:-3]
        if base.startswith("XX") and base.endswith("Z"):
            base = base[2:-1]
        elif base.startswith("X") and len(base) > 3:
            base = base[1:]
        return f"{base}/USD"
    
    return upper


def get_pair_calibration(symbol: str) -> Optional[PairCalibration]:
    """
    Obtener calibración institucional para un par específico.
    
    V6.5.4 PREMIUM - Retorna parámetros de trading calibrados por par.
    
    Args:
        symbol: Par de trading (ej: BTC/USD, ADA/USD, XXBTZUSD)
    
    Returns:
        PairCalibration o None si el par no está calibrado
    """
    normalized = normalize_symbol(symbol)
    
    calibration = PAIR_CALIBRATIONS.get(normalized)
    if calibration:
        logger.debug(f"📊 Calibración {calibration.tier.value} para {symbol} ({normalized}): "
                    f"SL={calibration.stop_loss_pct*100:.1f}%, "
                    f"TP={calibration.take_profit_pct*100:.1f}%, "
                    f"R:R={calibration.risk_reward_ratio:.2f}")
    return calibration


def is_symbol_allowed(symbol: str, profile: Optional['TradingProfile'] = None) -> bool:
    """
    Verificar si un símbolo está permitido para trading.
    
    V6.5.4 PREMIUM - Usa calibración por par si está disponible.
    
    Args:
        symbol: Par de trading
        profile: Perfil activo (opcional)
    
    Returns:
        True si el símbolo está permitido
    """
    calibration = get_pair_calibration(symbol)
    if calibration:
        allowed = calibration.tier != CalibrationTier.EXCLUDED
        if not allowed:
            logger.warning(f"🚫 {symbol} BLOQUEADO: {calibration.notes}")
        return allowed
    
    if profile is None:
        profile = get_active_profile()
    
    allowed_symbols = profile.extra_params.get('allowed_symbols', [])
    excluded_symbols = profile.extra_params.get('excluded_symbols', [])
    
    normalized = symbol.upper()
    if allowed_symbols:
        return any(s.upper() in normalized or normalized in s.upper() for s in allowed_symbols)
    if excluded_symbols:
        return not any(s.upper() in normalized or normalized in s.upper() for s in excluded_symbols)
    
    return True


PAIR_VOLATILITY_CLASS: Dict[str, VolatilityClass] = {
    "DOT/USD": VolatilityClass.HIGH,
    "DOTUSD": VolatilityClass.HIGH,
    "AVAX/USD": VolatilityClass.HIGH,
    "AVAXUSD": VolatilityClass.HIGH,
    "SOL/USD": VolatilityClass.HIGH,
    "SOLUSD": VolatilityClass.HIGH,
    "LINK/USD": VolatilityClass.HIGH,
    "LINKUSD": VolatilityClass.HIGH,
    "ATOM/USD": VolatilityClass.HIGH,
    "ATOMUSD": VolatilityClass.HIGH,
    "POL/USD": VolatilityClass.HIGH,
    "POLUSD": VolatilityClass.HIGH,
    "BTC/USD": VolatilityClass.NORMAL,
    "BTCUSD": VolatilityClass.NORMAL,
    "XXBTZUSD": VolatilityClass.NORMAL,
    "ETH/USD": VolatilityClass.NORMAL,
    "ETHUSD": VolatilityClass.NORMAL,
    "XETHZUSD": VolatilityClass.NORMAL,
    "XRP/USD": VolatilityClass.NORMAL,
    "XRPUSD": VolatilityClass.NORMAL,
    "LTC/USD": VolatilityClass.NORMAL,
    "LTCUSD": VolatilityClass.NORMAL,
    "ADA/USD": VolatilityClass.NORMAL,
    "ADAUSD": VolatilityClass.NORMAL,
}


def get_volatility_class(symbol: str) -> VolatilityClass:
    """Obtener clasificación de volatilidad para un par"""
    normalized = symbol.upper().replace("/", "")
    for key, value in PAIR_VOLATILITY_CLASS.items():
        if normalized in key.replace("/", ""):
            return value
    return VolatilityClass.NORMAL


def get_sl_tp_for_symbol(symbol: str, profile: Optional['TradingProfile'] = None) -> Dict[str, Any]:
    """
    Obtener stop-loss y take-profit correctos para un símbolo basado en volatilidad.
    
    Args:
        symbol: Par de trading (ej: DOT/USD, BTC/USD)
        profile: Perfil de trading activo (si None, usa el activo)
    
    Returns:
        Dict con 'stop_loss_pct' y 'take_profit_pct'
    """
    if profile is None:
        profile = get_active_profile()
    
    vol_class = get_volatility_class(symbol)
    
    if vol_class == VolatilityClass.HIGH:
        sl = profile.stop_loss_pct_high_vol
        tp = profile.take_profit_pct_high_vol
        logger.debug(f"📊 {symbol} -> HIGH volatility: SL={sl*100:.1f}%, TP={tp*100:.1f}%")
    else:
        sl = profile.stop_loss_pct
        tp = profile.take_profit_pct
        logger.debug(f"📊 {symbol} -> NORMAL volatility: SL={sl*100:.1f}%, TP={tp*100:.1f}%")
    
    return {
        'stop_loss_pct': sl,
        'take_profit_pct': tp,
        'volatility_class': vol_class.value
    }


@dataclass
class TradingProfile:
    """
    Perfil de trading con todos los parámetros configurables.
    
    Cada perfil define umbrales y comportamientos específicos
    para diferentes escenarios de trading.
    """
    name: str
    description: str
    
    min_trade_usd: float = 75.0
    max_position_pct: float = 0.12
    stop_loss_pct: float = 0.02
    stop_loss_pct_high_vol: float = 0.025
    take_profit_pct: float = 0.03
    take_profit_pct_high_vol: float = 0.035
    max_daily_loss_pct: float = 0.08
    min_confidence: float = 0.14
    check_interval_seconds: int = 25
    trades_per_day_target: int = 25
    
    coherence_veto_critical: float = 30.0
    coherence_veto_normal: float = 45.0
    coherence_warning: float = 60.0
    coherence_good: float = 80.0
    
    ramp_up_phase1_factor: float = 0.30
    ramp_up_phase2_factor: float = 0.50
    ramp_up_phase3_factor: float = 0.70
    ramp_up_phase4_factor: float = 0.85
    ramp_up_phase1_trades: int = 5
    ramp_up_phase2_trades: int = 10
    ramp_up_phase3_trades: int = 20
    ramp_up_phase4_trades: int = 50
    
    hmm_veto_enabled: bool = True
    hmm_veto_confidence_threshold: float = 0.85
    
    score_very_strong: int = 20
    score_strong: int = 10
    score_moderate: int = 5
    
    regime_change_veto_enabled: bool = True
    
    extra_params: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir perfil a diccionario para uso en bot"""
        return {
            'name': self.name,
            'description': self.description,
            'min_trade_usd': self.min_trade_usd,
            'max_position_pct': self.max_position_pct,
            'stop_loss_pct': self.stop_loss_pct,
            'take_profit_pct': self.take_profit_pct,
            'max_daily_loss_pct': self.max_daily_loss_pct,
            'min_confidence': self.min_confidence,
            'check_interval_seconds': self.check_interval_seconds,
            'trades_per_day_target': self.trades_per_day_target,
            'coherence': {
                'veto_critical': self.coherence_veto_critical,
                'veto_normal': self.coherence_veto_normal,
                'warning': self.coherence_warning,
                'good': self.coherence_good
            },
            'ramp_up': {
                'phase1': {'factor': self.ramp_up_phase1_factor, 'trades': self.ramp_up_phase1_trades},
                'phase2': {'factor': self.ramp_up_phase2_factor, 'trades': self.ramp_up_phase2_trades},
                'phase3': {'factor': self.ramp_up_phase3_factor, 'trades': self.ramp_up_phase3_trades},
                'phase4': {'factor': self.ramp_up_phase4_factor, 'trades': self.ramp_up_phase4_trades}
            },
            'hmm': {
                'veto_enabled': self.hmm_veto_enabled,
                'veto_confidence_threshold': self.hmm_veto_confidence_threshold
            },
            'score_thresholds': {
                'very_strong': self.score_very_strong,
                'strong': self.score_strong,
                'moderate': self.score_moderate
            },
            'regime_change_veto_enabled': self.regime_change_veto_enabled,
            **self.extra_params
        }


INSTITUTIONAL_PROFILE = TradingProfile(
    name="INSTITUTIONAL",
    description="Perfil conservador original - Prioriza preservar capital. "
                "Diseñado para trading real con fondos reales. "
                "Múltiples capas de protección y vetos estrictos.",
    
    min_trade_usd=75.0,
    max_position_pct=0.12,
    stop_loss_pct=0.02,
    stop_loss_pct_high_vol=0.03,
    take_profit_pct=0.03,
    take_profit_pct_high_vol=0.04,
    max_daily_loss_pct=0.08,
    min_confidence=0.14,
    check_interval_seconds=25,
    trades_per_day_target=25,
    
    coherence_veto_critical=30.0,
    coherence_veto_normal=45.0,
    coherence_warning=60.0,
    coherence_good=80.0,
    
    ramp_up_phase1_factor=0.30,
    ramp_up_phase2_factor=0.50,
    ramp_up_phase3_factor=0.70,
    ramp_up_phase4_factor=0.85,
    ramp_up_phase1_trades=5,
    ramp_up_phase2_trades=10,
    ramp_up_phase3_trades=20,
    ramp_up_phase4_trades=50,
    
    hmm_veto_enabled=True,
    hmm_veto_confidence_threshold=0.85,
    
    score_very_strong=20,
    score_strong=10,
    score_moderate=5,
    
    regime_change_veto_enabled=True
)


PAPER_AGGRESSIVE_PROFILE = TradingProfile(
    name="PAPER_AGGRESSIVE",
    description="Perfil agresivo para paper trading - Más trades para construir track record. "
                "Umbrales más bajos para permitir más oportunidades. "
                "Ramp-up más rápido. Ideal para demostrar capacidades a inversores.",
    
    min_trade_usd=50.0,
    max_position_pct=0.15,
    stop_loss_pct=0.025,
    stop_loss_pct_high_vol=0.035,
    take_profit_pct=0.04,
    take_profit_pct_high_vol=0.05,
    max_daily_loss_pct=0.12,
    min_confidence=0.10,
    check_interval_seconds=20,
    trades_per_day_target=40,
    
    coherence_veto_critical=20.0,
    coherence_veto_normal=30.0,
    coherence_warning=45.0,
    coherence_good=65.0,
    
    ramp_up_phase1_factor=0.50,
    ramp_up_phase2_factor=0.70,
    ramp_up_phase3_factor=0.85,
    ramp_up_phase4_factor=0.95,
    ramp_up_phase1_trades=3,
    ramp_up_phase2_trades=7,
    ramp_up_phase3_trades=15,
    ramp_up_phase4_trades=30,
    
    hmm_veto_enabled=True,
    hmm_veto_confidence_threshold=0.92,
    
    score_very_strong=15,
    score_strong=8,
    score_moderate=3,
    
    regime_change_veto_enabled=False
)


BALANCED_PROFILE = TradingProfile(
    name="BALANCED",
    description="Perfil equilibrado - Término medio entre conservador y agresivo. "
                "Bueno para transición o cuando quieres más trades sin arriesgar demasiado.",
    
    min_trade_usd=60.0,
    max_position_pct=0.13,
    stop_loss_pct=0.022,
    stop_loss_pct_high_vol=0.032,
    take_profit_pct=0.035,
    take_profit_pct_high_vol=0.045,
    max_daily_loss_pct=0.10,
    min_confidence=0.12,
    check_interval_seconds=22,
    trades_per_day_target=32,
    
    coherence_veto_critical=25.0,
    coherence_veto_normal=38.0,
    coherence_warning=55.0,
    coherence_good=72.0,
    
    ramp_up_phase1_factor=0.40,
    ramp_up_phase2_factor=0.60,
    ramp_up_phase3_factor=0.78,
    ramp_up_phase4_factor=0.90,
    ramp_up_phase1_trades=4,
    ramp_up_phase2_trades=8,
    ramp_up_phase3_trades=18,
    ramp_up_phase4_trades=40,
    
    hmm_veto_enabled=True,
    hmm_veto_confidence_threshold=0.88,
    
    score_very_strong=17,
    score_strong=9,
    score_moderate=4,
    
    regime_change_veto_enabled=True
)


PAPER_OPTIMIZED_PROFILE = TradingProfile(
    name="PAPER_OPTIMIZED",
    description="Perfil optimizado para paper trading V6.5.4 - Diseñado para inversores. "
                "Ratio R:R mejorado (SL 1.5%/TP 3.0% estables, SL 2.5%/TP 4.5% volátiles). "
                "Coherence Engine estricto (5/6). Alta selectividad para win rate 55%+.",
    
    min_trade_usd=100.0,
    max_position_pct=0.08,
    stop_loss_pct=0.015,
    stop_loss_pct_high_vol=0.025,
    take_profit_pct=0.030,
    take_profit_pct_high_vol=0.045,
    max_daily_loss_pct=0.04,
    min_confidence=0.22,
    check_interval_seconds=35,
    trades_per_day_target=12,
    
    coherence_veto_critical=45.0,
    coherence_veto_normal=60.0,
    coherence_warning=75.0,
    coherence_good=88.0,
    
    ramp_up_phase1_factor=0.20,
    ramp_up_phase2_factor=0.40,
    ramp_up_phase3_factor=0.60,
    ramp_up_phase4_factor=0.75,
    ramp_up_phase1_trades=15,
    ramp_up_phase2_trades=35,
    ramp_up_phase3_trades=70,
    ramp_up_phase4_trades=120,
    
    hmm_veto_enabled=True,
    hmm_veto_confidence_threshold=0.75,
    
    score_very_strong=28,
    score_strong=18,
    score_moderate=10,
    
    regime_change_veto_enabled=True
)


WIN_RATE_OPTIMIZED_PROFILE = TradingProfile(
    name="WIN_RATE_OPTIMIZED",
    description="Perfil V6.5.4 PREMIUM - Win Rate 55%+ con calibración por par. "
                "Opera BTC/USD, XRP/USD, ADA/USD, LINK/USD. "
                "SL/TP diferenciados por símbolo. Tier PROVEN vs CALIBRATING. "
                "Check cada 15s. Institucional-grade.",
    
    min_trade_usd=150.0,
    max_position_pct=0.10,
    stop_loss_pct=0.012,
    stop_loss_pct_high_vol=0.018,
    take_profit_pct=0.035,
    take_profit_pct_high_vol=0.050,
    max_daily_loss_pct=0.03,
    min_confidence=0.25,
    check_interval_seconds=15,
    trades_per_day_target=12,
    
    coherence_veto_critical=50.0,
    coherence_veto_normal=65.0,
    coherence_warning=78.0,
    coherence_good=90.0,
    
    ramp_up_phase1_factor=0.25,
    ramp_up_phase2_factor=0.45,
    ramp_up_phase3_factor=0.65,
    ramp_up_phase4_factor=0.80,
    ramp_up_phase1_trades=10,
    ramp_up_phase2_trades=25,
    ramp_up_phase3_trades=50,
    ramp_up_phase4_trades=100,
    
    hmm_veto_enabled=True,
    hmm_veto_confidence_threshold=0.70,
    
    score_very_strong=30,
    score_strong=20,
    score_moderate=12,
    
    regime_change_veto_enabled=True,
    
    extra_params={
        'allowed_symbols': ['BTC/USD', 'XRP/USD', 'ADA/USD', 'LINK/USD'],
        'excluded_symbols': ['SOL/USD', 'ETH/USD', 'DOT/USD', 'AVAX/USD', 'ATOM/USD', 'POL/USD', 'LTC/USD'],
        'use_pair_calibration': True,
        'risk_reward_min': 2.0,
        'force_sl_execution': True,
        'sl_check_interval_seconds': 10
    }
)


TRADING_PROFILES: Dict[str, TradingProfile] = {
    "INSTITUTIONAL": INSTITUTIONAL_PROFILE,
    "PAPER_AGGRESSIVE": PAPER_AGGRESSIVE_PROFILE,
    "BALANCED": BALANCED_PROFILE,
    "PAPER_OPTIMIZED": PAPER_OPTIMIZED_PROFILE,
    "WIN_RATE_OPTIMIZED": WIN_RATE_OPTIMIZED_PROFILE
}


def get_profile_by_name(name: str) -> Optional[TradingProfile]:
    """
    Obtener perfil por nombre.
    
    Args:
        name: Nombre del perfil (INSTITUTIONAL, PAPER_AGGRESSIVE, BALANCED)
    
    Returns:
        TradingProfile o None si no existe
    """
    return TRADING_PROFILES.get(name.upper())


def get_active_profile() -> TradingProfile:
    """
    Obtener el perfil activo basado en la variable de entorno TRADING_PROFILE.
    
    Por defecto retorna INSTITUTIONAL si no se especifica o el nombre es inválido.
    
    Environment:
        TRADING_PROFILE: Nombre del perfil a usar
    
    Returns:
        TradingProfile activo
    """
    profile_name = os.environ.get('TRADING_PROFILE', 'INSTITUTIONAL').upper()
    
    profile = TRADING_PROFILES.get(profile_name)
    
    if profile is None:
        logger.warning(
            f"⚠️ Perfil '{profile_name}' no encontrado. "
            f"Perfiles disponibles: {list(TRADING_PROFILES.keys())}. "
            f"Usando INSTITUTIONAL por defecto."
        )
        profile = INSTITUTIONAL_PROFILE
    else:
        logger.info(f"📊 Trading Profile activo: {profile.name}")
        logger.info(f"   📝 {profile.description[:80]}...")
    
    return profile


def log_profile_comparison():
    """Log comparación de todos los perfiles para debugging"""
    logger.info("=" * 70)
    logger.info("📊 COMPARACIÓN DE PERFILES DE TRADING")
    logger.info("=" * 70)
    
    headers = ["Parámetro", "INSTITUTIONAL", "BALANCED", "PAPER_AGGRESSIVE"]
    
    params = [
        ("Coherence VETO Critical", "coherence_veto_critical", "%"),
        ("Coherence VETO Normal", "coherence_veto_normal", "%"),
        ("Min Confidence", "min_confidence", ""),
        ("Ramp-Up Fase 1", "ramp_up_phase1_factor", "x"),
        ("Score Moderado Min", "score_moderate", "pts"),
        ("Trades/Día Target", "trades_per_day_target", ""),
        ("HMM VETO Threshold", "hmm_veto_confidence_threshold", ""),
    ]
    
    for param_name, attr, unit in params:
        inst = getattr(INSTITUTIONAL_PROFILE, attr)
        bal = getattr(BALANCED_PROFILE, attr)
        pap = getattr(PAPER_AGGRESSIVE_PROFILE, attr)
        logger.info(f"   {param_name}: {inst}{unit} | {bal}{unit} | {pap}{unit}")
    
    logger.info("=" * 70)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    log_profile_comparison()
    
    profile = get_active_profile()
    print(f"\nPerfil activo: {profile.name}")
    print(f"Descripción: {profile.description}")
    print(f"\nConfiguración completa:")
    import json
    print(json.dumps(profile.to_dict(), indent=2))
