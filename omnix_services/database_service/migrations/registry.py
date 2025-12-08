"""
OMNIX V6.5.4 - Migration Registry

Provides base classes and runner for database migrations.
Follows PEP 8 and professional Python patterns.
"""

import logging
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Callable, Any

logger = logging.getLogger("OMNIX.Migrations")


@dataclass
class Migration:
    """
    Base class for database migrations.
    
    Attributes:
        version: Unique version identifier (e.g., "V001", "V002")
        description: Human-readable description of the migration
        apply_func: Callable that executes the migration
        rollback_func: Optional callable to rollback the migration
    """
    version: str
    description: str
    apply_func: Callable[[Any], bool]
    rollback_func: Optional[Callable[[Any], bool]] = None
    
    @property
    def checksum(self) -> str:
        """Generate a checksum for the migration"""
        content = f"{self.version}:{self.description}"
        return hashlib.md5(content.encode()).hexdigest()[:12]


class MigrationRegistry:
    """
    Registry for all database migrations.
    
    Maintains an ordered list of migrations and provides
    methods to query and filter them.
    """
    
    def __init__(self):
        self._migrations: List[Migration] = []
    
    def register(self, migration: Migration) -> None:
        """Register a migration"""
        if any(m.version == migration.version for m in self._migrations):
            raise ValueError(f"Migration {migration.version} already registered")
        self._migrations.append(migration)
        self._migrations.sort(key=lambda m: m.version)
    
    def get_all(self) -> List[Migration]:
        """Get all registered migrations in order"""
        return self._migrations.copy()
    
    def get_by_version(self, version: str) -> Optional[Migration]:
        """Get a specific migration by version"""
        for m in self._migrations:
            if m.version == version:
                return m
        return None
    
    def get_pending(self, applied_versions: List[str]) -> List[Migration]:
        """Get migrations not yet applied"""
        return [m for m in self._migrations if m.version not in applied_versions]


class MigrationRunner:
    """
    Executes database migrations in a safe, transactional manner.
    
    Features:
    - Creates schema_migrations table for tracking
    - Runs migrations in version order
    - Uses transactions with rollback on failure
    - Advisory locks to prevent concurrent migrations
    """
    
    LOCK_ID = 123456789
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self._conn = None
    
    def _get_connection(self):
        """Get database connection"""
        if self._conn is None:
            try:
                import psycopg2
                self._conn = psycopg2.connect(self.database_url)
                self._conn.autocommit = False
            except ImportError:
                logger.error("psycopg2 not installed")
                raise
            except Exception as e:
                logger.error(f"Failed to connect to database: {e}")
                raise
        return self._conn
    
    def _close_connection(self):
        """Close database connection"""
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None
    
    def _ensure_migrations_table(self, cursor) -> None:
        """Create schema_migrations table if not exists"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(50) PRIMARY KEY,
                description TEXT NOT NULL,
                checksum VARCHAR(20) NOT NULL,
                applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                execution_time_ms INTEGER,
                success BOOLEAN DEFAULT TRUE
            )
        """)
    
    def _get_applied_versions(self, cursor) -> List[str]:
        """Get list of already applied migration versions"""
        cursor.execute("""
            SELECT version FROM schema_migrations 
            WHERE success = TRUE
            ORDER BY version
        """)
        return [row[0] for row in cursor.fetchall()]
    
    def _acquire_lock(self, cursor) -> bool:
        """Acquire advisory lock to prevent concurrent migrations"""
        cursor.execute("SELECT pg_try_advisory_lock(%s)", (self.LOCK_ID,))
        result = cursor.fetchone()
        return result[0] if result else False
    
    def _release_lock(self, cursor) -> None:
        """Release advisory lock"""
        try:
            cursor.execute("SELECT pg_advisory_unlock(%s)", (self.LOCK_ID,))
        except Exception:
            pass
    
    def _record_migration(
        self, 
        cursor, 
        migration: Migration, 
        execution_time_ms: int,
        success: bool
    ) -> None:
        """Record migration execution in schema_migrations table"""
        cursor.execute("""
            INSERT INTO schema_migrations (version, description, checksum, execution_time_ms, success)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (version) DO UPDATE SET
                applied_at = CURRENT_TIMESTAMP,
                execution_time_ms = EXCLUDED.execution_time_ms,
                success = EXCLUDED.success
        """, (migration.version, migration.description, migration.checksum, execution_time_ms, success))
    
    def run_pending_migrations(self, registry: MigrationRegistry) -> dict:
        """
        Run all pending migrations.
        
        Returns:
            dict with 'success', 'applied', 'failed', 'skipped' counts
        """
        result = {
            'success': True,
            'applied': 0,
            'failed': 0,
            'skipped': 0,
            'errors': []
        }
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            self._ensure_migrations_table(cursor)
            conn.commit()
            
            if not self._acquire_lock(cursor):
                logger.warning("Could not acquire migration lock - another process may be running migrations")
                result['success'] = False
                result['errors'].append("Could not acquire migration lock")
                return result
            
            try:
                applied_versions = self._get_applied_versions(cursor)
                pending = registry.get_pending(applied_versions)
                
                if not pending:
                    logger.info("No pending migrations to run")
                    return result
                
                logger.info(f"Found {len(pending)} pending migration(s)")
                
                for migration in pending:
                    start_time = datetime.now()
                    
                    try:
                        logger.info(f"Running migration {migration.version}: {migration.description}")
                        
                        success = migration.apply_func(cursor)
                        
                        execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                        
                        if success:
                            self._record_migration(cursor, migration, execution_time_ms, True)
                            conn.commit()
                            result['applied'] += 1
                            logger.info(f"Migration {migration.version} completed in {execution_time_ms}ms")
                        else:
                            conn.rollback()
                            result['failed'] += 1
                            result['errors'].append(f"{migration.version}: Migration returned False")
                            logger.error(f"Migration {migration.version} failed - rolled back")
                            
                    except Exception as e:
                        conn.rollback()
                        result['failed'] += 1
                        result['errors'].append(f"{migration.version}: {str(e)}")
                        logger.error(f"Migration {migration.version} failed with error: {e}")
                
                if result['failed'] > 0:
                    result['success'] = False
                    
            finally:
                self._release_lock(cursor)
                cursor.close()
                
        except Exception as e:
            result['success'] = False
            result['errors'].append(str(e))
            logger.error(f"Migration runner error: {e}")
            
        finally:
            self._close_connection()
        
        return result
    
    def get_migration_status(self, registry: MigrationRegistry) -> dict:
        """Get status of all migrations"""
        status = {
            'applied': [],
            'pending': [],
            'total': 0
        }
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            self._ensure_migrations_table(cursor)
            conn.commit()
            
            applied_versions = self._get_applied_versions(cursor)
            
            for migration in registry.get_all():
                if migration.version in applied_versions:
                    status['applied'].append(migration.version)
                else:
                    status['pending'].append(migration.version)
            
            status['total'] = len(registry.get_all())
            
            cursor.close()
            
        except Exception as e:
            logger.error(f"Failed to get migration status: {e}")
            
        finally:
            self._close_connection()
        
        return status
