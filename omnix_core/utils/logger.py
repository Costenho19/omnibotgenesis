"""
OMNIX INSTITUTIONAL+ - Centralized Logging System
Features: Structured logging, rotation, monitoring integration, institutional decision logging
"""

import logging
import sys
import json
import uuid
import hashlib
from enum import Enum
from dataclasses import dataclass, asdict, field
from typing import Optional, List, Dict, Any
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from datetime import datetime
from omnix_config.settings import settings


class DecisionEvent(Enum):
    """Institutional-grade trade lifecycle events (Citadel/Jump Trading standard)"""
    TRADE_CANDIDATE = "TRADE_CANDIDATE"
    TRADE_VALIDATED = "TRADE_VALIDATED"
    TRADE_EXECUTED = "TRADE_EXECUTED"
    TRADE_REJECTED = "TRADE_REJECTED"
    VETO_COHERENCE = "VETO_COHERENCE"
    VETO_DRAWDOWN = "VETO_DRAWDOWN"
    VETO_CONSENSUS = "VETO_CONSENSUS"
    VETO_RISK_GUARDIAN = "VETO_RISK_GUARDIAN"
    VETO_HMM_REGIME = "VETO_HMM_REGIME"
    VETO_POSITION_LIMIT = "VETO_POSITION_LIMIT"
    AI_NARRATIVE = "AI_NARRATIVE"
    POSITION_OPENED = "POSITION_OPENED"
    POSITION_CLOSED = "POSITION_CLOSED"


@dataclass
class DecisionPayload:
    """Structured payload for institutional decision logging"""
    decision_id: str
    event_type: str
    timestamp: str
    symbol: str
    direction: Optional[str] = None
    position_size_usd: Optional[float] = None
    profile: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[int] = None
    coherence_score: Optional[float] = None
    coherence_threshold: Optional[float] = None
    consensus_agreement: Optional[str] = None
    consensus_required: Optional[str] = None
    drawdown_current: Optional[float] = None
    drawdown_limit: Optional[float] = None
    mc_win_rate: Optional[float] = None
    mc_expected_return: Optional[float] = None
    hmm_regime: Optional[str] = None
    volatility_class: Optional[str] = None
    veto_reason: Optional[str] = None
    veto_chain: Optional[List[str]] = None
    guards_passed: Optional[List[str]] = None
    order_id: Optional[str] = None
    entry_price: Optional[float] = None
    current_price: Optional[float] = None
    pnl_pct: Optional[float] = None
    pnl_usd: Optional[float] = None
    ai_explanation: Optional[str] = None
    latency_ms: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_json(self) -> str:
        """Convert to single-line JSON for ELK/Loki ingestion"""
        data = {k: v for k, v in asdict(self).items() if v is not None}
        return json.dumps(data, ensure_ascii=False, separators=(',', ':'))


class InstitutionalDecisionLogger:
    """
    OMNIX INSTITUTIONAL+ - Premium Decision Logger
    
    Citadel/Jump Trading level logging for:
    - Complete trade lifecycle traceability
    - Veto chain documentation
    - Investor audit compliance
    - Grafana/Loki/ELK compatibility
    """
    
    def __init__(self):
        self.logger = logging.getLogger("OMNIX.InstitutionalDecision")
        self._decision_counter = 0
    
    def _generate_decision_id(self, symbol: str) -> str:
        """Generate unique decision ID with traceability"""
        self._decision_counter += 1
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        unique_hash = hashlib.sha256(f"{symbol}{timestamp}{self._decision_counter}".encode()).hexdigest()[:8]
        return f"DEC-{timestamp[:14]}-{unique_hash.upper()}"
    
    def _create_payload(
        self,
        event: DecisionEvent,
        symbol: str,
        decision_id: Optional[str] = None,
        **kwargs
    ) -> DecisionPayload:
        """Create structured payload for logging"""
        return DecisionPayload(
            decision_id=decision_id or self._generate_decision_id(symbol),
            event_type=event.value,
            timestamp=datetime.utcnow().isoformat() + "Z",
            symbol=symbol,
            **kwargs
        )
    
    def emit(self, payload: DecisionPayload) -> None:
        """Emit structured log event"""
        event_type = payload.event_type
        json_line = payload.to_json()
        
        if event_type.startswith("VETO_"):
            self.logger.warning(f"[{event_type}] {json_line}")
        elif event_type == "TRADE_REJECTED":
            self.logger.warning(f"[{event_type}] {json_line}")
        elif event_type == "TRADE_EXECUTED":
            self.logger.info(f"[{event_type}] {json_line}")
        else:
            self.logger.info(f"[{event_type}] {json_line}")
    
    def log_trade_candidate(
        self,
        symbol: str,
        direction: str,
        size_usd: float,
        coherence_score: float,
        mc_win_rate: float,
        mc_expected_return: float,
        user_id: Optional[int] = None,
        profile: Optional[str] = None,
        hmm_regime: Optional[str] = None,
        volatility_class: Optional[str] = None,
        decision_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """Log trade candidate - returns decision_id for chain tracking
        
        Args:
            decision_id: Optional pre-generated decision_id for lifecycle correlation.
                         If not provided, generates a new one.
        """
        final_decision_id = decision_id or self._generate_decision_id(symbol)
        payload = self._create_payload(
            event=DecisionEvent.TRADE_CANDIDATE,
            symbol=symbol,
            decision_id=final_decision_id,
            direction=direction,
            position_size_usd=size_usd,
            coherence_score=round(coherence_score, 2),
            mc_win_rate=round(mc_win_rate, 2),
            mc_expected_return=round(mc_expected_return, 4),
            user_id=user_id,
            profile=profile,
            hmm_regime=hmm_regime,
            volatility_class=volatility_class,
            metadata=kwargs if kwargs else None
        )
        self.emit(payload)
        return final_decision_id
    
    def log_veto_coherence(
        self,
        symbol: str,
        decision_id: str,
        score: float,
        threshold: float,
        direction: Optional[str] = None
    ) -> None:
        """Log coherence engine veto"""
        payload = self._create_payload(
            event=DecisionEvent.VETO_COHERENCE,
            symbol=symbol,
            decision_id=decision_id,
            direction=direction,
            coherence_score=round(score, 2),
            coherence_threshold=round(threshold, 2),
            veto_reason=f"Coherence {score:.1f}% < threshold {threshold:.1f}%"
        )
        self.emit(payload)
    
    def log_veto_drawdown(
        self,
        symbol: str,
        decision_id: str,
        current_drawdown: float,
        limit: float,
        direction: Optional[str] = None
    ) -> None:
        """Log drawdown protection veto"""
        payload = self._create_payload(
            event=DecisionEvent.VETO_DRAWDOWN,
            symbol=symbol,
            decision_id=decision_id,
            direction=direction,
            drawdown_current=round(current_drawdown, 2),
            drawdown_limit=round(limit, 2),
            veto_reason=f"Drawdown ${current_drawdown:.2f} exceeds limit ${limit:.2f}"
        )
        self.emit(payload)
    
    def log_veto_consensus(
        self,
        symbol: str,
        decision_id: str,
        agreement: int,
        total: int,
        required: int,
        direction: Optional[str] = None
    ) -> None:
        """Log consensus gate veto"""
        payload = self._create_payload(
            event=DecisionEvent.VETO_CONSENSUS,
            symbol=symbol,
            decision_id=decision_id,
            direction=direction,
            consensus_agreement=f"{agreement}/{total}",
            consensus_required=f"{required}/{total}",
            veto_reason=f"Consensus {agreement}/{total} < required {required}/{total}"
        )
        self.emit(payload)
    
    def log_veto_risk_guardian(
        self,
        symbol: str,
        decision_id: str,
        reason: str,
        direction: Optional[str] = None
    ) -> None:
        """Log AI Risk Guardian veto"""
        payload = self._create_payload(
            event=DecisionEvent.VETO_RISK_GUARDIAN,
            symbol=symbol,
            decision_id=decision_id,
            direction=direction,
            veto_reason=reason
        )
        self.emit(payload)
    
    def log_veto_hmm_regime(
        self,
        symbol: str,
        decision_id: str,
        regime: str,
        reason: str,
        direction: Optional[str] = None
    ) -> None:
        """Log HMM regime veto"""
        payload = self._create_payload(
            event=DecisionEvent.VETO_HMM_REGIME,
            symbol=symbol,
            decision_id=decision_id,
            direction=direction,
            hmm_regime=regime,
            veto_reason=reason
        )
        self.emit(payload)
    
    def log_veto_position_limit(
        self,
        symbol: str,
        decision_id: str,
        reason: str,
        direction: Optional[str] = None
    ) -> None:
        """Log position limit veto"""
        payload = self._create_payload(
            event=DecisionEvent.VETO_POSITION_LIMIT,
            symbol=symbol,
            decision_id=decision_id,
            direction=direction,
            veto_reason=reason
        )
        self.emit(payload)
    
    def log_trade_validated(
        self,
        symbol: str,
        decision_id: str,
        direction: str,
        size_usd: float,
        guards_passed: List[str]
    ) -> None:
        """Log trade validation success - all gates passed"""
        payload = self._create_payload(
            event=DecisionEvent.TRADE_VALIDATED,
            symbol=symbol,
            decision_id=decision_id,
            direction=direction,
            position_size_usd=size_usd,
            guards_passed=guards_passed
        )
        self.emit(payload)
    
    def log_trade_executed(
        self,
        symbol: str,
        decision_id: str,
        direction: str,
        size_usd: float,
        entry_price: float,
        order_id: Optional[str] = None,
        latency_ms: Optional[float] = None
    ) -> None:
        """Log successful trade execution"""
        payload = self._create_payload(
            event=DecisionEvent.TRADE_EXECUTED,
            symbol=symbol,
            decision_id=decision_id,
            direction=direction,
            position_size_usd=size_usd,
            entry_price=entry_price,
            order_id=order_id,
            latency_ms=latency_ms
        )
        self.emit(payload)
    
    def log_trade_rejected(
        self,
        symbol: str,
        decision_id: str,
        direction: str,
        size_usd: float,
        veto_chain: List[str]
    ) -> None:
        """Log trade rejection with veto chain"""
        payload = self._create_payload(
            event=DecisionEvent.TRADE_REJECTED,
            symbol=symbol,
            decision_id=decision_id,
            direction=direction,
            position_size_usd=size_usd,
            veto_chain=veto_chain,
            veto_reason=f"Blocked by: {', '.join(veto_chain)}"
        )
        self.emit(payload)
    
    def log_ai_narrative(
        self,
        symbol: str,
        decision_id: str,
        direction: str,
        explanation: str
    ) -> None:
        """Log AI explanation (post-decision, NOT decision-making)"""
        payload = self._create_payload(
            event=DecisionEvent.AI_NARRATIVE,
            symbol=symbol,
            decision_id=decision_id,
            direction=direction,
            ai_explanation=explanation[:500] if explanation else None
        )
        self.emit(payload)
    
    def log_position_opened(
        self,
        symbol: str,
        decision_id: str,
        direction: str,
        size_usd: float,
        entry_price: float,
        user_id: Optional[int] = None
    ) -> None:
        """Log position opened"""
        payload = self._create_payload(
            event=DecisionEvent.POSITION_OPENED,
            symbol=symbol,
            decision_id=decision_id,
            direction=direction,
            position_size_usd=size_usd,
            entry_price=entry_price,
            user_id=user_id
        )
        self.emit(payload)
    
    def log_position_closed(
        self,
        symbol: str,
        decision_id: str,
        direction: str,
        entry_price: float,
        current_price: float,
        pnl_pct: float,
        pnl_usd: float,
        reason: str,
        user_id: Optional[int] = None
    ) -> None:
        """Log position closed"""
        payload = self._create_payload(
            event=DecisionEvent.POSITION_CLOSED,
            symbol=symbol,
            decision_id=decision_id,
            direction=direction,
            entry_price=entry_price,
            current_price=current_price,
            pnl_pct=round(pnl_pct, 4),
            pnl_usd=round(pnl_usd, 2),
            veto_reason=reason,
            user_id=user_id
        )
        self.emit(payload)


_institutional_logger: Optional[InstitutionalDecisionLogger] = None

def get_institutional_logger() -> InstitutionalDecisionLogger:
    """Get singleton institutional decision logger"""
    global _institutional_logger
    if _institutional_logger is None:
        _institutional_logger = InstitutionalDecisionLogger()
    return _institutional_logger


class ColoredFormatter(logging.Formatter):
    """Colored console formatter for development"""
    
    COLORS = {
        'DEBUG': '\033[36m',  # Cyan
        'INFO': '\033[32m',   # Green
        'WARNING': '\033[33m', # Yellow
        'ERROR': '\033[31m',   # Red
        'CRITICAL': '\033[35m' # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


class StructuredFormatter(logging.Formatter):
    """JSON-like structured formatter for production"""
    
    def format(self, record):
        log_record = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_record['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id
        
        # Add exception info if present
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)
        
        return str(log_record)


def setup_logging(service_name: str = "omnix"):
    """Setup enterprise logging system"""
    
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.monitoring.log_level))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console Handler (colored for development)
    console_handler = logging.StreamHandler(sys.stdout)
    if settings.DEBUG:
        console_formatter = ColoredFormatter(
            '%(asctime)s [%(levelname)s] %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        console_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File Handler - All logs
    all_file_handler = RotatingFileHandler(
        log_dir / f"{service_name}_all.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    all_file_handler.setLevel(logging.DEBUG)
    if settings.is_production():
        all_file_formatter = StructuredFormatter()
    else:
        all_file_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    all_file_handler.setFormatter(all_file_formatter)
    root_logger.addHandler(all_file_handler)
    
    # File Handler - Errors only
    error_file_handler = TimedRotatingFileHandler(
        log_dir / f"{service_name}_errors.log",
        when='midnight',
        interval=1,
        backupCount=30  # Keep 30 days of error logs
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(all_file_formatter)
    root_logger.addHandler(error_file_handler)
    
    # File Handler - Trading specific (for audit)
    trading_file_handler = RotatingFileHandler(
        log_dir / f"{service_name}_trading.log",
        maxBytes=50*1024*1024,  # 50MB (important for audit)
        backupCount=10
    )
    trading_file_handler.setLevel(logging.INFO)
    trading_file_handler.addFilter(lambda record: 'trading' in record.name.lower())
    trading_file_handler.setFormatter(all_file_formatter)
    root_logger.addHandler(trading_file_handler)
    
    # Suppress noisy loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.WARNING)
    
    logging.info(f"✅ Logging system initialized - Service: {service_name}, Level: {settings.monitoring.log_level}")


def get_logger(name: str) -> logging.Logger:
    """Get logger instance with name"""
    return logging.getLogger(name)


# Initialize logging on import
setup_logging()
