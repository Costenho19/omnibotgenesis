"""
OMNIX V6.2 ULTRA - Circuit Breaker (Memory-Enhanced)
=====================================================
Sistema de bloqueo automático de trading con
detección predictiva basada en memoria Non-Markoviana.

Funciones principales:
- Activar/desactivar trading automáticamente
- Cooldown periods después de violaciones
- Override manual para administradores
- Estado persistente en base de datos
- NUEVO V6.2: Trigger por incoherencia de memoria temporal

Creado: Nov 27, 2025
Actualizado: Nov 29, 2025 - Memory-Enhanced Risk Management
"""

import logging
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from omnix_services.risk_management.risk_models import (
    RiskSeverity, RiskAction, RiskBreach, RiskConfig
)

logger = logging.getLogger(__name__)


class HaltReason(Enum):
    """Razones para detener el trading"""
    DAILY_LOSS_EXCEEDED = 'daily_loss_exceeded'
    DRAWDOWN_EXCEEDED = 'drawdown_exceeded'
    MANUAL_HALT = 'manual_halt'
    VOLATILITY_HIGH = 'volatility_high'
    SYSTEM_ERROR = 'system_error'
    CONSECUTIVE_LOSSES = 'consecutive_losses'
    RISK_SCORE_HIGH = 'risk_score_high'
    MEMORY_INCOHERENCE = 'memory_incoherence'
    REGIME_TRANSITION = 'regime_transition'


@dataclass
class HaltStatus:
    """Estado del circuit breaker"""
    is_halted: bool = False
    reason: Optional[HaltReason] = None
    message: str = ''
    halted_at: Optional[datetime] = None
    resume_at: Optional[datetime] = None
    halted_by: str = 'system'
    cooldown_remaining_minutes: int = 0
    can_override: bool = True
    
    def to_dict(self) -> Dict:
        return {
            'is_halted': self.is_halted,
            'reason': self.reason.value if self.reason else None,
            'message': self.message,
            'halted_at': self.halted_at.isoformat() if self.halted_at else None,
            'resume_at': self.resume_at.isoformat() if self.resume_at else None,
            'halted_by': self.halted_by,
            'cooldown_remaining_minutes': self.cooldown_remaining_minutes,
            'can_override': self.can_override
        }


class CircuitBreaker:
    """
    Circuit Breaker para protección de trading.
    
    Detiene automáticamente el trading cuando se violan límites críticos.
    """
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, database_service=None, config: RiskConfig = None,
                 memory_adapter=None):
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        self.db = database_service
        self.config = config or RiskConfig.from_env()
        
        self._halt_status: Dict[str, HaltStatus] = {}
        self._halt_history: Dict[str, List[HaltStatus]] = {}
        
        self._memory_adapter = memory_adapter
        self._enable_memory_halt = True
        self._memory_halt_cooldown = 30
        
        self._initialized = True
        logger.info("🔌 CircuitBreaker V6.2 inicializado - Protección automática activa")
        logger.info(f"   ⏱️ Cooldown default: {self.config.halt_cooldown_minutes} minutos")
        logger.info(f"   🔒 Auto-halt: {'Activado' if self.config.enable_auto_halt else 'Desactivado'}")
        logger.info(f"   🧠 Memory-halt: {'Activo' if memory_adapter else 'No disponible'}")
    
    def is_trading_halted(self, user_id: str) -> bool:
        """Verificar si el trading está detenido para un usuario"""
        status = self.get_halt_status(user_id)
        
        if status.is_halted and status.resume_at:
            if datetime.now() >= status.resume_at:
                self._auto_resume(user_id)
                return False
        
        return status.is_halted
    
    def get_halt_status(self, user_id: str) -> HaltStatus:
        """Obtener estado actual del circuit breaker"""
        if user_id not in self._halt_status:
            status = self._load_status_from_db(user_id)
            self._halt_status[user_id] = status or HaltStatus()
        
        status = self._halt_status[user_id]
        
        if status.is_halted and status.resume_at:
            remaining = (status.resume_at - datetime.now()).total_seconds() / 60
            status.cooldown_remaining_minutes = max(0, int(remaining))
        
        return status
    
    def trigger_halt(
        self,
        user_id: str,
        reason: HaltReason,
        message: str = '',
        cooldown_minutes: Optional[int] = None,
        halted_by: str = 'system'
    ) -> HaltStatus:
        """Activar bloqueo de trading"""
        
        if not self.config.enable_auto_halt and halted_by == 'system':
            logger.warning(f"⚠️ Auto-halt desactivado, ignorando trigger para {user_id}")
            return self.get_halt_status(user_id)
        
        cooldown = cooldown_minutes or self.config.halt_cooldown_minutes
        now = datetime.now()
        resume_at = now + timedelta(minutes=cooldown)
        
        status = HaltStatus(
            is_halted=True,
            reason=reason,
            message=message or f"Trading detenido: {reason.value}",
            halted_at=now,
            resume_at=resume_at,
            halted_by=halted_by,
            cooldown_remaining_minutes=cooldown,
            can_override=True
        )
        
        self._halt_status[user_id] = status
        
        if user_id not in self._halt_history:
            self._halt_history[user_id] = []
        self._halt_history[user_id].append(status)
        
        self._save_status_to_db(user_id, status)
        
        logger.warning(f"🚨 TRADING HALTED para {user_id}")
        logger.warning(f"   Razón: {reason.value}")
        logger.warning(f"   Mensaje: {message}")
        logger.warning(f"   Reanudar a las: {resume_at.strftime('%H:%M:%S')}")
        
        return status
    
    def trigger_from_breach(self, user_id: str, breach: RiskBreach) -> Optional[HaltStatus]:
        """Activar halt desde una violación de límite"""
        
        if breach.severity != RiskSeverity.HALT:
            return None
        
        reason_map = {
            'daily_loss': HaltReason.DAILY_LOSS_EXCEEDED,
            'max_drawdown': HaltReason.DRAWDOWN_EXCEEDED,
            'volatility': HaltReason.VOLATILITY_HIGH,
        }
        
        reason = reason_map.get(
            breach.limit_type.value if hasattr(breach.limit_type, 'value') else str(breach.limit_type),
            HaltReason.RISK_SCORE_HIGH
        )
        
        return self.trigger_halt(
            user_id=user_id,
            reason=reason,
            message=breach.description,
            halted_by='limits_engine'
        )
    
    def manual_halt(
        self,
        user_id: str,
        admin_id: str,
        message: str = '',
        cooldown_minutes: int = 0
    ) -> HaltStatus:
        """Halt manual por administrador (sin cooldown automático)"""
        
        return self.trigger_halt(
            user_id=user_id,
            reason=HaltReason.MANUAL_HALT,
            message=message or f"Halt manual por admin {admin_id}",
            cooldown_minutes=cooldown_minutes if cooldown_minutes > 0 else 525600,
            halted_by=f"admin:{admin_id}"
        )
    
    def resume_trading(
        self,
        user_id: str,
        resumed_by: str = 'system',
        force: bool = False
    ) -> bool:
        """Reanudar trading"""
        
        status = self.get_halt_status(user_id)
        
        if not status.is_halted:
            logger.info(f"ℹ️ Trading ya está activo para {user_id}")
            return True
        
        if not force and not status.can_override:
            logger.warning(f"⚠️ No se puede override halt para {user_id}")
            return False
        
        if not force and status.resume_at and datetime.now() < status.resume_at:
            remaining = status.cooldown_remaining_minutes
            logger.warning(f"⚠️ Cooldown activo, quedan {remaining} minutos")
            return False
        
        self._halt_status[user_id] = HaltStatus()
        self._save_status_to_db(user_id, HaltStatus())
        
        logger.info(f"✅ Trading REANUDADO para {user_id} por {resumed_by}")
        
        return True
    
    def _auto_resume(self, user_id: str):
        """Reanudar automáticamente después del cooldown"""
        logger.info(f"⏰ Cooldown completado, reanudando trading para {user_id}")
        self.resume_trading(user_id, resumed_by='auto_cooldown', force=True)
    
    def get_halt_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Obtener historial de halts"""
        history = self._halt_history.get(user_id, [])
        return [h.to_dict() for h in history[-limit:]]
    
    def _load_status_from_db(self, user_id: str) -> Optional[HaltStatus]:
        """Cargar estado desde base de datos"""
        if not self.db:
            return None
            
        try:
            data = self.db.get_circuit_breaker_status(user_id)
            if data and data.get('is_halted'):
                return HaltStatus(
                    is_halted=data.get('is_halted', False),
                    reason=HaltReason(data['reason']) if data.get('reason') else None,
                    message=data.get('message', ''),
                    halted_at=data.get('halted_at'),
                    resume_at=data.get('resume_at'),
                    halted_by=data.get('halted_by', 'system'),
                    can_override=data.get('can_override', True)
                )
        except Exception as e:
            logger.warning(f"⚠️ Error cargando status de BD: {e}")
        
        return None
    
    def _save_status_to_db(self, user_id: str, status: HaltStatus) -> bool:
        """Guardar estado en base de datos"""
        if not self.db:
            return False
            
        try:
            return self.db.save_circuit_breaker_status(user_id, status.to_dict())
        except Exception as e:
            logger.error(f"❌ Error guardando status: {e}")
            return False
    
    def check_consecutive_losses(self, user_id: str, threshold: int = 5) -> bool:
        """Verificar pérdidas consecutivas y activar halt si necesario"""
        if not self.db:
            return False
            
        try:
            recent_trades = self.db.get_recent_trades(user_id, limit=threshold)
            if not recent_trades or len(recent_trades) < threshold:
                return False
            
            consecutive_losses = 0
            for trade in recent_trades:
                if trade.get('profit', 0) < 0:
                    consecutive_losses += 1
                else:
                    break
            
            if consecutive_losses >= threshold:
                self.trigger_halt(
                    user_id=user_id,
                    reason=HaltReason.CONSECUTIVE_LOSSES,
                    message=f"{consecutive_losses} pérdidas consecutivas detectadas",
                    halted_by='loss_detector'
                )
                return True
                
        except Exception as e:
            logger.error(f"❌ Error verificando pérdidas: {e}")
        
        return False
    
    def get_global_status(self) -> Dict[str, Any]:
        """Obtener estado global del circuit breaker"""
        halted_users = [
            uid for uid, status in self._halt_status.items() 
            if status.is_halted
        ]
        
        return {
            'timestamp': datetime.now().isoformat(),
            'auto_halt_enabled': self.config.enable_auto_halt,
            'default_cooldown_minutes': self.config.halt_cooldown_minutes,
            'total_halted_users': len(halted_users),
            'halted_users': halted_users,
            'memory_halt_enabled': self._enable_memory_halt,
            'memory_adapter_connected': self._memory_adapter is not None
        }
    
    def set_memory_adapter(self, memory_adapter) -> None:
        """Configurar adaptador de memoria después de inicialización"""
        self._memory_adapter = memory_adapter
        if memory_adapter:
            logger.info("🧠 CircuitBreaker: MemoryRiskAdapter conectado")
    
    def enable_memory_halt(self, enabled: bool = True) -> None:
        """Habilitar/deshabilitar halt por memoria"""
        self._enable_memory_halt = enabled
        logger.info(f"🧠 Memory halt: {'Activo' if enabled else 'Desactivado'}")
    
    def check_memory_risk(self, user_id: str, current_price: float) -> Optional[HaltStatus]:
        """
        Verificar si el riesgo de memoria requiere halt.
        
        Esta función evalúa las métricas del kernel Non-Markoviano
        y activa el circuit breaker si detecta condiciones críticas.
        
        Args:
            user_id: ID del usuario
            current_price: Precio actual del activo
            
        Returns:
            HaltStatus si se activó halt, None en caso contrario
        """
        if not self._enable_memory_halt or not self._memory_adapter:
            return None
        
        if self.is_trading_halted(user_id):
            return self.get_halt_status(user_id)
        
        try:
            should_halt, halt_reason = self._memory_adapter.should_trigger_circuit_breaker()
            
            if should_halt:
                memory_metrics = self._memory_adapter.compute_memory_risk(current_price)
                
                if memory_metrics.transition_risk > 80:
                    reason = HaltReason.REGIME_TRANSITION
                else:
                    reason = HaltReason.MEMORY_INCOHERENCE
                
                return self.trigger_halt(
                    user_id=user_id,
                    reason=reason,
                    message=halt_reason,
                    cooldown_minutes=self._memory_halt_cooldown,
                    halted_by='memory_adapter'
                )
            
        except Exception as e:
            logger.error(f"❌ Error verificando riesgo de memoria: {e}")
        
        return None
    
    def trigger_from_memory_risk(self, user_id: str, 
                                  risk_type: str, 
                                  risk_value: float,
                                  message: str = '') -> Optional[HaltStatus]:
        """
        Trigger manual desde análisis de memoria.
        
        Args:
            user_id: ID del usuario
            risk_type: Tipo de riesgo ('coherence', 'transition', 'divergence')
            risk_value: Valor del riesgo (0-100)
            message: Mensaje descriptivo
            
        Returns:
            HaltStatus si se activó halt, None en caso contrario
        """
        if not self.config.enable_auto_halt:
            logger.warning(f"⚠️ Auto-halt desactivado, ignorando trigger de memoria")
            return None
        
        if risk_value < 75:
            logger.debug(f"📊 Riesgo de memoria {risk_type}={risk_value:.1f}% bajo umbral crítico")
            return None
        
        reason_map = {
            'coherence': HaltReason.MEMORY_INCOHERENCE,
            'transition': HaltReason.REGIME_TRANSITION,
            'divergence': HaltReason.MEMORY_INCOHERENCE
        }
        
        reason = reason_map.get(risk_type, HaltReason.MEMORY_INCOHERENCE)
        
        if not message:
            message = f"🧠 Riesgo de memoria {risk_type} detectado: {risk_value:.1f}%"
        
        return self.trigger_halt(
            user_id=user_id,
            reason=reason,
            message=message,
            cooldown_minutes=self._memory_halt_cooldown,
            halted_by='memory_risk'
        )
    
    def get_memory_halt_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de halts por memoria"""
        memory_halts = []
        for user_id, history in self._halt_history.items():
            for halt in history:
                if halt.reason in [HaltReason.MEMORY_INCOHERENCE, HaltReason.REGIME_TRANSITION]:
                    memory_halts.append({
                        'user_id': user_id,
                        'reason': halt.reason.value,
                        'halted_at': halt.halted_at.isoformat() if halt.halted_at else None
                    })
        
        return {
            'total_memory_halts': len(memory_halts),
            'recent_halts': memory_halts[-10:],
            'memory_halt_enabled': self._enable_memory_halt,
            'memory_halt_cooldown': self._memory_halt_cooldown
        }
