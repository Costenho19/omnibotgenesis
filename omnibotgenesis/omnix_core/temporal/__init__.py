"""
Temporal Coherence Validation (TCV) — OMNIX Checkpoint 7

Evaluates temporal admissibility of proposed decisions against
recent system trajectory. Inspired by QTD (JJ Jimenez, Feb 2026).
ADR-032.
"""

from omnix_core.temporal.coherence_validator import TemporalCoherenceValidator, TCVResult

__all__ = ["TemporalCoherenceValidator", "TCVResult"]
