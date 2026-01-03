"""
OMNIX V6.5.4d - Performance Honesty Guard
Created: Jan 3, 2026

Módulo que fuerza respuestas honestas del AI cuando las métricas de trading son malas.
Override del "Institutional Language Enforcement" cuando los números son muy negativos.

FILOSOFÍA:
- Si Profit Factor < 0.5 después de 50+ trades: NO HAY EDGE DEMOSTRADO
- Si Win Rate < 30% después de 50+ trades: LA ESTRATEGIA ESTÁ PERDIENDO
- Honestidad brutal > Frases institucionales vacías

UMBRALES DE HONESTIDAD:
- CRITICAL: PF < 0.3 o WR < 20% → Admitir sin edge, recomendar pausar
- SEVERE: PF < 0.5 o WR < 30% → Admitir problemas serios, explicar causa
- WARNING: PF < 0.8 o WR < 40% → Reconocer resultados mixtos, ser transparente
- OK: PF >= 0.8 y WR >= 40% → Puede usar lenguaje institucional normal
"""

import logging
import os
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

MIN_TRADES_FOR_JUDGMENT = 50

@dataclass
class HonestyThresholds:
    profit_factor_critical: float = 0.3
    profit_factor_severe: float = 0.5
    profit_factor_warning: float = 0.8
    win_rate_critical: float = 0.20
    win_rate_severe: float = 0.30
    win_rate_warning: float = 0.40
    pnl_critical_usd: float = -10000
    pnl_severe_usd: float = -5000


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


BANNED_PHRASES_HONESTY_MODE = [
    "capital deployment in learning phase",
    "strategy calibration in progress",
    "paper trading validation phase",
    "assets under strategic review",
    "risk-managed positions",
    "protective measure activated",
    "building statistical baseline",
    "fase de calibración",
    "despliegue de capital en fase de aprendizaje",
    "medida protectora activada",
    "construyendo baseline estadístico",
    "disciplina institucional",
    "institutional discipline",
    "founder controlling risk",
    "fundador controlando riesgo",
    "expected during system optimization",
    "esperado durante optimización",
    "refinando parámetros",
    "refining parameters",
    "building verified track record",
    "construyendo track record verificado",
]

HONESTY_STATEMENTS = {
    'critical': {
        'en': [
            "HONEST ASSESSMENT: With Profit Factor {pf:.2f} and Win Rate {wr:.1%} after {trades} trades, there is NO demonstrated trading edge.",
            "The current approach is consistently losing money. These results indicate the system needs fundamental changes.",
            "RECOMMENDATION: Pause all trading until a profitable approach is identified through backtesting.",
            "Being transparent: A simple RSI approach would likely outperform current results."
        ],
        'es': [
            "EVALUACIÓN HONESTA: Con Profit Factor {pf:.2f} y Win Rate {wr:.1%} después de {trades} trades, NO hay edge de trading demostrado.",
            "El enfoque actual está perdiendo dinero consistentemente. Estos resultados indican que el sistema necesita cambios fundamentales.",
            "RECOMENDACIÓN: Pausar todo trading hasta identificar un enfoque rentable mediante backtesting.",
            "Siendo transparente: Un enfoque RSI simple probablemente superaría estos resultados."
        ]
    },
    'severe': {
        'en': [
            "HONEST ASSESSMENT: With Profit Factor {pf:.2f} and Win Rate {wr:.1%}, the approach is underperforming significantly.",
            "After {trades} trades, the data shows consistent losses. This requires fundamental changes to the trading logic.",
            "RECOMMENDATION: Analyze which market conditions cause losses and either fix or remove those modules."
        ],
        'es': [
            "EVALUACIÓN HONESTA: Con Profit Factor {pf:.2f} y Win Rate {wr:.1%}, el enfoque está rindiendo muy por debajo de lo esperado.",
            "Después de {trades} trades, los datos muestran pérdidas consistentes. Esto requiere cambios fundamentales a la lógica de trading.",
            "RECOMENDACIÓN: Analizar qué condiciones de mercado causan las pérdidas y corregir o eliminar esos módulos."
        ]
    },
    'warning': {
        'en': [
            "TRANSPARENT UPDATE: Results are mixed. Profit Factor {pf:.2f} and Win Rate {wr:.1%} after {trades} trades.",
            "The approach shows potential but needs optimization. Current results would not satisfy institutional investors.",
            "Focus areas: Identify which pairs/conditions are profitable and double down on those."
        ],
        'es': [
            "ACTUALIZACIÓN TRANSPARENTE: Los resultados son mixtos. Profit Factor {pf:.2f} y Win Rate {wr:.1%} después de {trades} trades.",
            "El enfoque muestra potencial pero necesita optimización. Los resultados actuales no satisfarían inversores institucionales.",
            "Áreas de enfoque: Identificar qué pares/condiciones son rentables y duplicar esfuerzos ahí."
        ]
    }
}


class PerformanceHonestyGuard:
    """
    Guard que evalúa métricas de trading y genera contexto honesto para el AI.
    
    Uso:
        guard = PerformanceHonestyGuard()
        context = guard.get_honesty_context(language='es')
        
        if context['honesty_mode_active']:
            # Inyectar context['mandatory_statements'] en el prompt
            # Activar context['banned_phrases'] para filtrado
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
    
    def evaluate_severity(self, snapshot: PerformanceSnapshot) -> str:
        """Evaluate severity level based on metrics."""
        if not snapshot.data_available or snapshot.total_trades < MIN_TRADES_FOR_JUDGMENT:
            return 'insufficient_data'
        
        pf = snapshot.profit_factor
        wr = snapshot.win_rate
        pnl = snapshot.total_pnl
        
        if (pf < self.thresholds.profit_factor_critical or 
            wr < self.thresholds.win_rate_critical or
            pnl < self.thresholds.pnl_critical_usd):
            return 'critical'
        
        if (pf < self.thresholds.profit_factor_severe or 
            wr < self.thresholds.win_rate_severe or
            pnl < self.thresholds.pnl_severe_usd):
            return 'severe'
        
        if (pf < self.thresholds.profit_factor_warning or 
            wr < self.thresholds.win_rate_warning):
            return 'warning'
        
        return 'ok'
    
    def get_honesty_context(self, language: str = 'es', force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get honesty context to inject into AI prompts.
        
        Returns:
            Dict with:
                - honesty_mode_active: bool
                - severity: str ('critical', 'severe', 'warning', 'ok', 'insufficient_data')
                - mandatory_statements: List[str] - MUST be included in response
                - banned_phrases: List[str] - MUST be filtered out
                - metrics_summary: str - Brief metrics for context
                - raw_metrics: PerformanceSnapshot
        """
        snapshot = self.get_performance_snapshot(force_refresh)
        severity = self.evaluate_severity(snapshot)
        
        lang_key = 'es' if language.lower().startswith('es') else 'en'
        
        result = {
            'honesty_mode_active': severity in ('critical', 'severe', 'warning'),
            'severity': severity,
            'mandatory_statements': [],
            'banned_phrases': [],
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
        
        if severity in ('critical', 'severe', 'warning'):
            result['banned_phrases'] = BANNED_PHRASES_HONESTY_MODE.copy()
            
            statements = HONESTY_STATEMENTS.get(severity, {}).get(lang_key, [])
            result['mandatory_statements'] = [
                stmt.format(
                    pf=snapshot.profit_factor,
                    wr=snapshot.win_rate,
                    trades=snapshot.total_trades,
                    pnl=snapshot.total_pnl
                ) for stmt in statements
            ]
        
        logger.info(f"🔍 HonestyGuard: severity={severity}, trades={snapshot.total_trades}, PF={snapshot.profit_factor:.2f}, WR={snapshot.win_rate:.1%}")
        
        return result
    
    def generate_prompt_injection(self, language: str = 'es') -> str:
        """Generate prompt text to inject for honesty mode."""
        context = self.get_honesty_context(language)
        
        if not context['honesty_mode_active']:
            return ""
        
        severity = context['severity']
        lang = 'es' if language.lower().startswith('es') else 'en'
        
        if lang == 'es':
            header = f"""
## MODO HONESTIDAD ACTIVADO [SEVERITY: {severity.upper()}]
**OVERRIDE OBLIGATORIO del lenguaje institucional debido a métricas pobres.**
**Métricas actuales**: {context['metrics_summary']}

**DECLARACIONES OBLIGATORIAS** - DEBES incluir estas en tu respuesta:
"""
        else:
            header = f"""
## HONESTY MODE ACTIVE [SEVERITY: {severity.upper()}]
**MANDATORY OVERRIDE of institutional language due to poor metrics.**
**Current metrics**: {context['metrics_summary']}

**MANDATORY STATEMENTS** - You MUST include these in your response:
"""
        
        statements = "\n".join([f"- {s}" for s in context['mandatory_statements']])
        
        if lang == 'es':
            banned_header = "\n**FRASES PROHIBIDAS** - NO uses estas frases evasivas:"
        else:
            banned_header = "\n**BANNED PHRASES** - Do NOT use these evasive phrases:"
        
        banned = "\n".join([f"- \"{p}\"" for p in context['banned_phrases']])
        
        if lang == 'es':
            instruction = """
**INSTRUCCIÓN CRÍTICA**: 
- Sé DIRECTO y HONESTO sobre los resultados
- NO uses eufemismos o frases institucionales vacías
- Admite que no hay edge demostrado si los números lo indican
- Recomienda acciones concretas, no promesas vagas
- Mantén la respuesta CONCISA (máximo 4 párrafos)
"""
        else:
            instruction = """
**CRITICAL INSTRUCTION**:
- Be DIRECT and HONEST about results
- Do NOT use euphemisms or empty institutional phrases
- Admit there is no demonstrated edge if numbers indicate so
- Recommend concrete actions, not vague promises
- Keep response CONCISE (maximum 4 paragraphs)
"""
        
        return f"{header}{statements}{banned_header}{banned}{instruction}"


_global_honesty_guard: Optional[PerformanceHonestyGuard] = None

def get_honesty_guard() -> PerformanceHonestyGuard:
    """Get or create global HonestyGuard instance."""
    global _global_honesty_guard
    if _global_honesty_guard is None:
        _global_honesty_guard = PerformanceHonestyGuard()
    return _global_honesty_guard


def get_honesty_context(language: str = 'es') -> Dict[str, Any]:
    """Convenience function to get honesty context."""
    return get_honesty_guard().get_honesty_context(language)


def get_honesty_prompt_injection(language: str = 'es') -> str:
    """Convenience function to get prompt injection text."""
    return get_honesty_guard().generate_prompt_injection(language)
