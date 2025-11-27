"""
OMNIX V6.0 ULTRA - Circuit Breaker
==================================
Sistema de bloqueo automático de trading.

Funciones principales:
- Activar/desactivar trading automáticamente
- Cooldown periods después de violaciones
- Override manual para administradores
- Estado persistente en base de datos

Creado: Nov 27, 2025
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
    
    def __init__(self, database_service=None, config: RiskConfig = None):
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        self.db = database_service
        self.config = config or RiskConfig.from_env()
        
        self._halt_status: Dict[str, HaltStatus] = {}
        self._halt_history: Dict[str, List[HaltStatus]] = {}
        
        self._initialized = True
        logger.info("🔌 CircuitBreaker inicializado - Protección automática activa")
        logger.info(f"   ⏱️ Cooldown default: {self.config.halt_cooldown_minutes} minutos")
        logger.info(f"   🔒 Auto-halt: {'Activado' if self.config.enable_auto_halt else 'Desactivado'}")
    
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
            'halted_users': halted_users
        }
