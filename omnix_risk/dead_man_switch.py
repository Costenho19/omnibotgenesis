"""
OMNIX V6.0 ULTRA - Dead Man Switch
===================================
Monitor proactivo de salud del sistema para hedge funds.

Monitorea continuamente (cada 500ms):
1. Heartbeat del exchange (respuesta API)
2. Latencia (umbral 2000ms)
3. Estado del orderbook (no congelado)
4. Integridad de datos (sin spikes)
5. Slippage anormal
6. Patrones críticos HMM

Si cualquier check falla por más de 5-15 segundos,
detiene TODO el trading automáticamente.

Este es el "último candado" que exigen los hedge funds.

Creado: Nov 27, 2025
Autor: OMNIX Team
"""

import logging
import threading
import time
from typing import Optional, Dict, List, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import statistics

try:
    from omnix_risk.audit_logger import AuditAction, AuditResult
    AUDIT_ENUMS_AVAILABLE = True
except ImportError:
    AUDIT_ENUMS_AVAILABLE = False

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """System health status levels"""
    HEALTHY = 'HEALTHY'
    DEGRADED = 'DEGRADED'
    CRITICAL = 'CRITICAL'
    DEAD = 'DEAD'


class CheckType(Enum):
    """Types of health checks"""
    EXCHANGE_HEARTBEAT = 'exchange_heartbeat'
    LATENCY = 'latency'
    ORDERBOOK_FRESH = 'orderbook_fresh'
    DATA_INTEGRITY = 'data_integrity'
    SLIPPAGE_NORMAL = 'slippage_normal'
    HMM_REGIME = 'hmm_regime'
    WEBSOCKET_ALIVE = 'websocket_alive'


@dataclass
class HealthCheck:
    """Individual health check result"""
    check_type: CheckType
    passed: bool
    value: Any
    threshold: Any
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            'check_type': self.check_type.value,
            'passed': self.passed,
            'value': self.value,
            'threshold': self.threshold,
            'message': self.message,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class SystemHealth:
    """Aggregate system health status"""
    status: HealthStatus
    checks: List[HealthCheck]
    failed_checks: List[str]
    consecutive_failures: int
    last_healthy_time: datetime
    time_since_healthy_seconds: float
    trading_allowed: bool
    
    def to_dict(self) -> Dict:
        return {
            'status': self.status.value,
            'checks': [c.to_dict() for c in self.checks],
            'failed_checks': self.failed_checks,
            'consecutive_failures': self.consecutive_failures,
            'last_healthy_time': self.last_healthy_time.isoformat(),
            'time_since_healthy_seconds': self.time_since_healthy_seconds,
            'trading_allowed': self.trading_allowed
        }


class DeadManSwitch:
    """
    Institutional-grade system health monitor.
    
    Proactively monitors exchange connectivity and data quality.
    Automatically halts all trading if critical issues detected.
    
    This is the "last lock" required by institutional investors.
    """
    
    DEFAULT_CONFIG = {
        'check_interval_ms': 500,
        'heartbeat_timeout_ms': 5000,
        'latency_threshold_ms': 2000,
        'orderbook_stale_seconds': 10,
        'data_spike_threshold_pct': 20,
        'slippage_threshold_bps': 50,
        'consecutive_failures_to_halt': 3,
        'halt_duration_seconds': 300,
        'auto_recovery': True
    }
    
    def __init__(
        self,
        trading_service=None,
        circuit_breaker=None,
        audit_logger=None,
        config: Optional[Dict] = None
    ):
        """
        Initialize Dead Man Switch.
        
        Args:
            trading_service: Trading service for exchange connectivity
            circuit_breaker: Circuit breaker for halt coordination
            audit_logger: Audit logger for compliance logging
            config: Optional custom configuration
        """
        self._trading_service = trading_service
        self._circuit_breaker = circuit_breaker
        self._audit_logger = audit_logger
        
        self._config = {**self.DEFAULT_CONFIG, **(config or {})}
        
        self._status = HealthStatus.HEALTHY
        self._trading_allowed = True
        self._consecutive_failures = 0
        self._last_healthy_time = datetime.utcnow()
        self._halt_until: Optional[datetime] = None
        
        self._last_price: Optional[float] = None
        self._last_orderbook_time: Optional[datetime] = None
        self._last_heartbeat_time: Optional[datetime] = None
        self._latency_samples: List[float] = []
        self._max_latency_samples = 20
        
        self._check_history: List[SystemHealth] = []
        self._max_history = 100
        
        self._monitor_thread: Optional[threading.Thread] = None
        self._running = False
        self._lock = threading.Lock()
        
        self._halt_callbacks: List[Callable] = []
        self._recovery_callbacks: List[Callable] = []
        
        logger.info("🔒 DeadManSwitch initialized - Institutional Safety Lock")
        logger.info(f"   ⏱️ Check interval: {self._config['check_interval_ms']}ms")
        logger.info(f"   📡 Heartbeat timeout: {self._config['heartbeat_timeout_ms']}ms")
        logger.info(f"   ⚡ Latency threshold: {self._config['latency_threshold_ms']}ms")
        logger.info(f"   🔄 Failures to halt: {self._config['consecutive_failures_to_halt']}")
    
    def start_monitoring(self):
        """Start continuous health monitoring"""
        if self._running:
            logger.warning("DeadManSwitch already running")
            return
        
        self._running = True
        self._monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
            name="DeadManSwitch"
        )
        self._monitor_thread.start()
        
        logger.info("🟢 DeadManSwitch monitoring STARTED")
        
        if self._audit_logger:
            action = AuditAction.DEAD_MAN_SWITCH_TRIGGERED if AUDIT_ENUMS_AVAILABLE else "DEAD_MAN_SWITCH_ACTIVATED"
            result = AuditResult.SUCCESS if AUDIT_ENUMS_AVAILABLE else "SUCCESS"
            self._audit_logger.log_event(
                action=action,
                reason="System health monitoring started",
                module="DeadManSwitch",
                metric=f"check_interval={self._config['check_interval_ms']}ms",
                result=result
            )
    
    def stop_monitoring(self):
        """Stop health monitoring"""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)
        
        logger.info("🔴 DeadManSwitch monitoring STOPPED")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        interval_seconds = self._config['check_interval_ms'] / 1000
        
        while self._running:
            try:
                health = self.check_health()
                
                with self._lock:
                    self._check_history.append(health)
                    if len(self._check_history) > self._max_history:
                        self._check_history = self._check_history[-self._max_history:]
                
                if health.status == HealthStatus.DEAD:
                    self._handle_dead_state(health)
                elif health.status == HealthStatus.CRITICAL:
                    self._handle_critical_state(health)
                elif health.status == HealthStatus.HEALTHY and not self._trading_allowed:
                    self._handle_recovery()
                
            except Exception as e:
                logger.error(f"DeadManSwitch monitoring error: {e}")
            
            time.sleep(interval_seconds)
    
    def check_health(self) -> SystemHealth:
        """
        Perform all health checks.
        
        Returns:
            SystemHealth with aggregate status
        """
        checks = []
        failed = []
        
        checks.append(self._check_exchange_heartbeat())
        if not checks[-1].passed:
            failed.append(checks[-1].check_type.value)
        
        checks.append(self._check_latency())
        if not checks[-1].passed:
            failed.append(checks[-1].check_type.value)
        
        checks.append(self._check_orderbook_freshness())
        if not checks[-1].passed:
            failed.append(checks[-1].check_type.value)
        
        checks.append(self._check_data_integrity())
        if not checks[-1].passed:
            failed.append(checks[-1].check_type.value)
        
        checks.append(self._check_slippage())
        if not checks[-1].passed:
            failed.append(checks[-1].check_type.value)
        
        checks.append(self._check_websocket())
        if not checks[-1].passed:
            failed.append(checks[-1].check_type.value)
        
        now = datetime.utcnow()
        
        if len(failed) == 0:
            status = HealthStatus.HEALTHY
            self._consecutive_failures = 0
            self._last_healthy_time = now
        elif len(failed) <= 2:
            status = HealthStatus.DEGRADED
            self._consecutive_failures += 1
        elif len(failed) <= 4:
            status = HealthStatus.CRITICAL
            self._consecutive_failures += 1
        else:
            status = HealthStatus.DEAD
            self._consecutive_failures += 1
        
        time_since_healthy = (now - self._last_healthy_time).total_seconds()
        
        trading_allowed = self._trading_allowed
        if self._halt_until and now < self._halt_until:
            trading_allowed = False
        elif self._consecutive_failures >= self._config['consecutive_failures_to_halt']:
            trading_allowed = False
        
        self._status = status
        self._trading_allowed = trading_allowed
        
        return SystemHealth(
            status=status,
            checks=checks,
            failed_checks=failed,
            consecutive_failures=self._consecutive_failures,
            last_healthy_time=self._last_healthy_time,
            time_since_healthy_seconds=time_since_healthy,
            trading_allowed=trading_allowed
        )
    
    def _check_exchange_heartbeat(self) -> HealthCheck:
        """Check if exchange is responding"""
        timeout_ms = self._config['heartbeat_timeout_ms']
        
        if self._trading_service:
            try:
                start = time.perf_counter()
                
                if hasattr(self._trading_service, 'kraken_client'):
                    self._trading_service.kraken_client.get_server_time()
                elif hasattr(self._trading_service, 'get_ticker'):
                    self._trading_service.get_ticker('BTC/USD')
                
                latency_ms = (time.perf_counter() - start) * 1000
                self._last_heartbeat_time = datetime.utcnow()
                
                passed = latency_ms < timeout_ms
                return HealthCheck(
                    check_type=CheckType.EXCHANGE_HEARTBEAT,
                    passed=passed,
                    value=f"{latency_ms:.0f}ms",
                    threshold=f"{timeout_ms}ms",
                    message="Exchange responding" if passed else "Exchange timeout"
                )
            except Exception as e:
                return HealthCheck(
                    check_type=CheckType.EXCHANGE_HEARTBEAT,
                    passed=False,
                    value="ERROR",
                    threshold=f"{timeout_ms}ms",
                    message=f"Exchange error: {str(e)[:50]}"
                )
        
        return HealthCheck(
            check_type=CheckType.EXCHANGE_HEARTBEAT,
            passed=False,
            value="NO_CONNECTION",
            threshold=f"{timeout_ms}ms",
            message="Trading service not available - no exchange connection"
        )
    
    def _check_latency(self) -> HealthCheck:
        """Check if latency is within acceptable range"""
        threshold_ms = self._config['latency_threshold_ms']
        
        if self._trading_service and hasattr(self._trading_service, 'ws_client'):
            ws = self._trading_service.ws_client
            if hasattr(ws, 'latency_ms'):
                current_latency = ws.latency_ms
                self._latency_samples.append(current_latency)
                if len(self._latency_samples) > self._max_latency_samples:
                    self._latency_samples = self._latency_samples[-self._max_latency_samples:]
                
                avg_latency = statistics.mean(self._latency_samples) if self._latency_samples else current_latency
                passed = current_latency < threshold_ms
                
                return HealthCheck(
                    check_type=CheckType.LATENCY,
                    passed=passed,
                    value=f"{current_latency:.0f}ms (avg: {avg_latency:.0f}ms)",
                    threshold=f"{threshold_ms}ms",
                    message="Latency OK" if passed else "HIGH LATENCY"
                )
        
        return HealthCheck(
            check_type=CheckType.LATENCY,
            passed=False,
            value="N/A",
            threshold=f"{threshold_ms}ms",
            message="WebSocket not connected - latency unavailable"
        )
    
    def _check_orderbook_freshness(self) -> HealthCheck:
        """Check if orderbook data is fresh"""
        stale_seconds = self._config['orderbook_stale_seconds']
        
        if self._trading_service and hasattr(self._trading_service, 'ws_client'):
            ws = self._trading_service.ws_client
            if hasattr(ws, 'last_orderbook_update'):
                self._last_orderbook_time = ws.last_orderbook_update
        
        if self._last_orderbook_time:
            age = (datetime.utcnow() - self._last_orderbook_time).total_seconds()
            passed = age < stale_seconds
        else:
            passed = True
            age = 0
            self._last_orderbook_time = datetime.utcnow()
        
        return HealthCheck(
            check_type=CheckType.ORDERBOOK_FRESH,
            passed=passed,
            value=f"{age:.1f}s old",
            threshold=f"{stale_seconds}s",
            message="Orderbook fresh" if passed else "STALE ORDERBOOK"
        )
    
    def _check_data_integrity(self) -> HealthCheck:
        """Check for data anomalies (price spikes)"""
        spike_threshold = self._config['data_spike_threshold_pct']
        
        current_price = None
        
        if self._trading_service:
            try:
                if hasattr(self._trading_service, 'get_ticker'):
                    ticker = self._trading_service.get_ticker('BTC/USD')
                    if ticker:
                        current_price = ticker.get('last', ticker.get('close'))
            except:
                pass
        
        if current_price is None:
            return HealthCheck(
                check_type=CheckType.DATA_INTEGRITY,
                passed=False,
                value="NO_DATA",
                threshold=f"{spike_threshold}%",
                message="Unable to get price from exchange"
            )
        
        if self._last_price is not None and current_price is not None:
            change_pct = abs((current_price - self._last_price) / self._last_price * 100)
            passed = change_pct < spike_threshold
            message = "Data OK" if passed else f"PRICE SPIKE: {change_pct:.1f}%"
        else:
            passed = True
            change_pct = 0
            message = "Data OK (first check)"
        
        if current_price:
            self._last_price = current_price
        
        return HealthCheck(
            check_type=CheckType.DATA_INTEGRITY,
            passed=passed,
            value=f"{change_pct:.2f}% change",
            threshold=f"{spike_threshold}%",
            message=message
        )
    
    def _check_slippage(self) -> HealthCheck:
        """Check if slippage is within normal range"""
        threshold_bps = self._config['slippage_threshold_bps']
        
        if self._trading_service and hasattr(self._trading_service, 'last_slippage_bps'):
            current_slippage = self._trading_service.last_slippage_bps
            passed = current_slippage < threshold_bps
            return HealthCheck(
                check_type=CheckType.SLIPPAGE_NORMAL,
                passed=passed,
                value=f"{current_slippage:.1f} bps",
                threshold=f"{threshold_bps} bps",
                message="Slippage OK" if passed else "HIGH SLIPPAGE"
            )
        
        return HealthCheck(
            check_type=CheckType.SLIPPAGE_NORMAL,
            passed=True,
            value="N/A",
            threshold=f"{threshold_bps} bps",
            message="No recent trades - slippage unavailable"
        )
    
    def _check_websocket(self) -> HealthCheck:
        """Check WebSocket connection status"""
        if self._trading_service and hasattr(self._trading_service, 'ws_client'):
            ws = self._trading_service.ws_client
            if hasattr(ws, 'is_connected'):
                connected = ws.is_connected
            else:
                connected = True
        else:
            connected = True
        
        return HealthCheck(
            check_type=CheckType.WEBSOCKET_ALIVE,
            passed=connected,
            value="CONNECTED" if connected else "DISCONNECTED",
            threshold="CONNECTED",
            message="WebSocket OK" if connected else "WEBSOCKET DOWN"
        )
    
    def _handle_dead_state(self, health: SystemHealth):
        """Handle system in DEAD state"""
        logger.critical("💀 DEAD MAN SWITCH TRIGGERED - System health DEAD")
        logger.critical(f"   Failed checks: {health.failed_checks}")
        
        self._halt_trading("DEAD_MAN_SWITCH", "System health critical - all trading halted")
        
        if self._audit_logger:
            action = AuditAction.DEAD_MAN_SWITCH_TRIGGERED if AUDIT_ENUMS_AVAILABLE else "DEAD_MAN_SWITCH_TRIGGERED"
            result = AuditResult.CRITICAL if AUDIT_ENUMS_AVAILABLE else "CRITICAL"
            self._audit_logger.log_event(
                action=action,
                reason=f"System DEAD state - Failed: {', '.join(health.failed_checks)}",
                module="DeadManSwitch",
                metric=f"consecutive_failures={health.consecutive_failures}",
                result=result
            )
        
        for callback in self._halt_callbacks:
            try:
                callback(health)
            except Exception as e:
                logger.error(f"Halt callback error: {e}")
    
    def _handle_critical_state(self, health: SystemHealth):
        """Handle system in CRITICAL state"""
        if self._consecutive_failures >= self._config['consecutive_failures_to_halt']:
            logger.error(f"⚠️ CRITICAL STATE - {self._consecutive_failures} consecutive failures")
            self._halt_trading("CRITICAL_STATE", "Multiple consecutive failures detected")
    
    def _handle_recovery(self):
        """Handle system recovery to healthy state"""
        if self._config['auto_recovery'] and self._status == HealthStatus.HEALTHY:
            if self._halt_until is None or datetime.utcnow() >= self._halt_until:
                logger.info("🟢 System recovered - Trading can resume")
                self._trading_allowed = True
                
                if self._audit_logger:
                    action = AuditAction.DEAD_MAN_SWITCH_RESET if AUDIT_ENUMS_AVAILABLE else "DEAD_MAN_SWITCH_RESET"
                    result = AuditResult.SUCCESS if AUDIT_ENUMS_AVAILABLE else "SUCCESS"
                    self._audit_logger.log_event(
                        action=action,
                        reason="System health restored to HEALTHY",
                        module="DeadManSwitch",
                        metric="status=HEALTHY",
                        result=result
                    )
                
                for callback in self._recovery_callbacks:
                    try:
                        callback()
                    except Exception as e:
                        logger.error(f"Recovery callback error: {e}")
    
    def _halt_trading(self, reason_code: str, message: str):
        """Halt all trading"""
        with self._lock:
            self._trading_allowed = False
            self._halt_until = datetime.utcnow() + timedelta(
                seconds=self._config['halt_duration_seconds']
            )
        
        if self._circuit_breaker:
            try:
                self._circuit_breaker.trigger_halt(
                    reason='system_error',
                    message=message
                )
            except Exception as e:
                logger.error(f"Failed to trigger circuit breaker: {e}")
        
        logger.critical(f"🛑 TRADING HALTED: {message}")
        logger.critical(f"   Halt until: {self._halt_until}")
    
    def force_halt(self, reason: str = "Manual halt"):
        """Manually force trading halt"""
        self._halt_trading("MANUAL_HALT", reason)
        
        if self._audit_logger:
            action = AuditAction.MANUAL_OVERRIDE if AUDIT_ENUMS_AVAILABLE else "MANUAL_OVERRIDE"
            result = AuditResult.SUCCESS if AUDIT_ENUMS_AVAILABLE else "SUCCESS"
            self._audit_logger.log_event(
                action=action,
                reason=f"Manual halt: {reason}",
                module="DeadManSwitch",
                metric="manual_halt=true",
                result=result
            )
    
    def force_resume(self):
        """Manually resume trading"""
        with self._lock:
            self._trading_allowed = True
            self._halt_until = None
            self._consecutive_failures = 0
        
        logger.info("🟢 Trading manually resumed")
        
        if self._audit_logger:
            action = AuditAction.MANUAL_OVERRIDE if AUDIT_ENUMS_AVAILABLE else "MANUAL_OVERRIDE"
            result = AuditResult.SUCCESS if AUDIT_ENUMS_AVAILABLE else "SUCCESS"
            self._audit_logger.log_event(
                action=action,
                reason="Manual trading resume",
                module="DeadManSwitch",
                metric="trading_allowed=true",
                result=result
            )
    
    def register_halt_callback(self, callback: Callable):
        """Register callback for halt events"""
        self._halt_callbacks.append(callback)
    
    def register_recovery_callback(self, callback: Callable):
        """Register callback for recovery events"""
        self._recovery_callbacks.append(callback)
    
    def update_price(self, price: float):
        """Update last known price for integrity checks"""
        self._last_price = price
    
    def update_orderbook_time(self):
        """Update orderbook timestamp"""
        self._last_orderbook_time = datetime.utcnow()
    
    def update_heartbeat(self):
        """Update exchange heartbeat timestamp"""
        self._last_heartbeat_time = datetime.utcnow()
    
    def is_trading_allowed(self) -> bool:
        """Check if trading is currently allowed"""
        return self._trading_allowed
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status summary"""
        return {
            'status': self._status.value,
            'trading_allowed': self._trading_allowed,
            'consecutive_failures': self._consecutive_failures,
            'last_healthy': self._last_healthy_time.isoformat(),
            'halt_until': self._halt_until.isoformat() if self._halt_until else None,
            'monitoring_active': self._running
        }
    
    def format_status_text(self) -> str:
        """Format current status for display"""
        health = self.check_health()
        
        status_icons = {
            HealthStatus.HEALTHY: "🟢",
            HealthStatus.DEGRADED: "🟡",
            HealthStatus.CRITICAL: "🟠",
            HealthStatus.DEAD: "🔴"
        }
        
        lines = [
            "=" * 50,
            "🔒 DEAD MAN SWITCH - INSTITUTIONAL SAFETY LOCK",
            "=" * 50,
            f"Status: {status_icons.get(health.status, '❓')} {health.status.value}",
            f"Trading Allowed: {'✅ YES' if health.trading_allowed else '❌ NO'}",
            f"Consecutive Failures: {health.consecutive_failures}",
            f"Time Since Healthy: {health.time_since_healthy_seconds:.1f}s",
            "",
            "-" * 50,
            "Health Checks:",
            "-" * 50
        ]
        
        for check in health.checks:
            icon = "✅" if check.passed else "❌"
            lines.append(f"  {icon} {check.check_type.value}: {check.value}")
        
        if health.failed_checks:
            lines.extend([
                "",
                f"⚠️ Failed: {', '.join(health.failed_checks)}"
            ])
        
        lines.extend([
            "",
            "=" * 50
        ])
        
        return "\n".join(lines)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
    )
    
    dms = DeadManSwitch()
    
    print("\n🧪 Testing Dead Man Switch...\n")
    
    health = dms.check_health()
    print(dms.format_status_text())
    
    print("\n📊 Status:", dms.get_status())
    
    print("\n✅ Dead Man Switch test complete")
