"""
OMNIX REST API Port - HTTP Interface Contract

This Protocol defines the contract for REST API endpoints.
Driver ports represent how external actors interact with the application.

SOLID Principles:
- SRP: Only HTTP request/response handling
- ISP: Minimal interface for API operations
- DIP: Controllers depend on this abstraction
"""

from typing import Protocol, Dict, Any, runtime_checkable


@runtime_checkable
class RestApiPort(Protocol):
    """
    Contract for REST API endpoint handlers.
    
    Implementation: omnix_dashboard.app (Flask routes)
    """
    
    def get_health(self) -> Dict[str, Any]:
        """
        Health check endpoint.
        
        Returns:
            Dict with:
            - status: str ('healthy', 'degraded', 'unhealthy')
            - version: str
            - uptime_seconds: int
            - components: Dict[str, bool]
        """
        ...
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get trading metrics.
        
        Returns:
            Dict with trading performance metrics:
            - total_trades: int
            - win_rate: float
            - profit_loss: float
            - sharpe_ratio: float
        """
        ...
    
    def get_positions(self) -> Dict[str, Any]:
        """
        Get current positions.
        
        Returns:
            Dict with:
            - positions: List of position dicts
            - total_value: float
            - unrealized_pnl: float
        """
        ...
    
    def execute_command(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a trading command.
        
        Args:
            command: Command name ('start', 'stop', 'status', etc.)
            params: Command parameters
            
        Returns:
            Dict with command result
        """
        ...
