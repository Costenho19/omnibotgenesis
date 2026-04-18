#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔄 ALGORITHMIC ROLLBACK PROTOCOL (ARP)
OMNIX INSTITUTIONAL+ - Protocolo de Rollback Automático

Este módulo implementa auto-revert de configuración cuando se detecta
drawdown excesivo después de un deploy.

ARQUITECTURA:
    Deploy → Snapshot Config → Monitor Drawdown → Auto-Revert si necesario

REGLAS:
    - Si drawdown > 1% en las primeras 24h post-deploy → Auto-revert
    - Si drawdown > 0.5% en la primera hora → Warning + Preparar revert
    - Snapshots de configuración guardados antes de cada deploy

Harold Nunes - OMNIX INSTITUTIONAL+
"""

import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)

SNAPSHOTS_DIR = Path("config_snapshots")
CURRENT_CONFIG_FILE = SNAPSHOTS_DIR / "current_config.json"
DEPLOY_TIMESTAMP_FILE = SNAPSHOTS_DIR / "last_deploy.json"


@dataclass
class ConfigSnapshot:
    """Snapshot de configuración del sistema"""
    timestamp: str
    trading_profile: str
    max_aggression: float
    min_confidence: float
    max_daily_loss_pct: float
    max_position_pct: float
    coherence_thresholds: Dict[str, float]
    description: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConfigSnapshot':
        return cls(**data)


@dataclass 
class DeployInfo:
    """Información del último deploy"""
    timestamp: str
    initial_balance: float
    config_snapshot_file: str
    description: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DeployInfo':
        return cls(**data)


@dataclass
class RollbackResult:
    """Resultado de verificación de rollback"""
    rollback_triggered: bool
    warning_triggered: bool
    drawdown_pct: float
    hours_since_deploy: float
    action: str
    message: str


class AlgorithmicRollbackProtocol:
    """
    🔄 ARP - Algorithmic Rollback Protocol
    
    Protocolo automático para detectar y revertir cambios problemáticos.
    Respuesta directa a la vulnerabilidad axiomática identificada:
    "¿Cuál es el protocolo hard-coded de rollback si un cambio causa pérdidas?"
    
    Este módulo proporciona:
    1. Snapshots automáticos antes de cada deploy
    2. Monitoreo de drawdown post-deploy
    3. Auto-revert si se exceden umbrales
    4. Logging completo para auditoría
    """
    
    def __init__(self,
                 drawdown_threshold_1h: float = 0.005,  # 0.5% en 1 hora
                 drawdown_threshold_24h: float = 0.01,  # 1% en 24 horas
                 auto_revert_enabled: bool = True):
        """
        Inicializa el ARP.
        
        Args:
            drawdown_threshold_1h: Umbral de drawdown para warning (1 hora)
            drawdown_threshold_24h: Umbral de drawdown para auto-revert (24 horas)
            auto_revert_enabled: Si True, ejecuta auto-revert automáticamente
        """
        self.drawdown_threshold_1h = drawdown_threshold_1h
        self.drawdown_threshold_24h = drawdown_threshold_24h
        self.auto_revert_enabled = auto_revert_enabled
        
        self._ensure_snapshots_dir()
        self._current_deploy: Optional[DeployInfo] = None
        self._load_deploy_info()
        
        logger.info("=" * 70)
        logger.info("🔄 ALGORITHMIC ROLLBACK PROTOCOL (ARP) V6.5.4 INITIALIZED")
        logger.info(f"   ⚠️ Warning threshold (1h): {drawdown_threshold_1h*100:.2f}%")
        logger.info(f"   🚨 Auto-revert threshold (24h): {drawdown_threshold_24h*100:.2f}%")
        logger.info(f"   🔧 Auto-revert enabled: {auto_revert_enabled}")
        logger.info("=" * 70)
    
    def _ensure_snapshots_dir(self):
        """Asegura que el directorio de snapshots exista"""
        SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    
    def _load_deploy_info(self):
        """Carga información del último deploy"""
        try:
            if DEPLOY_TIMESTAMP_FILE.exists():
                with open(DEPLOY_TIMESTAMP_FILE, 'r') as f:
                    data = json.load(f)
                    self._current_deploy = DeployInfo.from_dict(data)
                    logger.info(f"📦 Deploy info loaded: {self._current_deploy.timestamp}")
        except Exception as e:
            logger.warning(f"Could not load deploy info: {e}")
            self._current_deploy = None
    
    def create_pre_deploy_snapshot(self, 
                                    current_config: Dict[str, Any],
                                    description: str = "Pre-deploy snapshot") -> str:
        """
        Crea un snapshot de la configuración actual ANTES de un deploy.
        
        Args:
            current_config: Configuración actual del sistema
            description: Descripción del snapshot
            
        Returns:
            Path al archivo de snapshot creado
        """
        timestamp = datetime.utcnow().isoformat()
        snapshot = ConfigSnapshot(
            timestamp=timestamp,
            trading_profile=current_config.get('trading_profile', 'UNKNOWN'),
            max_aggression=current_config.get('max_aggression', 3.0),
            min_confidence=current_config.get('min_confidence', 0.6),
            max_daily_loss_pct=current_config.get('max_daily_loss_pct', 0.08),
            max_position_pct=current_config.get('max_position_pct', 0.12),
            coherence_thresholds=current_config.get('coherence_thresholds', {}),
            description=description
        )
        
        filename = f"snapshot_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = SNAPSHOTS_DIR / filename
        
        with open(filepath, 'w') as f:
            json.dump(snapshot.to_dict(), f, indent=2)
        
        logger.info(f"📸 Pre-deploy snapshot created: {filepath}")
        return str(filepath)
    
    def register_deploy(self, 
                        initial_balance: float,
                        snapshot_file: str,
                        description: str = "New deployment") -> DeployInfo:
        """
        Registra un nuevo deploy para monitoreo.
        
        Args:
            initial_balance: Balance al momento del deploy
            snapshot_file: Archivo de snapshot pre-deploy
            description: Descripción del deploy
            
        Returns:
            DeployInfo registrado
        """
        deploy = DeployInfo(
            timestamp=datetime.utcnow().isoformat(),
            initial_balance=initial_balance,
            config_snapshot_file=snapshot_file,
            description=description
        )
        
        self._current_deploy = deploy
        
        with open(DEPLOY_TIMESTAMP_FILE, 'w') as f:
            json.dump(deploy.to_dict(), f, indent=2)
        
        logger.info(f"🚀 Deploy registered: {description}")
        logger.info(f"   💰 Initial balance: ${initial_balance:,.2f}")
        logger.info(f"   📸 Snapshot: {snapshot_file}")
        
        return deploy
    
    def check_rollback_needed(self, 
                               current_balance: float) -> RollbackResult:
        """
        Verifica si se necesita un rollback basado en el drawdown post-deploy.
        
        Args:
            current_balance: Balance actual
            
        Returns:
            RollbackResult con el estado del check
        """
        if not self._current_deploy:
            return RollbackResult(
                rollback_triggered=False,
                warning_triggered=False,
                drawdown_pct=0.0,
                hours_since_deploy=0.0,
                action='NO_ACTION',
                message='No deploy registered'
            )
        
        deploy_time = datetime.fromisoformat(self._current_deploy.timestamp)
        hours_since = (datetime.utcnow() - deploy_time).total_seconds() / 3600
        
        initial = self._current_deploy.initial_balance
        drawdown = (initial - current_balance) / initial if initial > 0 else 0
        drawdown_pct = max(0, drawdown)
        
        if hours_since > 24:
            return RollbackResult(
                rollback_triggered=False,
                warning_triggered=False,
                drawdown_pct=drawdown_pct,
                hours_since_deploy=hours_since,
                action='MONITORING_COMPLETE',
                message='Post-deploy monitoring period (24h) completed'
            )
        
        if drawdown_pct >= self.drawdown_threshold_24h:
            message = f"Drawdown {drawdown_pct*100:.2f}% exceeds 24h threshold {self.drawdown_threshold_24h*100:.2f}%"
            logger.error(f"🚨 ARP ALERT: {message}")
            return RollbackResult(
                rollback_triggered=True,
                warning_triggered=False,
                drawdown_pct=drawdown_pct,
                hours_since_deploy=hours_since,
                action='AUTO_REVERT' if self.auto_revert_enabled else 'MANUAL_REVIEW_REQUIRED',
                message=message
            )
        
        if hours_since <= 1 and drawdown_pct >= self.drawdown_threshold_1h:
            message = f"Drawdown {drawdown_pct*100:.2f}% exceeds 1h threshold {self.drawdown_threshold_1h*100:.2f}%"
            logger.warning(f"⚠️ ARP WARNING: {message}")
            return RollbackResult(
                rollback_triggered=False,
                warning_triggered=True,
                drawdown_pct=drawdown_pct,
                hours_since_deploy=hours_since,
                action='WARNING',
                message=message
            )
        
        return RollbackResult(
            rollback_triggered=False,
            warning_triggered=False,
            drawdown_pct=drawdown_pct,
            hours_since_deploy=hours_since,
            action='CONTINUE',
            message='Within acceptable parameters'
        )
    
    def execute_rollback(self) -> Dict[str, Any]:
        """
        Ejecuta el rollback a la configuración anterior.
        
        Returns:
            Dict con resultado del rollback:
            - success: bool
            - restored_config: Dict or None
            - message: str
        """
        if not self._current_deploy:
            return {
                'success': False,
                'restored_config': None,
                'message': 'No deploy to rollback from'
            }
        
        snapshot_file = self._current_deploy.config_snapshot_file
        
        try:
            if not os.path.exists(snapshot_file):
                return {
                    'success': False,
                    'restored_config': None,
                    'message': f'Snapshot file not found: {snapshot_file}'
                }
            
            with open(snapshot_file, 'r') as f:
                snapshot_data = json.load(f)
            
            snapshot = ConfigSnapshot.from_dict(snapshot_data)
            
            with open(CURRENT_CONFIG_FILE, 'w') as f:
                json.dump(snapshot.to_dict(), f, indent=2)
            
            rollback_log = {
                'timestamp': datetime.utcnow().isoformat(),
                'action': 'ROLLBACK_EXECUTED',
                'from_deploy': self._current_deploy.timestamp,
                'restored_to': snapshot.timestamp,
                'trading_profile': snapshot.trading_profile
            }
            
            rollback_log_file = SNAPSHOTS_DIR / f"rollback_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            with open(rollback_log_file, 'w') as f:
                json.dump(rollback_log, f, indent=2)
            
            logger.info("=" * 70)
            logger.info("🔄 ROLLBACK EXECUTED SUCCESSFULLY")
            logger.info(f"   📸 Restored from: {snapshot_file}")
            logger.info(f"   🎯 Trading Profile: {snapshot.trading_profile}")
            logger.info(f"   📊 Max Aggression: {snapshot.max_aggression}x")
            logger.info("=" * 70)
            
            return {
                'success': True,
                'restored_config': snapshot.to_dict(),
                'message': f'Rolled back to snapshot from {snapshot.timestamp}'
            }
            
        except Exception as e:
            logger.error(f"❌ Rollback failed: {e}")
            return {
                'success': False,
                'restored_config': None,
                'message': f'Rollback failed: {str(e)}'
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado actual del ARP"""
        return {
            'enabled': self.auto_revert_enabled,
            'threshold_1h': self.drawdown_threshold_1h,
            'threshold_24h': self.drawdown_threshold_24h,
            'current_deploy': self._current_deploy.to_dict() if self._current_deploy else None,
            'snapshots_dir': str(SNAPSHOTS_DIR)
        }


_arp_instance: Optional[AlgorithmicRollbackProtocol] = None

def get_arp_instance() -> AlgorithmicRollbackProtocol:
    """Obtiene o crea la instancia singleton del ARP"""
    global _arp_instance
    if _arp_instance is None:
        _arp_instance = AlgorithmicRollbackProtocol()
    return _arp_instance
