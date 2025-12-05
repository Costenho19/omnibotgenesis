"""
OMNIX V6.5.3 - Trading Profiles System
=======================================

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
    take_profit_pct: float = 0.03
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
    take_profit_pct=0.03,
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
    take_profit_pct=0.04,
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
    take_profit_pct=0.035,
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


TRADING_PROFILES: Dict[str, TradingProfile] = {
    "INSTITUTIONAL": INSTITUTIONAL_PROFILE,
    "PAPER_AGGRESSIVE": PAPER_AGGRESSIVE_PROFILE,
    "BALANCED": BALANCED_PROFILE
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
