"""
OMNIX V6.5.4d - Performance Honesty Guard (Context-Aware)
Created: Jan 3, 2026
Updated: Jan 4, 2026

Módulo que contextualiza las métricas de trading dentro de la estrategia de 2 fases.
Se activa SOLO cuando el usuario pregunta sobre rendimiento/métricas.

ESTRATEGIA DE 2 FASES:
- FASE 1 (Anti-Pérdida): Sistema aprende a NO perder. Pérdidas = datos de entrenamiento.
- FASE 2 (Optimización): Una vez que evita pérdidas, se optimiza para ganar.

FILOSOFÍA:
- Honesto pero sin auto-destruirse
- Contextualizar pérdidas como parte del plan, no como fracaso
- Solo activar cuando preguntan específicamente sobre métricas
- Dar datos reales sin evasivas ni drama
"""

import logging
import os
import re
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

MIN_TRADES_FOR_JUDGMENT = 50

PHASE_TRANSITION_CRITERIA = {
    'phase1_to_phase2': {
        'min_trades': 200,
        'min_profit_factor': 0.8,
        'min_win_rate': 0.35,
        'max_consecutive_losses': 5
    }
}

@dataclass
class HonestyThresholds:
    profit_factor_phase2_ready: float = 0.8
    profit_factor_learning: float = 0.5
    win_rate_phase2_ready: float = 0.35
    win_rate_learning: float = 0.25
    pnl_concern_usd: float = -20000


@dataclass  
class PerformanceSnapshot:
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    total_pnl: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    data_available: bool = False
    error: Optional[str] = None


PERFORMANCE_INTENT_PATTERNS = [
    r'\b(profit\s*factor|pf)\b',
    r'\b(win\s*rate|winrate|tasa\s*de\s*acierto)\b',
    r'\b(c[oó]mo\s*(vamos|va|est[aá]|anda))\b',
    r'\b(rendimiento|performance|resultados?)\b',
    r'\b(ganando|perdiendo|winning|losing)\b',
    r'\b(ganancias?|p[eé]rdidas?)\b',
    r'\b(p\s*&\s*l|pnl|profit|loss)\b',
    r'\b(m[eé]tricas?|metrics?|estad[ií]sticas?|stats?)\b',
    r'\b(funciona|working|sirve)\b.*\b(estrategia|strategy|bot|sistema)\b',
    r'\b(track\s*record)\b',
    r'\b(edge|ventaja)\b',
    r'\b(rentable|profitable|rentabilidad)\b',
    r'\b(roi|return|retorno)\b',
    r'\b(capital|inversi[oó]n)\b.*\b(resultado|retorno)\b',
    r'\bqu[eé]\s*tal\s*(va|vamos|el\s*bot)\b',
    r'\bc[oó]mo\s*(va|anda)\s*(el\s*)?(rendimiento|bot|trading)\b',
    r'\btenemos\s*(ganancias?|p[eé]rdidas?)\b',
]

CONTEXTUAL_STATEMENTS = {
    'phase1_early': {
        'en': [
            "Current Phase: Pattern Recognition (Phase 1)",
            "Metrics: Profit Factor {pf:.2f}, Win Rate {wr:.1%} across {trades} trades.",
            "Context: The system is in capital deployment learning phase, identifying which market conditions to filter. These results inform the risk management calibration.",
            "Progress: Once pattern recognition stabilizes, we transition to profit optimization (Phase 2)."
        ],
        'es': [
            "Fase Actual: Reconocimiento de Patrones (Fase 1)",
            "Métricas: Profit Factor {pf:.2f}, Win Rate {wr:.1%} en {trades} trades.",
            "Contexto: El sistema está en fase de aprendizaje de capital deployment, identificando qué condiciones de mercado filtrar. Estos resultados informan la calibración de risk management.",
            "Progreso: Una vez que el reconocimiento de patrones se estabilice, pasamos a optimización de ganancias (Fase 2)."
        ]
    },
    'phase1_progress': {
        'en': [
            "Current Phase: Pattern Recognition (Phase 1) - Making Progress",
            "Metrics: Profit Factor {pf:.2f}, Win Rate {wr:.1%} across {trades} trades, P&L: ${pnl:,.2f}",
            "Context: The system is learning which conditions to filter. Unfavorable patterns are being documented and blocked by the veto system.",
            "Next milestone: Achieve PF > 0.8 and WR > 35% before transitioning to Phase 2."
        ],
        'es': [
            "Fase Actual: Reconocimiento de Patrones (Fase 1) - Progresando",
            "Métricas: Profit Factor {pf:.2f}, Win Rate {wr:.1%} en {trades} trades, P&L: ${pnl:,.2f}",
            "Contexto: El sistema está aprendiendo qué condiciones filtrar. Los patrones desfavorables se documentan y bloquean por el sistema de veto.",
            "Siguiente hito: Lograr PF > 0.8 y WR > 35% antes de pasar a Fase 2."
        ]
    },
    'phase1_ready': {
        'en': [
            "Current Phase: Pattern Recognition (Phase 1) - Near Transition",
            "Metrics: Profit Factor {pf:.2f}, Win Rate {wr:.1%} across {trades} trades, P&L: ${pnl:,.2f}",
            "Context: Pattern filtering is stabilizing. System approaching Phase 2 criteria.",
            "Next step: Continue monitoring for consistent performance before enabling profit optimization."
        ],
        'es': [
            "Fase Actual: Reconocimiento de Patrones (Fase 1) - Cerca de Transición",
            "Métricas: Profit Factor {pf:.2f}, Win Rate {wr:.1%} en {trades} trades, P&L: ${pnl:,.2f}",
            "Contexto: El filtrado de patrones se estabiliza. Sistema acercándose a criterios de Fase 2.",
            "Siguiente paso: Continuar monitoreando rendimiento consistente antes de habilitar optimización de ganancias."
        ]
    },
    'phase2': {
        'en': [
            "Current Phase: Profit Optimization (Phase 2)",
            "Metrics: Profit Factor {pf:.2f}, Win Rate {wr:.1%} across {trades} trades, P&L: ${pnl:,.2f}",
            "Context: System has demonstrated effective pattern filtering. Now optimizing for consistent profits.",
            "Focus: Maximizing edge in favorable market conditions."
        ],
        'es': [
            "Fase Actual: Optimización de Ganancias (Fase 2)",
            "Métricas: Profit Factor {pf:.2f}, Win Rate {wr:.1%} en {trades} trades, P&L: ${pnl:,.2f}",
            "Contexto: Sistema ha demostrado filtrado efectivo de patrones. Ahora optimizando para ganancias consistentes.",
            "Enfoque: Maximizar edge en condiciones de mercado favorables."
        ]
    },
    'insufficient_data': {
        'en': [
            "Current Phase: Data Collection",
            "Trades so far: {trades} (minimum {min_trades} needed for analysis).",
            "Context: Building baseline data before meaningful metrics can be calculated."
        ],
        'es': [
            "Fase Actual: Recolección de Datos",
            "Trades hasta ahora: {trades} (mínimo {min_trades} necesarios para análisis).",
            "Contexto: Construyendo datos base antes de calcular métricas significativas."
        ]
    }
}


class PerformanceHonestyGuard:
    """
    Guard que evalúa métricas de trading y genera contexto honesto.
    Solo se activa cuando el usuario pregunta sobre rendimiento.
    """
    
    def __init__(self, thresholds: Optional[HonestyThresholds] = None):
        self.thresholds = thresholds or HonestyThresholds()
        self._cached_snapshot: Optional[PerformanceSnapshot] = None
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl_seconds = 60
    
    def _fetch_performance_from_db(self) -> PerformanceSnapshot:
        """Fetch real performance metrics from PostgreSQL."""
        try:
            import psycopg2
            database_url = os.environ.get('DATABASE_URL')
            
            if not database_url:
                logger.warning("DATABASE_URL not available for HonestyGuard")
                return PerformanceSnapshot(data_available=False, error="No DATABASE_URL")
            
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_trades,
                    COUNT(CASE WHEN profit_loss > 0 THEN 1 END) as winning_trades,
                    COUNT(CASE WHEN profit_loss <= 0 THEN 1 END) as losing_trades,
                    COALESCE(SUM(profit_loss), 0) as total_pnl,
                    COALESCE(SUM(CASE WHEN profit_loss > 0 THEN profit_loss ELSE 0 END), 0) as total_wins,
                    COALESCE(SUM(CASE WHEN profit_loss < 0 THEN ABS(profit_loss) ELSE 0 END), 0) as total_losses,
                    COALESCE(AVG(CASE WHEN profit_loss > 0 THEN profit_loss END), 0) as avg_win,
                    COALESCE(AVG(CASE WHEN profit_loss < 0 THEN profit_loss END), 0) as avg_loss
                FROM paper_trading_trades
                WHERE status = 'closed'
            ''')
            
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not row or row[0] == 0:
                return PerformanceSnapshot(data_available=False, error="No closed trades")
            
            total_trades = row[0]
            winning_trades = row[1]
            losing_trades = row[2]
            total_pnl = float(row[3])
            total_wins = float(row[4])
            total_losses = float(row[5])
            avg_win = float(row[6])
            avg_loss = float(row[7])
            
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            profit_factor = total_wins / total_losses if total_losses > 0 else 0
            
            return PerformanceSnapshot(
                total_trades=total_trades,
                winning_trades=winning_trades,
                losing_trades=losing_trades,
                win_rate=win_rate,
                profit_factor=profit_factor,
                total_pnl=total_pnl,
                avg_win=avg_win,
                avg_loss=avg_loss,
                data_available=True
            )
            
        except Exception as e:
            logger.error(f"HonestyGuard DB error: {e}")
            return PerformanceSnapshot(data_available=False, error=str(e))
    
    def get_performance_snapshot(self, force_refresh: bool = False) -> PerformanceSnapshot:
        """Get performance metrics with caching."""
        now = datetime.now()
        
        if (not force_refresh and 
            self._cached_snapshot is not None and 
            self._cache_timestamp is not None and
            (now - self._cache_timestamp).total_seconds() < self._cache_ttl_seconds):
            return self._cached_snapshot
        
        self._cached_snapshot = self._fetch_performance_from_db()
        self._cache_timestamp = now
        return self._cached_snapshot
    
    def detect_performance_intent(self, user_message: str) -> bool:
        """Detect if user is asking about performance/metrics."""
        if not user_message:
            return False
        
        message_lower = user_message.lower()
        
        for pattern in PERFORMANCE_INTENT_PATTERNS:
            if re.search(pattern, message_lower, re.IGNORECASE):
                logger.info(f"🎯 HonestyGuard: Detected performance intent with pattern: {pattern}")
                return True
        
        return False
    
    def determine_phase(self, snapshot: PerformanceSnapshot) -> str:
        """Determine current phase based on metrics."""
        if not snapshot.data_available or snapshot.total_trades < MIN_TRADES_FOR_JUDGMENT:
            return 'insufficient_data'
        
        pf = snapshot.profit_factor
        wr = snapshot.win_rate
        trades = snapshot.total_trades
        
        criteria = PHASE_TRANSITION_CRITERIA['phase1_to_phase2']
        
        if (pf >= criteria['min_profit_factor'] and 
            wr >= criteria['min_win_rate'] and
            trades >= criteria['min_trades']):
            return 'phase2'
        
        if pf >= self.thresholds.profit_factor_phase2_ready and wr >= self.thresholds.win_rate_phase2_ready:
            return 'phase1_ready'
        
        if pf >= self.thresholds.profit_factor_learning or wr >= self.thresholds.win_rate_learning:
            return 'phase1_progress'
        
        return 'phase1_early'
    
    def get_honesty_context(self, language: str = 'es', user_message: str = "", force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get honesty context - ONLY activates if user asks about performance.
        
        Returns:
            Dict with:
                - context_active: bool - True if user asked about performance
                - phase: str - Current phase
                - contextual_statements: List[str] - Statements to include
                - metrics_summary: str - Brief metrics
                - raw_metrics: PerformanceSnapshot
        """
        is_performance_query = self.detect_performance_intent(user_message)
        snapshot = self.get_performance_snapshot(force_refresh)
        phase = self.determine_phase(snapshot)
        
        lang_key = 'es' if language.lower().startswith('es') else 'en'
        
        result = {
            'context_active': is_performance_query,
            'phase': phase,
            'contextual_statements': [],
            'metrics_summary': '',
            'raw_metrics': snapshot
        }
        
        if not snapshot.data_available:
            result['metrics_summary'] = "Performance data unavailable"
            return result
        
        result['metrics_summary'] = (
            f"Trades: {snapshot.total_trades}, "
            f"Win Rate: {snapshot.win_rate:.1%}, "
            f"Profit Factor: {snapshot.profit_factor:.2f}, "
            f"P&L: ${snapshot.total_pnl:,.2f}"
        )
        
        if is_performance_query:
            statements = CONTEXTUAL_STATEMENTS.get(phase, {}).get(lang_key, [])
            result['contextual_statements'] = [
                stmt.format(
                    pf=snapshot.profit_factor,
                    wr=snapshot.win_rate,
                    trades=snapshot.total_trades,
                    pnl=snapshot.total_pnl,
                    min_trades=MIN_TRADES_FOR_JUDGMENT
                ) for stmt in statements
            ]
        
        logger.info(f"🔍 HonestyGuard: phase={phase}, query_detected={is_performance_query}, trades={snapshot.total_trades}")
        
        return result
    
    def generate_prompt_injection(self, language: str = 'es', user_message: str = "") -> str:
        """Generate prompt text - only when user asks about performance."""
        context = self.get_honesty_context(language, user_message)
        
        if not context['context_active']:
            return ""
        
        phase = context['phase']
        lang = 'es' if language.lower().startswith('es') else 'en'
        
        if lang == 'es':
            header = f"""
## CONTEXTO DE RENDIMIENTO (Usuario preguntó sobre métricas)
**Fase actual**: {phase.replace('_', ' ').title()}
**Métricas**: {context['metrics_summary']}

**Responder con estos puntos (honesto pero sin drama):**
"""
        else:
            header = f"""
## PERFORMANCE CONTEXT (User asked about metrics)
**Current phase**: {phase.replace('_', ' ').title()}
**Metrics**: {context['metrics_summary']}

**Respond with these points (honest but no drama):**
"""
        
        statements = "\n".join([f"- {s}" for s in context['contextual_statements']])
        
        if lang == 'es':
            instruction = """

**INSTRUCCIONES**:
- Presenta los datos de forma neutra
- Contextualiza dentro de la estrategia de 2 fases
- No seas dramático ni auto-destructivo
- No uses eufemismos vacíos tampoco
- Las pérdidas actuales son datos de entrenamiento, no fracaso
"""
        else:
            instruction = """

**INSTRUCTIONS**:
- Present data neutrally
- Contextualize within the 2-phase strategy
- Don't be dramatic or self-destructive
- Don't use empty euphemisms either
- Current losses are training data, not failure
"""
        
        return f"{header}{statements}{instruction}"


_global_honesty_guard: Optional[PerformanceHonestyGuard] = None

def get_honesty_guard() -> PerformanceHonestyGuard:
    """Get or create global HonestyGuard instance."""
    global _global_honesty_guard
    if _global_honesty_guard is None:
        _global_honesty_guard = PerformanceHonestyGuard()
    return _global_honesty_guard


def get_honesty_context(language: str = 'es', user_message: str = "") -> Dict[str, Any]:
    """Convenience function to get honesty context."""
    return get_honesty_guard().get_honesty_context(language, user_message)


def get_honesty_prompt_injection(language: str = 'es', user_message: str = "") -> str:
    """Convenience function to get prompt injection text."""
    return get_honesty_guard().generate_prompt_injection(language, user_message)


def is_performance_query(user_message: str) -> bool:
    """Check if message is asking about performance."""
    return get_honesty_guard().detect_performance_intent(user_message)
