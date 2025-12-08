"""
OMNIX V6.5.4 - Database Migrations Module

Professional versioned migration system integrated with main.py entrypoint.
All migrations are idempotent and non-destructive.

Usage:
    from omnix_services.database_service.migrations import MigrationRunner
    
    runner = MigrationRunner(database_url)
    runner.run_pending_migrations()
"""

from .registry import Migration, MigrationRegistry, MigrationRunner
from .versions import MIGRATIONS

__all__ = [
    'Migration',
    'MigrationRegistry', 
    'MigrationRunner',
    'MIGRATIONS'
]
