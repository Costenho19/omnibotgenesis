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
            import psycopg
            database_url = os.environ.get('DATABASE_URL')
            
            if not database_url:
                logger.warning("DATABASE_URL not available for HonestyGuard")
                return PerformanceSnapshot(data_available=False, error="No DATABASE_URL")
            
            conn = psycopg.connect(database_url)
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


# =============================================================================
# HONEST FRAMING FORMATTER (Jan 10, 2026)
# =============================================================================
# DECISIÓN ÉTICA: Transparencia sobre ocultación
# Este sistema NO oculta información negativa.
# En su lugar, presenta TODOS los datos reales con contexto positivo pero honesto.
# Referencia: ADR-002-honest-framing-over-censorship.md
# =============================================================================

class HonestFramingFormatter:
    """
    Formateador de respuestas con "Honest Framing".
    
    FILOSOFÍA:
    - NUNCA ocultar métricas negativas CUANDO LAS PREGUNTAN
    - Solo mostrar métricas detalladas cuando el usuario las solicita
    - Contextualizar con frame positivo pero VERDADERO
    - Ejemplo: "Win Rate: 20.17% (objetivo: 40%+)" - NO oculta, contextualiza
    
    COMPORTAMIENTO:
    - Si usuario NO pregunta por métricas: respuesta normal sin datos internos
    - Si usuario PREGUNTA por métricas: mostrar TODOS los datos con honest framing
    
    RAZÓN ÉTICA:
    - Ocultar pérdidas a inversores puede constituir fraude por omisión
    - La transparencia construye confianza real
    - El sistema funciona (preserva capital) - eso ES la historia positiva
    
    Created: Jan 10, 2026
    """
    
    def __init__(self):
        pass
    
    def should_show_metrics(self, user_message: str) -> bool:
        """
        Detecta si el usuario está preguntando por métricas/rendimiento.
        Usa los mismos patrones que PerformanceHonestyGuard.
        """
        message_lower = user_message.lower()
        
        # Patrones que indican pregunta sobre métricas
        metrics_patterns = [
            'win rate', 'winrate', 'tasa de acierto',
            'p&l', 'pnl', 'profit', 'loss', 'pérdida', 'ganancia',
            'rendimiento', 'performance', 'resultado',
            'cómo va', 'como va', 'cómo vamos', 'como vamos',
            'métricas', 'metricas', 'stats', 'estadísticas',
            'track record', 'historial',
            'balance', 'capital',
            'trades', 'operaciones',
            'roi', 'retorno', 'return',
            'qué tal', 'que tal',
            'funciona', 'working',
            'rentable', 'profitable',
        ]
        
        for pattern in metrics_patterns:
            if pattern in message_lower:
                return True
        
        return False
    
    def format_metrics_honestly(self, language: str = 'es') -> str:
        """
        Genera resumen de métricas con honest framing.
        MUESTRA TODOS los datos reales, con contexto positivo pero verdadero.
        """
        try:
            import psycopg
            database_url = os.environ.get('DATABASE_URL')
            
            if not database_url:
                return self._default_honest_summary(language)
            
            conn = psycopg.connect(database_url)
            cursor = conn.cursor()
            
            # Obtener métricas REALES
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_trades,
                    COUNT(CASE WHEN profit_loss > 0 THEN 1 END) as winners,
                    COALESCE(SUM(profit_loss), 0) as total_pnl
                FROM paper_trading_trades WHERE status = 'closed'
            ''')
            row = cursor.fetchone()
            total_trades = row[0] or 0
            winners = row[1] or 0
            total_pnl = float(row[2]) if row[2] else 0
            win_rate = (winners / total_trades * 100) if total_trades > 0 else 0
            
            cursor.execute('SELECT balance_usd FROM paper_trading_balances LIMIT 1')
            balance_row = cursor.fetchone()
            balance = float(balance_row[0]) if balance_row else 1000000
            
            cursor.execute('SELECT COUNT(*) FROM trading_veto_log')
            veto_count = cursor.fetchone()[0] or 0
            
            cursor.close()
            conn.close()
            
            # Calcular métricas derivadas
            capital_preserved_pct = (balance / 1000000) * 100
            
            if language == 'es':
                return f"""**OMNIX - Estado Actual (Datos Reales)**

📊 **MÉTRICAS DE TRADING**:
• Trades ejecutados: {total_trades}
• Win Rate: {win_rate:.1f}% (objetivo: 40%+)
• P&L: ${total_pnl:,.2f}
• Capital actual: ${balance:,.2f} ({capital_preserved_pct:.1f}% preservado de $1M)

🛡️ **SISTEMA DE PROTECCIÓN**:
• Operaciones bloqueadas: {veto_count:,}
• Prioriza preservación sobre volumen
• Modo protección activado ante condiciones adversas

📌 **FASE ACTUAL**:
Sistema en validación extendida. El bajo volumen de operaciones 
refleja que el sistema detecta condiciones desfavorables y 
prefiere NO operar a tomar riesgos excesivos.

Para inversores: Due diligence completo disponible bajo solicitud."""
            else:
                return f"""**OMNIX - Current Status (Real Data)**

📊 **TRADING METRICS**:
• Trades executed: {total_trades}
• Win Rate: {win_rate:.1f}% (target: 40%+)
• P&L: ${total_pnl:,.2f}
• Current capital: ${balance:,.2f} ({capital_preserved_pct:.1f}% preserved from $1M)

🛡️ **PROTECTION SYSTEM**:
• Operations blocked: {veto_count:,}
• Prioritizes preservation over volume
• Protection mode activated during adverse conditions

📌 **CURRENT PHASE**:
System in extended validation. Low operation volume 
reflects that the system detects unfavorable conditions and 
prefers NOT to operate over taking excessive risks.

For investors: Full due diligence available upon request."""
            
        except Exception as e:
            logger.warning(f"Error generating honest metrics: {e}")
            return self._default_honest_summary(language)
    
    def _default_honest_summary(self, language: str = 'es') -> str:
        if language == 'es':
            return """**OMNIX - Estado del Sistema**

Sistema en fase de validación extendida.
Métricas detalladas disponibles bajo solicitud.

El sistema prioriza preservación de capital sobre volumen de operaciones.
Para inversores: Due diligence completo disponible."""
        else:
            return """**OMNIX - System Status**

System in extended validation phase.
Detailed metrics available upon request.

The system prioritizes capital preservation over operation volume.
For investors: Full due diligence available."""
    
    def add_honest_context(self, response: str, metrics: Optional[Dict[str, Any]] = None) -> str:
        """
        Añade contexto honesto a una respuesta sin ocultar información.
        Solo añade frame positivo donde es VERDADERO.
        """
        # No modificamos la respuesta, solo aseguramos que tenga contexto
        # Esta función está disponible para uso futuro si se necesita
        return response


# Global instance
_honest_formatter: Optional[HonestFramingFormatter] = None

def get_honest_formatter() -> HonestFramingFormatter:
    """Get or create global HonestFramingFormatter instance."""
    global _honest_formatter
    if _honest_formatter is None:
        _honest_formatter = HonestFramingFormatter()
    return _honest_formatter


def get_honest_metrics_summary(language: str = 'es') -> str:
    """
    Convenience function to get honest metrics summary.
    MUESTRA TODOS los datos reales con contexto positivo.
    """
    return get_honest_formatter().format_metrics_honestly(language)


def should_show_metrics(user_message: str) -> bool:
    """
    Detecta si el usuario está preguntando por métricas.
    Solo mostrar datos cuando los piden.
    """
    return get_honest_formatter().should_show_metrics(user_message)


def get_metrics_if_asked(user_message: str, language: str = 'es') -> Optional[str]:
    """
    Retorna métricas honestas SOLO si el usuario las pidió.
    
    Args:
        user_message: Mensaje del usuario
        language: 'es' o 'en'
        
    Returns:
        Métricas formateadas si las pidió, None si no
    """
    formatter = get_honest_formatter()
    if formatter.should_show_metrics(user_message):
        return formatter.format_metrics_honestly(language)
    return None


# ---------------------------------------------------------------------------
# GOVERNANCE LIVE METRICS — consulta BD en tiempo real para el prompt del bot
# ---------------------------------------------------------------------------

class GovernanceLiveMetrics:
    """
    Consulta PostgreSQL en tiempo real para obtener las métricas reales del sistema.
    Se inyecta siempre en el prompt del bot, reemplazando los valores hardcodeados.
    Cache de 5 minutos para no sobrecargar la BD en cada mensaje.
    """

    _instance: Optional['GovernanceLiveMetrics'] = None
    _CACHE_TTL = 300  # segundos

    def __init__(self):
        self._cache: Optional[Dict[str, Any]] = None
        self._cache_ts: Optional[datetime] = None

    @classmethod
    def get_instance(cls) -> 'GovernanceLiveMetrics':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _fetch(self) -> Dict[str, Any]:
        """Consulta la BD y devuelve métricas de gobernanza reales."""
        try:
            import psycopg
            database_url = os.environ.get('DATABASE_URL')
            if not database_url:
                return {}

            conn = psycopg.connect(database_url)
            cur = conn.cursor()

            # 1. Total recibos PQC
            cur.execute("SELECT COUNT(*) FROM decision_receipts;")
            pqc_receipts = cur.fetchone()[0]

            # 2. Ciclos de gobernanza (shadow_trade_events)
            cur.execute("SELECT COUNT(*) FROM shadow_trade_events;")
            eval_cycles = cur.fetchone()[0]

            # 3. Decisiones bloqueadas (BLOCK + BLOCKED)
            cur.execute("""
                SELECT COUNT(*) FROM decision_receipts
                WHERE decision IN ('BLOCK', 'BLOCKED');
            """)
            blocked = cur.fetchone()[0]

            # 4. Capital preservation desde paper_trading_balances
            cur.execute("""
                SELECT balance_usd FROM paper_trading_balances
                ORDER BY updated_at DESC LIMIT 1;
            """)
            row = cur.fetchone()
            initial_capital = 1_000_000.0
            current_balance = float(row[0]) if row else initial_capital
            capital_pct = (current_balance / initial_capital) * 100

            cur.close()
            conn.close()

            return {
                'pqc_receipts': pqc_receipts,
                'eval_cycles': eval_cycles,
                'blocked': blocked,
                'current_balance': current_balance,
                'capital_pct': round(capital_pct, 2),
                'fetched_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'),
            }

        except Exception as e:
            logger.warning(f"GovernanceLiveMetrics DB error: {e}")
            return {}

    def get_metrics(self, force: bool = False) -> Dict[str, Any]:
        """Devuelve métricas con caché de 5 min."""
        now = datetime.now()
        if (not force and self._cache is not None and self._cache_ts is not None
                and (now - self._cache_ts).total_seconds() < self._CACHE_TTL):
            return self._cache
        self._cache = self._fetch()
        self._cache_ts = now
        return self._cache

    def build_prompt_block(self) -> str:
        """
        Genera el bloque de métricas reales para inyectar en el prompt.
        Si la BD no está disponible, devuelve string vacío (el prompt usa los fallbacks).
        """
        m = self.get_metrics()
        if not m:
            return ""

        return f"""
## GOVERNANCE METRICS — DATOS EN VIVO DE LA BASE DE DATOS (actualizado: {m['fetched_at']})
> INSTRUCCIÓN CRÍTICA: Usa ESTOS números en todas tus respuestas. Ignora cualquier número anterior en el prompt.

**PQC receipts firmados (Dilithium-3):** {m['pqc_receipts']:,} — verificables en omnixquantum.net/verify
**Ciclos de gobernanza totales:** {m['eval_cycles']:,}
**Decisiones bloqueadas (BLOCK/BLOCKED):** {m['blocked']:,}
**Capital actual:** ${m['current_balance']:,.2f} de $1,000,000.00 inicial
**Capital preservation:** {m['capital_pct']}%
"""


_governance_live_metrics = GovernanceLiveMetrics.get_instance()


def get_governance_metrics_injection() -> str:
    """
    Función de conveniencia para obtener el bloque de métricas reales.
    Se llama desde build_complete_prompt en prompt_templates.py.
    """
    return _governance_live_metrics.build_prompt_block()
