"""
OMNIX V7.0 Risk Guardian Domain Module
========================================
Re-export from legacy location for backward compatibility.

Original: omnix_services/monitoring/risk_guardian.py
Migration Status: RE-EXPORT (Phase 2 Wave 2)

This file serves as a bridge during migration. The RiskGuardian is
re-exported from its legacy location while maintaining the new
hexagonal architecture structure.
"""

try:
    from omnix_services.monitoring.risk_guardian import (
        RiskGuardian,
        RiskGuardian as AIRiskGuardian,
    )
except ImportError:
    RiskGuardian = None
    AIRiskGuardian = None

__all__ = ["RiskGuardian", "AIRiskGuardian"]
