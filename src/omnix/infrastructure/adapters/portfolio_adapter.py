"""
OMNIX V7.0 - PortfolioAdapter
==============================
Adapter implementing PortfolioPort by wrapping legacy portfolio services.

Wrapped Legacy Services:
- PortfolioEngine (omnix_services/portfolio/)
- PortfolioOptimizer (omnix_services/portfolio/)
- ExposureManager (omnix_services/portfolio/)
- RiskModelEngine (omnix_services/portfolio/)

Feature flag: USE_PORTFOLIO_PORT
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from src.omnix.ports.driven.portfolio_port import (
    PortfolioPort,
    PortfolioPosition,
    PortfolioView,
    ExposureReport,
    RebalanceOrder,
    RebalanceCommand,
    RebalanceStrategy,
    TargetAllocation,
    AllocationPlan,
    AssetClass,
)

logger = logging.getLogger(__name__)


class PortfolioAdapter:
    """
    Adapter wrapping legacy portfolio services.
    
    Implements PortfolioPort protocol with lazy loading
    and graceful degradation.
    """
    
    def __init__(
        self,
        portfolio_engine: Any = None,
        portfolio_optimizer: Any = None,
        exposure_manager: Any = None,
        risk_model_engine: Any = None
    ):
        self._portfolio_engine = portfolio_engine
        self._portfolio_optimizer = portfolio_optimizer
        self._exposure_manager = exposure_manager
        self._risk_model_engine = risk_model_engine
        self._initialized = False
        self._active_plan: Optional[AllocationPlan] = None
        logger.info("PortfolioAdapter: Initialized with lazy-loaded services")
    
    def _ensure_services(self) -> None:
        """Lazy load services if not initialized."""
        if self._initialized:
            return
        
        if self._portfolio_engine is None:
            try:
                from omnix_services.portfolio.portfolio_engine import PortfolioEngine
                self._portfolio_engine = PortfolioEngine()
            except ImportError:
                logger.warning("PortfolioAdapter: PortfolioEngine not available")
        
        if self._portfolio_optimizer is None:
            try:
                from omnix_services.portfolio.portfolio_optimizer import PortfolioOptimizer
                self._portfolio_optimizer = PortfolioOptimizer()
            except ImportError:
                logger.warning("PortfolioAdapter: PortfolioOptimizer not available")
        
        if self._exposure_manager is None:
            try:
                from omnix_services.portfolio.exposure_manager import ExposureManager
                self._exposure_manager = ExposureManager()
            except ImportError:
                logger.warning("PortfolioAdapter: ExposureManager not available")
        
        if self._risk_model_engine is None:
            try:
                from omnix_services.portfolio.risk_model_engine import RiskModelEngine
                self._risk_model_engine = RiskModelEngine()
            except ImportError:
                logger.warning("PortfolioAdapter: RiskModelEngine not available")
        
        self._initialized = True
    
    def _map_asset_class(self, class_str: str) -> AssetClass:
        """Map string to AssetClass enum."""
        class_lower = class_str.lower()
        mapping = {
            "crypto": AssetClass.CRYPTO,
            "stocks": AssetClass.STOCKS,
            "forex": AssetClass.FOREX,
            "commodities": AssetClass.COMMODITIES,
            "derivatives": AssetClass.DERIVATIVES,
            "stablecoins": AssetClass.STABLECOINS,
        }
        return mapping.get(class_lower, AssetClass.CRYPTO)
    
    def _map_rebalance_strategy(self, strategy_str: str) -> RebalanceStrategy:
        """Map string to RebalanceStrategy enum."""
        strategy_lower = strategy_str.lower()
        mapping = {
            "threshold": RebalanceStrategy.THRESHOLD,
            "calendar": RebalanceStrategy.CALENDAR,
            "tactical": RebalanceStrategy.TACTICAL,
            "momentum": RebalanceStrategy.MOMENTUM,
            "risk_parity": RebalanceStrategy.RISK_PARITY,
        }
        return mapping.get(strategy_lower, RebalanceStrategy.THRESHOLD)
    
    def get_portfolio_view(
        self,
        include_derivatives: bool = False
    ) -> PortfolioView:
        """Get current portfolio view."""
        self._ensure_services()
        
        try:
            if self._portfolio_engine and hasattr(self._portfolio_engine, 'get_view'):
                result = self._portfolio_engine.get_view(include_derivatives)
                
                if isinstance(result, dict):
                    positions = []
                    for pos in result.get('positions', []):
                        positions.append(PortfolioPosition(
                            symbol=pos.get('symbol', ''),
                            asset_class=self._map_asset_class(pos.get('asset_class', 'crypto')),
                            quantity=pos.get('quantity', 0),
                            avg_entry_price=pos.get('entry_price', 0),
                            current_price=pos.get('current_price', 0),
                            market_value_usd=pos.get('value_usd', 0),
                            unrealized_pnl=pos.get('unrealized_pnl', 0),
                            unrealized_pnl_pct=pos.get('unrealized_pnl_pct', 0),
                            weight_pct=pos.get('weight_pct', 0),
                            target_weight_pct=pos.get('target_weight'),
                            side=pos.get('side', 'long')
                        ))
                    
                    return PortfolioView(
                        total_value_usd=result.get('total_value', 0),
                        cash_usd=result.get('cash', 0),
                        invested_usd=result.get('invested', 0),
                        positions=positions,
                        position_count=len(positions),
                        asset_allocation=result.get('allocation', {}),
                        unrealized_pnl=result.get('unrealized_pnl', 0),
                        unrealized_pnl_pct=result.get('unrealized_pnl_pct', 0),
                        realized_pnl_today=result.get('realized_pnl_today', 0),
                        sharpe_ratio=result.get('sharpe'),
                        sortino_ratio=result.get('sortino'),
                        max_drawdown_pct=result.get('max_drawdown')
                    )
        except Exception as e:
            logger.error(f"PortfolioAdapter: get_portfolio_view error: {e}")
        
        return PortfolioView(
            total_value_usd=0,
            cash_usd=0,
            invested_usd=0,
            positions=[],
            position_count=0,
            asset_allocation={},
            unrealized_pnl=0,
            unrealized_pnl_pct=0,
            realized_pnl_today=0
        )
    
    def get_positions(
        self,
        asset_class: Optional[AssetClass] = None,
        symbols: Optional[List[str]] = None
    ) -> List[PortfolioPosition]:
        """Get portfolio positions."""
        view = self.get_portfolio_view()
        positions = view.positions
        
        if asset_class:
            positions = [p for p in positions if p.asset_class == asset_class]
        
        if symbols:
            positions = [p for p in positions if p.symbol in symbols]
        
        return positions
    
    def get_exposure_report(self) -> ExposureReport:
        """Get portfolio exposure report."""
        self._ensure_services()
        
        try:
            if self._exposure_manager and hasattr(self._exposure_manager, 'get_report'):
                result = self._exposure_manager.get_report()
                
                if isinstance(result, dict):
                    return ExposureReport(
                        gross_exposure_usd=result.get('gross', 0),
                        net_exposure_usd=result.get('net', 0),
                        long_exposure_usd=result.get('long', 0),
                        short_exposure_usd=result.get('short', 0),
                        leverage=result.get('leverage', 1),
                        beta=result.get('beta', 1),
                        delta_exposure=result.get('delta', 0),
                        sector_exposure=result.get('sectors', {}),
                        asset_class_exposure=result.get('asset_classes', {}),
                        geographic_exposure=result.get('geographic', {}),
                        concentration_top5_pct=result.get('concentration', 0),
                        correlation_with_market=result.get('market_correlation', 0)
                    )
        except Exception as e:
            logger.error(f"PortfolioAdapter: get_exposure_report error: {e}")
        
        return ExposureReport(
            gross_exposure_usd=0,
            net_exposure_usd=0,
            long_exposure_usd=0,
            short_exposure_usd=0,
            leverage=1,
            beta=1,
            delta_exposure=0,
            sector_exposure={},
            asset_class_exposure={},
            geographic_exposure={},
            concentration_top5_pct=0,
            correlation_with_market=0
        )
    
    def calculate_rebalance(
        self,
        strategy: RebalanceStrategy = RebalanceStrategy.THRESHOLD,
        targets: Optional[List[TargetAllocation]] = None
    ) -> RebalanceCommand:
        """Calculate rebalancing orders."""
        self._ensure_services()
        
        command_id = str(uuid.uuid4())[:8]
        
        try:
            if self._portfolio_optimizer and hasattr(self._portfolio_optimizer, 'calculate_rebalance'):
                target_dict = None
                if targets:
                    target_dict = {t.symbol: t.target_weight_pct for t in targets}
                
                result = self._portfolio_optimizer.calculate_rebalance(strategy.value, target_dict)
                
                if isinstance(result, dict):
                    orders = []
                    for order in result.get('orders', []):
                        orders.append(RebalanceOrder(
                            symbol=order.get('symbol', ''),
                            side=order.get('side', 'buy'),
                            quantity=order.get('quantity', 0),
                            current_weight_pct=order.get('current_weight', 0),
                            target_weight_pct=order.get('target_weight', 0),
                            estimated_value_usd=order.get('value_usd', 0),
                            priority=order.get('priority', 0),
                            reason=order.get('reason', '')
                        ))
                    
                    return RebalanceCommand(
                        command_id=result.get('id', command_id),
                        strategy=strategy,
                        orders=orders,
                        total_buy_usd=result.get('total_buy', 0),
                        total_sell_usd=result.get('total_sell', 0),
                        net_flow_usd=result.get('net_flow', 0),
                        estimated_cost_usd=result.get('cost', 0),
                        drift_before_pct=result.get('drift_before', 0),
                        drift_after_pct=result.get('drift_after', 0)
                    )
        except Exception as e:
            logger.error(f"PortfolioAdapter: calculate_rebalance error: {e}")
        
        return RebalanceCommand(
            command_id=command_id,
            strategy=strategy,
            orders=[],
            total_buy_usd=0,
            total_sell_usd=0,
            net_flow_usd=0,
            estimated_cost_usd=0,
            drift_before_pct=0,
            drift_after_pct=0,
            status='failed'
        )
    
    def execute_rebalance(
        self,
        command: RebalanceCommand
    ) -> RebalanceCommand:
        """Execute a rebalance command."""
        self._ensure_services()
        
        try:
            if self._portfolio_optimizer and hasattr(self._portfolio_optimizer, 'execute_rebalance'):
                result = self._portfolio_optimizer.execute_rebalance({
                    'id': command.command_id,
                    'orders': [
                        {'symbol': o.symbol, 'side': o.side, 'quantity': o.quantity}
                        for o in command.orders
                    ]
                })
                
                if isinstance(result, dict):
                    command.status = result.get('status', 'executed')
                    return command
        except Exception as e:
            logger.error(f"PortfolioAdapter: execute_rebalance error: {e}")
        
        command.status = 'failed'
        return command
    
    def get_allocation_plan(
        self,
        plan_id: Optional[str] = None
    ) -> Optional[AllocationPlan]:
        """Get allocation plan."""
        self._ensure_services()
        
        if plan_id is None and self._active_plan:
            return self._active_plan
        
        try:
            if self._portfolio_optimizer and hasattr(self._portfolio_optimizer, 'get_plan'):
                result = self._portfolio_optimizer.get_plan(plan_id)
                
                if isinstance(result, dict):
                    targets = []
                    for t in result.get('targets', []):
                        targets.append(TargetAllocation(
                            symbol=t.get('symbol', ''),
                            target_weight_pct=t.get('weight', 0),
                            min_weight_pct=t.get('min', 0),
                            max_weight_pct=t.get('max', 100),
                            asset_class=self._map_asset_class(t.get('asset_class', 'crypto')),
                            rebalance_threshold_pct=t.get('threshold', 5)
                        ))
                    
                    return AllocationPlan(
                        plan_id=result.get('id', ''),
                        name=result.get('name', ''),
                        targets=targets,
                        rebalance_strategy=self._map_rebalance_strategy(
                            result.get('strategy', 'threshold')
                        ),
                        rebalance_frequency_hours=result.get('frequency_hours', 24),
                        is_active=result.get('active', True)
                    )
        except Exception as e:
            logger.error(f"PortfolioAdapter: get_allocation_plan error: {e}")
        
        return None
    
    def set_allocation_plan(
        self,
        plan: AllocationPlan
    ) -> bool:
        """Set or update allocation plan."""
        self._ensure_services()
        
        try:
            if self._portfolio_optimizer and hasattr(self._portfolio_optimizer, 'set_plan'):
                result = self._portfolio_optimizer.set_plan({
                    'id': plan.plan_id,
                    'name': plan.name,
                    'targets': [
                        {'symbol': t.symbol, 'weight': t.target_weight_pct}
                        for t in plan.targets
                    ],
                    'strategy': plan.rebalance_strategy.value,
                    'frequency_hours': plan.rebalance_frequency_hours
                })
                if result:
                    self._active_plan = plan
                    return True
        except Exception as e:
            logger.error(f"PortfolioAdapter: set_allocation_plan error: {e}")
        
        self._active_plan = plan
        return True
    
    def get_drift_analysis(self) -> Dict[str, Any]:
        """Get portfolio drift analysis."""
        self._ensure_services()
        
        try:
            if self._portfolio_optimizer and hasattr(self._portfolio_optimizer, 'analyze_drift'):
                return self._portfolio_optimizer.analyze_drift()
        except Exception as e:
            logger.error(f"PortfolioAdapter: get_drift_analysis error: {e}")
        
        return {
            'total_drift_pct': 0,
            'positions': {},
            'needs_rebalance': False
        }
    
    def get_performance_metrics(
        self,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """Get portfolio performance metrics."""
        self._ensure_services()
        
        try:
            if self._portfolio_engine and hasattr(self._portfolio_engine, 'get_metrics'):
                return self._portfolio_engine.get_metrics(period_days)
        except Exception as e:
            logger.error(f"PortfolioAdapter: get_performance_metrics error: {e}")
        
        return {
            'period_days': period_days,
            'total_return_pct': 0,
            'sharpe_ratio': 0,
            'sortino_ratio': 0,
            'max_drawdown_pct': 0,
            'win_rate': 0
        }
    
    def get_correlation_matrix(
        self,
        symbols: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, float]]:
        """Get correlation matrix for positions."""
        self._ensure_services()
        
        try:
            if self._exposure_manager and hasattr(self._exposure_manager, 'get_correlations'):
                return self._exposure_manager.get_correlations(symbols)
        except Exception as e:
            logger.error(f"PortfolioAdapter: get_correlation_matrix error: {e}")
        
        return {}
    
    def health_check(self) -> Dict[str, Any]:
        """Check health of portfolio services."""
        self._ensure_services()
        
        components = {
            'portfolio_engine': self._portfolio_engine is not None,
            'portfolio_optimizer': self._portfolio_optimizer is not None,
            'exposure_manager': self._exposure_manager is not None,
            'risk_model_engine': self._risk_model_engine is not None,
        }
        
        healthy_count = sum(1 for v in components.values() if v)
        
        return {
            'healthy': healthy_count >= 2,
            'adapter': 'PortfolioAdapter',
            'components': components,
            'healthy_count': healthy_count,
            'total_components': len(components),
            'has_active_plan': self._active_plan is not None,
            'timestamp': datetime.now().isoformat()
        }
