"""
OMNIX Dashboard Blueprints
Modular route organization for Flask application
"""

from .views import views_bp
from .core import core_bp
from .market import market_bp
from .intelligence import intelligence_bp
from .system import system_bp
from .snapshots import snapshots_bp
from .verification import verification_bp
from .governance import governance_bp
from .governance_risk import governance_risk_bp
from .governance_metrics import governance_metrics_bp
from .governance_oversight import governance_oversight_bp
from .governance_incidents import governance_incidents_bp
from .governance_reports import governance_reports_bp
from .governance_sandbox import governance_sandbox_bp
from .governance_alerts import governance_alerts_bp
from .public_sandbox import public_sandbox_bp
from .public_verify import public_verify_bp
from .receipt_verification import receipt_pki_bp
from .credit_governance import credit_bp
from .insurance_governance import insurance_bp
from .robotics_governance import robotics_bp
from .medical_governance import medical_bp
from .agents_governance import agents_bp
from .real_estate_governance import real_estate_bp
from .energy_governance import energy_bp
from .stablecoin_governance import stablecoin_bp

__all__ = [
    'views_bp',
    'core_bp',
    'market_bp',
    'intelligence_bp',
    'system_bp',
    'snapshots_bp',
    'verification_bp',
    'governance_bp',
    'governance_risk_bp',
    'governance_metrics_bp',
    'governance_oversight_bp',
    'governance_incidents_bp',
    'governance_reports_bp',
    'governance_sandbox_bp',
    'governance_alerts_bp',
    'public_sandbox_bp',
    'public_verify_bp',
    'receipt_pki_bp',
    'credit_bp',
    'insurance_bp',
    'robotics_bp',
    'medical_bp',
    'agents_bp',
    'real_estate_bp',
    'energy_bp',
    'stablecoin_bp',
]
