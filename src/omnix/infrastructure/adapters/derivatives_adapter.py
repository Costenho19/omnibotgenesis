"""
OMNIX V7.0 - DerivativesAdapter
================================
Adapter implementing DerivativesPort by wrapping legacy derivatives services.

Wrapped Legacy Services:
- DerivativesManager (omnix_services/derivatives/)
- KrakenFuturesClient (omnix_services/exchange/)
- HedgingService (omnix_services/derivatives/)
- OptionsPricer (omnix_services/derivatives/)

Feature flag: USE_DERIVATIVES_PORT
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import uuid

from src.omnix.ports.driven.derivatives_port import (
    DerivativesPort,
    FuturesContract,
    ContractType,
    DerivativesPosition,
    MarginStatus,
    MarginType,
    HedgeOrder,
    HedgeType,
    HedgeRecommendation,
    FundingAnalysis,
    DerivativesSummary,
)

logger = logging.getLogger(__name__)


class DerivativesAdapter:
    """
    Adapter wrapping legacy derivatives services.
    
    Implements DerivativesPort protocol with lazy loading
    and graceful degradation.
    """
    
    def __init__(
        self,
        derivatives_manager: Any = None,
        futures_client: Any = None,
        hedging_service: Any = None,
        options_pricer: Any = None
    ):
        self._derivatives_manager = derivatives_manager
        self._futures_client = futures_client
        self._hedging_service = hedging_service
        self._options_pricer = options_pricer
        self._initialized = False
        self._active_hedges: List[HedgeOrder] = []
        logger.info("DerivativesAdapter: Initialized with lazy-loaded services")
    
    def _ensure_services(self) -> None:
        """Lazy load services if not initialized."""
        if self._initialized:
            return
        
        if self._derivatives_manager is None:
            try:
                from omnix_services.derivatives.derivatives_manager import DerivativesManager
                self._derivatives_manager = DerivativesManager()
            except ImportError:
                logger.warning("DerivativesAdapter: DerivativesManager not available")
        
        if self._futures_client is None:
            try:
                from omnix_services.exchange.kraken_futures_client import KrakenFuturesClient
                self._futures_client = KrakenFuturesClient()
            except ImportError:
                logger.warning("DerivativesAdapter: KrakenFuturesClient not available")
        
        if self._hedging_service is None:
            try:
                from omnix_services.derivatives.hedging_service import HedgingService
                self._hedging_service = HedgingService()
            except ImportError:
                logger.warning("DerivativesAdapter: HedgingService not available")
        
        if self._options_pricer is None:
            try:
                from omnix_services.derivatives.options_pricer import OptionsPricer
                self._options_pricer = OptionsPricer()
            except ImportError:
                logger.warning("DerivativesAdapter: OptionsPricer not available")
        
        self._initialized = True
    
    def _map_contract_type(self, type_str: str) -> ContractType:
        """Map string to ContractType enum."""
        type_lower = type_str.lower()
        mapping = {
            "perpetual": ContractType.PERPETUAL,
            "quarterly": ContractType.QUARTERLY,
            "monthly": ContractType.MONTHLY,
            "weekly": ContractType.WEEKLY,
            "call": ContractType.OPTION_CALL,
            "put": ContractType.OPTION_PUT,
        }
        return mapping.get(type_lower, ContractType.PERPETUAL)
    
    def _map_margin_type(self, type_str: str) -> MarginType:
        """Map string to MarginType enum."""
        if type_str.lower() == "isolated":
            return MarginType.ISOLATED
        return MarginType.CROSS
    
    def _map_hedge_type(self, type_str: str) -> HedgeType:
        """Map string to HedgeType enum."""
        type_lower = type_str.lower().replace("-", "_").replace(" ", "_")
        mapping = {
            "delta_neutral": HedgeType.DELTA_NEUTRAL,
            "protective_put": HedgeType.PROTECTIVE_PUT,
            "covered_call": HedgeType.COVERED_CALL,
            "collar": HedgeType.COLLAR,
            "inverse": HedgeType.INVERSE,
        }
        return mapping.get(type_lower, HedgeType.DELTA_NEUTRAL)
    
    def get_futures_contracts(
        self,
        underlying: Optional[str] = None
    ) -> List[FuturesContract]:
        """Get available futures contracts."""
        self._ensure_services()
        
        try:
            if self._futures_client and hasattr(self._futures_client, 'get_contracts'):
                result = self._futures_client.get_contracts(underlying)
                
                if isinstance(result, list):
                    contracts = []
                    for item in result:
                        contracts.append(FuturesContract(
                            symbol=item.get('symbol', ''),
                            contract_type=self._map_contract_type(item.get('type', 'perpetual')),
                            underlying=item.get('underlying', ''),
                            expiry=item.get('expiry'),
                            mark_price=item.get('mark_price', 0),
                            index_price=item.get('index_price', 0),
                            funding_rate=item.get('funding_rate', 0),
                            next_funding_time=item.get('next_funding'),
                            open_interest=item.get('open_interest', 0),
                            volume_24h=item.get('volume_24h', 0)
                        ))
                    return contracts
        except Exception as e:
            logger.error(f"DerivativesAdapter: get_futures_contracts error: {e}")
        
        return []
    
    def get_contract_info(
        self,
        symbol: str
    ) -> Optional[FuturesContract]:
        """Get info for a specific contract."""
        self._ensure_services()
        
        try:
            if self._futures_client and hasattr(self._futures_client, 'get_contract'):
                result = self._futures_client.get_contract(symbol)
                
                if isinstance(result, dict):
                    return FuturesContract(
                        symbol=result.get('symbol', symbol),
                        contract_type=self._map_contract_type(result.get('type', 'perpetual')),
                        underlying=result.get('underlying', ''),
                        expiry=result.get('expiry'),
                        mark_price=result.get('mark_price', 0),
                        index_price=result.get('index_price', 0),
                        funding_rate=result.get('funding_rate', 0),
                        next_funding_time=result.get('next_funding'),
                        open_interest=result.get('open_interest', 0),
                        volume_24h=result.get('volume_24h', 0)
                    )
        except Exception as e:
            logger.error(f"DerivativesAdapter: get_contract_info error: {e}")
        
        return None
    
    def get_derivatives_positions(
        self,
        symbols: Optional[List[str]] = None
    ) -> List[DerivativesPosition]:
        """Get current derivatives positions."""
        self._ensure_services()
        
        try:
            if self._derivatives_manager and hasattr(self._derivatives_manager, 'get_positions'):
                result = self._derivatives_manager.get_positions(symbols)
                
                if isinstance(result, list):
                    positions = []
                    for item in result:
                        positions.append(DerivativesPosition(
                            symbol=item.get('symbol', ''),
                            contract_type=self._map_contract_type(item.get('type', 'perpetual')),
                            side=item.get('side', 'long'),
                            size=item.get('size', 0),
                            size_usd=item.get('size_usd', 0),
                            entry_price=item.get('entry_price', 0),
                            mark_price=item.get('mark_price', 0),
                            liquidation_price=item.get('liquidation_price'),
                            margin_used=item.get('margin', 0),
                            margin_type=self._map_margin_type(item.get('margin_type', 'cross')),
                            leverage=item.get('leverage', 1),
                            unrealized_pnl=item.get('unrealized_pnl', 0),
                            unrealized_pnl_pct=item.get('unrealized_pnl_pct', 0),
                            funding_payment_accumulated=item.get('funding_paid', 0)
                        ))
                    return positions
        except Exception as e:
            logger.error(f"DerivativesAdapter: get_derivatives_positions error: {e}")
        
        return []
    
    def get_margin_status(self) -> MarginStatus:
        """Get margin account status."""
        self._ensure_services()
        
        try:
            if self._futures_client and hasattr(self._futures_client, 'get_margin'):
                result = self._futures_client.get_margin()
                
                if isinstance(result, dict):
                    return MarginStatus(
                        total_collateral_usd=result.get('total_collateral', 0),
                        available_margin_usd=result.get('available', 0),
                        used_margin_usd=result.get('used', 0),
                        maintenance_margin_usd=result.get('maintenance', 0),
                        margin_ratio=result.get('ratio', 100),
                        account_leverage=result.get('leverage', 1),
                        liquidation_risk=result.get('liquidation_risk', 0),
                        margin_type=self._map_margin_type(result.get('type', 'cross'))
                    )
        except Exception as e:
            logger.error(f"DerivativesAdapter: get_margin_status error: {e}")
        
        return MarginStatus(
            total_collateral_usd=0,
            available_margin_usd=0,
            used_margin_usd=0,
            maintenance_margin_usd=0,
            margin_ratio=100,
            account_leverage=1,
            liquidation_risk=0
        )
    
    def calculate_hedge_requirement(
        self,
        spot_symbol: str,
        spot_size_usd: float,
        target_delta: float = 0.0
    ) -> HedgeRecommendation:
        """Calculate hedging requirement for a spot position."""
        self._ensure_services()
        
        try:
            if self._hedging_service and hasattr(self._hedging_service, 'calculate'):
                result = self._hedging_service.calculate(
                    spot_symbol, spot_size_usd, target_delta
                )
                
                if isinstance(result, dict):
                    return HedgeRecommendation(
                        should_hedge=result.get('should_hedge', False),
                        hedge_type=self._map_hedge_type(result.get('type', 'delta_neutral')),
                        recommended_size_usd=result.get('size_usd', 0),
                        recommended_instrument=result.get('instrument', ''),
                        reason=result.get('reason', ''),
                        urgency=result.get('urgency', 'normal'),
                        estimated_cost_usd=result.get('cost', 0)
                    )
        except Exception as e:
            logger.error(f"DerivativesAdapter: calculate_hedge_requirement error: {e}")
        
        return HedgeRecommendation(
            should_hedge=False,
            hedge_type=HedgeType.DELTA_NEUTRAL,
            recommended_size_usd=0,
            recommended_instrument='',
            reason='Hedging service unavailable',
            urgency='low'
        )
    
    def execute_hedge(
        self,
        recommendation: HedgeRecommendation
    ) -> HedgeOrder:
        """Execute a hedge based on recommendation."""
        self._ensure_services()
        
        hedge_id = str(uuid.uuid4())[:8]
        now = datetime.now()
        
        try:
            if self._hedging_service and hasattr(self._hedging_service, 'execute'):
                result = self._hedging_service.execute({
                    'type': recommendation.hedge_type.value,
                    'size_usd': recommendation.recommended_size_usd,
                    'instrument': recommendation.recommended_instrument
                })
                
                if isinstance(result, dict):
                    hedge = HedgeOrder(
                        hedge_id=result.get('id', hedge_id),
                        hedge_type=recommendation.hedge_type,
                        spot_symbol='',
                        hedge_symbol=recommendation.recommended_instrument,
                        spot_size_usd=0,
                        hedge_size_usd=recommendation.recommended_size_usd,
                        hedge_ratio=1.0,
                        entry_price=result.get('entry_price', 0),
                        target_delta=0,
                        current_delta=result.get('delta', 0),
                        status=result.get('status', 'filled'),
                        created_at=now
                    )
                    self._active_hedges.append(hedge)
                    return hedge
        except Exception as e:
            logger.error(f"DerivativesAdapter: execute_hedge error: {e}")
        
        hedge = HedgeOrder(
            hedge_id=hedge_id,
            hedge_type=recommendation.hedge_type,
            spot_symbol='',
            hedge_symbol=recommendation.recommended_instrument,
            spot_size_usd=0,
            hedge_size_usd=recommendation.recommended_size_usd,
            hedge_ratio=1.0,
            entry_price=0,
            status='failed',
            created_at=now
        )
        return hedge
    
    def get_active_hedges(self) -> List[HedgeOrder]:
        """Get active hedge orders."""
        self._ensure_services()
        
        try:
            if self._hedging_service and hasattr(self._hedging_service, 'get_active'):
                result = self._hedging_service.get_active()
                
                if isinstance(result, list):
                    hedges = []
                    for item in result:
                        hedges.append(HedgeOrder(
                            hedge_id=item.get('id', ''),
                            hedge_type=self._map_hedge_type(item.get('type', 'delta_neutral')),
                            spot_symbol=item.get('spot_symbol', ''),
                            hedge_symbol=item.get('hedge_symbol', ''),
                            spot_size_usd=item.get('spot_size', 0),
                            hedge_size_usd=item.get('hedge_size', 0),
                            hedge_ratio=item.get('ratio', 1),
                            entry_price=item.get('entry_price', 0),
                            target_delta=item.get('target_delta', 0),
                            current_delta=item.get('current_delta', 0),
                            status=item.get('status', 'active'),
                            created_at=item.get('created_at', datetime.now())
                        ))
                    return hedges
        except Exception as e:
            logger.error(f"DerivativesAdapter: get_active_hedges error: {e}")
        
        return self._active_hedges
    
    def rebalance_hedge(
        self,
        hedge_id: str
    ) -> HedgeOrder:
        """Rebalance an existing hedge."""
        self._ensure_services()
        
        try:
            if self._hedging_service and hasattr(self._hedging_service, 'rebalance'):
                result = self._hedging_service.rebalance(hedge_id)
                
                if isinstance(result, dict):
                    return HedgeOrder(
                        hedge_id=hedge_id,
                        hedge_type=self._map_hedge_type(result.get('type', 'delta_neutral')),
                        spot_symbol=result.get('spot_symbol', ''),
                        hedge_symbol=result.get('hedge_symbol', ''),
                        spot_size_usd=result.get('spot_size', 0),
                        hedge_size_usd=result.get('hedge_size', 0),
                        hedge_ratio=result.get('ratio', 1),
                        entry_price=result.get('entry_price', 0),
                        target_delta=result.get('target_delta', 0),
                        current_delta=result.get('current_delta', 0),
                        status='rebalanced'
                    )
        except Exception as e:
            logger.error(f"DerivativesAdapter: rebalance_hedge error: {e}")
        
        return HedgeOrder(
            hedge_id=hedge_id,
            hedge_type=HedgeType.DELTA_NEUTRAL,
            spot_symbol='',
            hedge_symbol='',
            spot_size_usd=0,
            hedge_size_usd=0,
            hedge_ratio=1,
            entry_price=0,
            status='failed'
        )
    
    def analyze_funding_rates(
        self,
        symbols: Optional[List[str]] = None
    ) -> List[FundingAnalysis]:
        """Analyze funding rates for opportunities."""
        self._ensure_services()
        
        try:
            if self._futures_client and hasattr(self._futures_client, 'get_funding_analysis'):
                result = self._futures_client.get_funding_analysis(symbols)
                
                if isinstance(result, list):
                    analyses = []
                    for item in result:
                        rate = item.get('current_rate', 0)
                        analyses.append(FundingAnalysis(
                            symbol=item.get('symbol', ''),
                            current_rate=rate,
                            predicted_rate_8h=item.get('predicted_rate', rate),
                            rate_trend=item.get('trend', 'stable'),
                            annualized_rate=rate * 3 * 365 * 100,
                            is_favorable_long=rate < 0,
                            is_favorable_short=rate > 0,
                            recommendation=item.get('recommendation', '')
                        ))
                    return analyses
        except Exception as e:
            logger.error(f"DerivativesAdapter: analyze_funding_rates error: {e}")
        
        return []
    
    def get_derivatives_summary(self) -> DerivativesSummary:
        """Get summary of derivatives exposure."""
        self._ensure_services()
        
        positions = self.get_derivatives_positions()
        
        total_notional = sum(p.size_usd for p in positions)
        total_pnl = sum(p.unrealized_pnl for p in positions)
        net_delta = sum(p.size_usd if p.side == 'long' else -p.size_usd for p in positions)
        
        margin = self.get_margin_status()
        largest_pct = 0.0
        if total_notional > 0:
            largest_pct = max((p.size_usd / total_notional * 100) for p in positions) if positions else 0
        
        return DerivativesSummary(
            total_positions=len(positions),
            total_notional_usd=total_notional,
            total_unrealized_pnl=total_pnl,
            net_delta=net_delta,
            total_funding_paid_24h=sum(p.funding_payment_accumulated for p in positions),
            margin_utilization_pct=100 - margin.margin_ratio if margin.margin_ratio < 100 else 0,
            largest_position_pct=largest_pct,
            positions=positions
        )
    
    def set_leverage(
        self,
        symbol: str,
        leverage: float
    ) -> bool:
        """Set leverage for a symbol."""
        self._ensure_services()
        
        try:
            if self._futures_client and hasattr(self._futures_client, 'set_leverage'):
                return self._futures_client.set_leverage(symbol, leverage)
        except Exception as e:
            logger.error(f"DerivativesAdapter: set_leverage error: {e}")
        
        return False
    
    def set_margin_type(
        self,
        symbol: str,
        margin_type: MarginType
    ) -> bool:
        """Set margin type for a symbol."""
        self._ensure_services()
        
        try:
            if self._futures_client and hasattr(self._futures_client, 'set_margin_type'):
                return self._futures_client.set_margin_type(symbol, margin_type.value)
        except Exception as e:
            logger.error(f"DerivativesAdapter: set_margin_type error: {e}")
        
        return False
    
    def is_derivatives_available(self) -> tuple[bool, str]:
        """Check if derivatives trading is available."""
        self._ensure_services()
        
        if self._futures_client is None:
            return False, "Futures client not initialized"
        
        try:
            if hasattr(self._futures_client, 'is_available'):
                result = self._futures_client.is_available()
                if isinstance(result, tuple):
                    return result
                return bool(result), "" if result else "Service unavailable"
        except Exception as e:
            return False, str(e)
        
        return True, ""
    
    def health_check(self) -> Dict[str, Any]:
        """Check health of derivatives services."""
        self._ensure_services()
        
        components = {
            'derivatives_manager': self._derivatives_manager is not None,
            'futures_client': self._futures_client is not None,
            'hedging_service': self._hedging_service is not None,
            'options_pricer': self._options_pricer is not None,
        }
        
        healthy_count = sum(1 for v in components.values() if v)
        
        is_available, reason = self.is_derivatives_available()
        
        return {
            'healthy': healthy_count >= 2 and is_available,
            'adapter': 'DerivativesAdapter',
            'components': components,
            'healthy_count': healthy_count,
            'total_components': len(components),
            'derivatives_available': is_available,
            'availability_reason': reason,
            'active_hedges': len(self._active_hedges),
            'timestamp': datetime.now().isoformat()
        }
