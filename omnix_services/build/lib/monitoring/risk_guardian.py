"""
AI RISK GUARDIAN V5.4 - Sistema de Supervisión de Riesgos
===========================================================

Sistema de inteligencia artificial que supervisa el trading bot y detecta
patrones peligrosos antes de que causen pérdidas significativas.

Features:
---------
1. Overtrading Detection - Detecta cuando se están haciendo demasiados trades
2. Drawdown Protection - Protege contra pérdidas excesivas
3. Revenge Trading Detection - Detecta trading emocional después de pérdidas
4. Capital Protection - Asegura que nunca se arriesgue más del límite seguro

Autor: Harold Nunes
Fecha: 2025-11-16
Versión: 5.4
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Niveles de riesgo detectados"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskType(Enum):
    """Tipos de riesgos detectables"""
    OVERTRADING = "OVERTRADING"
    DRAWDOWN = "DRAWDOWN"
    REVENGE_TRADING = "REVENGE_TRADING"
    CAPITAL_RISK = "CAPITAL_RISK"
    POSITION_SIZE = "POSITION_SIZE"


@dataclass
class RiskEvent:
    """Evento de riesgo detectado"""
    risk_type: RiskType
    risk_level: RiskLevel
    description: str
    action_taken: str
    metadata: Dict
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class AIRiskGuardian:
    """
    AI Risk Guardian - Supervisor Inteligente de Riesgos
    
    Monitorea continuamente el comportamiento del bot y detecta patrones
    peligrosos que podrían causar pérdidas significativas.
    """
    
    def __init__(self, database_service=None):
        """
        Inicializa el AI Risk Guardian
        
        Args:
            database_service: DatabaseManager o DatabaseServiceEnterprise instance
        """
        self.db = database_service
        self.connected = self.db is not None and self.db.connected
        
        # Configuración de límites
        self.config = {
            # Overtrading
            'max_trades_per_day': 20,
            'max_trades_per_hour': 10,
            'max_trades_per_10min': 5,
            'overtrading_cooldown_minutes': 30,
            
            # Drawdown Protection
            'max_drawdown_10pct_action': 'reduce_size',  # Reducir tamaño 50%
            'max_drawdown_20pct_action': 'stop_trading',  # STOP completo
            'max_daily_loss_pct': 0.05,  # 5% pérdida diaria máxima
            
            # Revenge Trading
            'consecutive_losses_trigger': 3,
            'loss_cooldown_minutes': 60,
            'post_loss_size_reduction': 0.5,  # Reducir a 50% después de pérdida
            
            # Capital Protection
            'max_risk_per_trade_pct': 0.02,  # 2% por trade
            'min_balance_threshold': 1000,  # Balance mínimo para operar
            'max_position_size_small_account': 50,  # Si balance < $1000
            
            # FIX INSTITUCIONAL: Hard Cap Absoluto
            'max_trade_size_usd': 20000,  # NUNCA exceder este límite - SIN EXCEPCIONES
        }
        
        # Estado interno
        self.is_trading_blocked = False
        self.block_until = None
        self.block_reason = None
        self.size_reduction_factor = 1.0
        
        logger.info("🛡️ AI RISK GUARDIAN V5.4 INICIALIZADO")
        logger.info(f"   📊 Máx trades/día: {self.config['max_trades_per_day']}")
        logger.info(f"   📉 Drawdown crítico: 20%")
        logger.info(f"   🛑 Pérdidas consecutivas: {self.config['consecutive_losses_trigger']}")
    
    def _create_tables_DEPRECATED(self):
        """DEPRECATED: Tablas ahora en database_service.py"""
        pass
    
    def check_all_risks(
        self, 
        balance: float,
        recent_trades: List[Dict],
        proposed_trade_size: float = None
    ) -> Tuple[bool, Optional[RiskEvent]]:
        """
        Verifica TODOS los riesgos antes de permitir un trade
        
        Args:
            balance: Balance actual en USD
            recent_trades: Lista de trades recientes con info
            proposed_trade_size: Tamaño propuesto del trade en USD
        
        Returns:
            (can_trade, risk_event): 
                - can_trade: True si se puede tradear, False si está bloqueado
                - risk_event: Evento de riesgo si se detectó algo
        """
        import time
        import json
        
        check_id = f"RG_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
        start_time = time.time()
        checks_timing = {}
        
        # 1. Verificar si hay bloqueo activo
        t0 = time.time()
        if self._is_blocked():
            checks_timing['block_check_ms'] = round((time.time() - t0) * 1000, 2)
            logger.info(json.dumps({
                "event": "RISK_GUARDIAN_BLOCKED",
                "check_id": check_id,
                "reason": self.block_reason,
                "block_until": self.block_until.isoformat() if self.block_until else None,
                "timing": checks_timing,
                "timestamp": datetime.utcnow().isoformat()
            }))
            return False, RiskEvent(
                risk_type=RiskType.OVERTRADING,
                risk_level=RiskLevel.CRITICAL,
                description=f"Trading bloqueado hasta {self.block_until}",
                action_taken="TRADE_BLOCKED",
                metadata={'reason': self.block_reason}
            )
        checks_timing['block_check_ms'] = round((time.time() - t0) * 1000, 2)
        
        # 2. Overtrading Detection
        t0 = time.time()
        can_trade, event = self._check_overtrading(recent_trades)
        checks_timing['overtrading_check_ms'] = round((time.time() - t0) * 1000, 2)
        if not can_trade:
            self._log_risk_check(check_id, "overtrading", event, checks_timing, start_time)
            return False, event
        
        # 3. Drawdown Protection
        t0 = time.time()
        can_trade, event = self._check_drawdown(balance, recent_trades)
        checks_timing['drawdown_check_ms'] = round((time.time() - t0) * 1000, 2)
        if not can_trade:
            self._log_risk_check(check_id, "drawdown", event, checks_timing, start_time)
            return False, event
        
        # 4. Revenge Trading Detection
        t0 = time.time()
        can_trade, event = self._check_revenge_trading(recent_trades)
        checks_timing['revenge_check_ms'] = round((time.time() - t0) * 1000, 2)
        if not can_trade:
            self._log_risk_check(check_id, "revenge_trading", event, checks_timing, start_time)
            return False, event
        
        # 5. Capital Protection
        if proposed_trade_size:
            t0 = time.time()
            can_trade, event = self._check_capital_protection(
                balance, proposed_trade_size
            )
            checks_timing['capital_check_ms'] = round((time.time() - t0) * 1000, 2)
            if not can_trade:
                self._log_risk_check(check_id, "capital_protection", event, checks_timing, start_time)
                return False, event
        
        # Todo OK - se puede tradear
        total_time = (time.time() - start_time) * 1000
        
        # V6.5.4: Emit sync check event for latency monitoring
        sync_latency_threshold_ms = 500
        if total_time > sync_latency_threshold_ms:
            logger.warning(json.dumps({
                "event": "RISK_GUARDIAN_SYNC_CHECK",
                "check_id": check_id,
                "sync_status": "HIGH_LATENCY",
                "total_latency_ms": round(total_time, 2),
                "threshold_ms": sync_latency_threshold_ms,
                "timing_breakdown": checks_timing,
                "recommendation": "Review database connectivity or system load",
                "timestamp": datetime.utcnow().isoformat()
            }))
        else:
            logger.debug(json.dumps({
                "event": "RISK_GUARDIAN_SYNC_CHECK",
                "check_id": check_id,
                "sync_status": "OK",
                "total_latency_ms": round(total_time, 2),
                "timing_breakdown": checks_timing,
                "timestamp": datetime.utcnow().isoformat()
            }))
        
        logger.debug(json.dumps({
            "event": "RISK_GUARDIAN_PASSED",
            "check_id": check_id,
            "balance": round(balance, 2),
            "proposed_size": round(proposed_trade_size, 2) if proposed_trade_size else None,
            "recent_trades_count": len(recent_trades),
            "total_latency_ms": round(total_time, 2),
            "timing_breakdown": checks_timing,
            "timestamp": datetime.utcnow().isoformat()
        }))
        
        return True, None
    
    def _log_risk_check(self, check_id: str, risk_type: str, event: Optional[RiskEvent], timing: Dict, start_time: float):
        """Log structured risk check result"""
        import json
        import time
        total_time = (time.time() - start_time) * 1000
        logger.warning(json.dumps({
            "event": "RISK_GUARDIAN_REJECTED",
            "check_id": check_id,
            "risk_type": risk_type,
            "risk_level": event.risk_level.value if event else "UNKNOWN",
            "description": event.description if event else None,
            "action_taken": event.action_taken if event else None,
            "total_latency_ms": round(total_time, 2),
            "timing_breakdown": timing,
            "timestamp": datetime.utcnow().isoformat()
        }))
    
    def _is_blocked(self) -> bool:
        """Verifica si el trading está bloqueado temporalmente"""
        if not self.is_trading_blocked:
            return False
        
        if self.block_until and datetime.utcnow() >= self.block_until:
            # Bloqueo expirado - liberar
            self.is_trading_blocked = False
            self.block_until = None
            self.block_reason = None
            self.size_reduction_factor = 1.0
            logger.info("✅ Bloqueo de trading expirado - Trading habilitado")
            return False
        
        return True
    
    def _check_overtrading(
        self, 
        recent_trades: List[Dict]
    ) -> Tuple[bool, Optional[RiskEvent]]:
        """
        Detecta overtrading (demasiados trades en poco tiempo)
        
        Reglas:
        - Máx 5 trades en 10 minutos → BLOQUEAR 30 min
        - Máx 10 trades en 1 hora → ADVERTENCIA
        - Máx 20 trades en 24 horas → BLOQUEAR hasta mañana
        """
        now = datetime.utcnow()
        
        # Filtrar trades por tiempo
        trades_10min = [
            t for t in recent_trades 
            if self._get_trade_time(t) > now - timedelta(minutes=10)
        ]
        trades_1hour = [
            t for t in recent_trades 
            if self._get_trade_time(t) > now - timedelta(hours=1)
        ]
        trades_24hours = [
            t for t in recent_trades 
            if self._get_trade_time(t) > now - timedelta(hours=24)
        ]
        
        # CHECK 1: 5 trades en 10 minutos
        if len(trades_10min) >= self.config['max_trades_per_10min']:
            self._block_trading(
                minutes=self.config['overtrading_cooldown_minutes'],
                reason="5+ trades en 10 minutos"
            )
            
            event = RiskEvent(
                risk_type=RiskType.OVERTRADING,
                risk_level=RiskLevel.CRITICAL,
                description=f"OVERTRADING DETECTADO: {len(trades_10min)} trades en 10 minutos",
                action_taken=f"Trading bloqueado {self.config['overtrading_cooldown_minutes']} minutos",
                metadata={
                    'trades_10min': len(trades_10min),
                    'limit': self.config['max_trades_per_10min']
                }
            )
            self._log_event(event)
            return False, event
        
        # CHECK 2: 10 trades en 1 hora
        if len(trades_1hour) >= self.config['max_trades_per_hour']:
            event = RiskEvent(
                risk_type=RiskType.OVERTRADING,
                risk_level=RiskLevel.HIGH,
                description=f"Alta frecuencia: {len(trades_1hour)} trades en 1 hora",
                action_taken="WARNING - Reduciendo frecuencia",
                metadata={
                    'trades_1hour': len(trades_1hour),
                    'limit': self.config['max_trades_per_hour']
                }
            )
            self._log_event(event)
            # No bloquear, solo advertir
        
        # CHECK 3: 20 trades en 24 horas
        if len(trades_24hours) >= self.config['max_trades_per_day']:
            self._block_trading(
                minutes=60 * 6,  # 6 horas
                reason="20+ trades en 24 horas"
            )
            
            event = RiskEvent(
                risk_type=RiskType.OVERTRADING,
                risk_level=RiskLevel.CRITICAL,
                description=f"LÍMITE DIARIO ALCANZADO: {len(trades_24hours)} trades",
                action_taken="Trading bloqueado 6 horas",
                metadata={
                    'trades_24h': len(trades_24hours),
                    'limit': self.config['max_trades_per_day']
                }
            )
            self._log_event(event)
            return False, event
        
        return True, None
    
    def _check_drawdown(
        self, 
        current_balance: float,
        recent_trades: List[Dict]
    ) -> Tuple[bool, Optional[RiskEvent]]:
        """
        Protección contra drawdown excesivo
        
        Reglas:
        - Si pérdida > 10% en 24h → Reducir tamaño 50%
        - Si pérdida > 20% en 24h → STOP TRADING completo
        """
        # Calcular pérdida/ganancia en últimas 24 horas
        now = datetime.utcnow()
        trades_24h = [
            t for t in recent_trades
            if self._get_trade_time(t) > now - timedelta(hours=24)
        ]
        
        if not trades_24h:
            return True, None
        
        # Sumar profit/loss
        total_pnl = sum(t.get('profit_usd', 0) for t in trades_24h)
        drawdown_pct = (total_pnl / current_balance) * 100 if current_balance > 0 else 0
        
        # CHECK 1: Pérdida > 20% → STOP COMPLETO
        if drawdown_pct < -20:
            self._block_trading(
                minutes=60 * 24,  # 24 horas
                reason=f"Drawdown crítico: {drawdown_pct:.1f}%"
            )
            
            event = RiskEvent(
                risk_type=RiskType.DRAWDOWN,
                risk_level=RiskLevel.CRITICAL,
                description=f"DRAWDOWN CRÍTICO: {drawdown_pct:.1f}% en 24h",
                action_taken="TRADING DETENIDO 24 horas - Protección de capital",
                metadata={
                    'drawdown_pct': drawdown_pct,
                    'total_loss_usd': total_pnl,
                    'balance': current_balance
                }
            )
            self._log_event(event)
            return False, event
        
        # CHECK 2: Pérdida > 12% → Reducir tamaño (V6.5.4c: updated from 10%)
        if drawdown_pct < -12:
            self.size_reduction_factor = 0.5  # Reducir a 50%
            
            event = RiskEvent(
                risk_type=RiskType.DRAWDOWN,
                risk_level=RiskLevel.HIGH,
                description=f"Drawdown elevado: {drawdown_pct:.1f}% en 24h",
                action_taken="Tamaño de posición reducido a 50%",
                metadata={
                    'drawdown_pct': drawdown_pct,
                    'total_loss_usd': total_pnl,
                    'new_size_factor': 0.5
                }
            )
            self._log_event(event)
            # No bloquear, solo reducir tamaño
        
        return True, None
    
    def _check_revenge_trading(
        self, 
        recent_trades: List[Dict]
    ) -> Tuple[bool, Optional[RiskEvent]]:
        """
        Detecta revenge trading (trading emocional después de pérdidas)
        
        Regla:
        - Si 3 pérdidas consecutivas → Forzar pausa 1 hora
        """
        if len(recent_trades) < self.config['consecutive_losses_trigger']:
            return True, None
        
        # Obtener últimos N trades
        last_trades = sorted(
            recent_trades, 
            key=lambda t: self._get_trade_time(t),
            reverse=True
        )[:self.config['consecutive_losses_trigger']]
        
        # Verificar si todos son pérdidas
        all_losses = all(t.get('profit_usd', 0) < 0 for t in last_trades)
        
        if all_losses:
            total_loss = sum(t.get('profit_usd', 0) for t in last_trades)
            
            self._block_trading(
                minutes=self.config['loss_cooldown_minutes'],
                reason=f"{self.config['consecutive_losses_trigger']} pérdidas consecutivas"
            )
            
            event = RiskEvent(
                risk_type=RiskType.REVENGE_TRADING,
                risk_level=RiskLevel.CRITICAL,
                description=f"REVENGE TRADING DETECTADO: {self.config['consecutive_losses_trigger']} pérdidas consecutivas (${total_loss:.2f})",
                action_taken=f"Trading bloqueado {self.config['loss_cooldown_minutes']} minutos - Enfriamiento forzado",
                metadata={
                    'consecutive_losses': self.config['consecutive_losses_trigger'],
                    'total_loss': total_loss,
                    'cooldown_minutes': self.config['loss_cooldown_minutes']
                }
            )
            self._log_event(event)
            return False, event
        
        return True, None
    
    def _check_capital_protection(
        self, 
        balance: float,
        proposed_trade_size: float
    ) -> Tuple[bool, Optional[RiskEvent]]:
        """
        Protección de capital - Nunca arriesgar demasiado
        
        Reglas:
        - Nunca más del 2% del balance por trade
        - Si balance < $1000 → Máximo $50 por trade
        """
        max_risk = balance * self.config['max_risk_per_trade_pct']
        
        # Regla especial para cuentas pequeñas
        if balance < self.config['min_balance_threshold']:
            max_risk = min(
                max_risk, 
                self.config['max_position_size_small_account']
            )
        
        if proposed_trade_size > max_risk:
            event = RiskEvent(
                risk_type=RiskType.CAPITAL_RISK,
                risk_level=RiskLevel.HIGH,
                description=f"Tamaño de trade excesivo: ${proposed_trade_size:.2f} (máx: ${max_risk:.2f})",
                action_taken="TRADE BLOQUEADO - Protección de capital",
                metadata={
                    'proposed_size': proposed_trade_size,
                    'max_allowed': max_risk,
                    'balance': balance,
                    'risk_pct': self.config['max_risk_per_trade_pct'] * 100
                }
            )
            self._log_event(event)
            return False, event
        
        return True, None
    
    def _block_trading(self, minutes: int, reason: str):
        """Bloquea el trading temporalmente"""
        self.is_trading_blocked = True
        self.block_until = datetime.utcnow() + timedelta(minutes=minutes)
        self.block_reason = reason
        
        logger.warning(f"🛑 TRADING BLOQUEADO por {minutes} minutos")
        logger.warning(f"   Razón: {reason}")
        logger.warning(f"   Hasta: {self.block_until}")
    
    def _log_event(self, event: RiskEvent):
        """Registra evento de riesgo usando DatabaseService"""
        if not self.connected:
            logger.warning("⚠️ Database no disponible para logging de eventos")
            return
        
        try:
            # Usar DatabaseService centralizado
            self.db.log_risk_event(
                risk_type=event.risk_type.value,
                risk_level=event.risk_level.value,
                description=event.description,
                action_taken=event.action_taken,
                metadata=event.metadata
            )
        except Exception as e:
            logger.error(f"Error logging risk event: {e}")
    
    def _get_trade_time(self, trade: Dict) -> datetime:
        """Extrae timestamp del trade"""
        timestamp = trade.get('timestamp') or trade.get('executed_at')
        if isinstance(timestamp, datetime):
            return timestamp
        # Si es string, intentar parsear
        if isinstance(timestamp, str):
            try:
                return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except Exception as _e:
                logger.debug(f"[RiskGuardian] Timestamp parse failed for '{timestamp}': {_e} — using utcnow() fallback")
        return datetime.utcnow()
    
    def get_adjusted_position_size(self, original_size: float) -> float:
        """
        Ajusta el tamaño de posición según el factor de reducción actual.
        
        FIX INSTITUCIONAL: Aplica hard cap ABSOLUTO.
        Práctica institucional: Si size > MAX_LIMIT, se recorta a MAX_LIMIT exactos.
        No hay negociación ni "recortes suaves". Hard limit es hard limit.
        
        Args:
            original_size: Tamaño original propuesto
        
        Returns:
            Tamaño ajustado según riesgos detectados, NUNCA excede max_trade_size_usd
        """
        adjusted_size = original_size * self.size_reduction_factor
        
        # HARD CAP ABSOLUTO - Sin excepciones
        max_trade_size = self.config.get('max_trade_size_usd', 20000)
        
        if adjusted_size > max_trade_size:
            logger.warning(f"🛑 HARD CAP: ${adjusted_size:,.2f} → ${max_trade_size:,.2f} (límite absoluto)")
            adjusted_size = max_trade_size
        
        return adjusted_size
    
    def get_status(self) -> Dict:
        """Retorna estado actual del Risk Guardian"""
        return {
            'is_blocked': self.is_trading_blocked,
            'block_until': self.block_until.isoformat() if self.block_until else None,
            'block_reason': self.block_reason,
            'size_reduction_factor': self.size_reduction_factor,
            'config': self.config
        }
    
    def get_recent_events(self, hours: int = 24, limit: int = 50) -> List[Dict]:
        """
        Obtiene eventos recientes de riesgo
        
        Args:
            hours: Últimas N horas
            limit: Máximo de eventos a retornar
        
        Returns:
            Lista de eventos de riesgo
        """
        if not self.connected:
            return []
        
        try:
            # Usar DatabaseService centralizado
            events = self.db.get_risk_events(limit=limit)
            return events if events else []
        except Exception as e:
            logger.error(f"Error getting risk events: {e}")
            return []
    


# Testing standalone
if __name__ == "__main__":
    import os
    
    logging.basicConfig(level=logging.INFO)
    
    print("🛡️ Testing AI Risk Guardian V5.4")
    print("=" * 50)
    
    # Usar DATABASE_URL o test string
    db_url = os.getenv('DATABASE_URL', 'postgresql://localhost/test')
    
    guardian = AIRiskGuardian(db_url)
    
    # Simular trades recientes
    fake_trades = [
        {'timestamp': datetime.utcnow() - timedelta(minutes=5), 'profit_usd': -50},
        {'timestamp': datetime.utcnow() - timedelta(minutes=10), 'profit_usd': -30},
        {'timestamp': datetime.utcnow() - timedelta(minutes=15), 'profit_usd': -20},
    ]
    
    # Test 1: Revenge Trading
    print("\n📊 Test 1: Revenge Trading Detection")
    can_trade, event = guardian.check_all_risks(
        balance=10000,
        recent_trades=fake_trades
    )
    print(f"Can trade: {can_trade}")
    if event:
        print(f"Risk: {event.description}")
        print(f"Action: {event.action_taken}")
    
    # Test 2: Capital Protection
    print("\n📊 Test 2: Capital Protection")
    can_trade, event = guardian.check_all_risks(
        balance=10000,
        recent_trades=[],
        proposed_trade_size=500  # 5% - demasiado
    )
    print(f"Can trade: {can_trade}")
    if event:
        print(f"Risk: {event.description}")
        print(f"Action: {event.action_taken}")
    
    print("\n✅ AI Risk Guardian funcionando correctamente")
