# Import Audit Report - Phase 4 Cleanup

**Date**: December 13, 2025
**Version**: V6.5.4d → V7.0 Migration

## Summary

This audit identifies dead code and legacy dependencies in the OMNIX codebase.

## Legacy Imports in src/omnix/

The hexagonal architecture layer (`src/omnix/`) intentionally imports from legacy modules:

| File | Legacy Imports | Purpose |
|------|---------------|---------|
| `bootstrap/main_entry.py` | omnix_config, omnix_services, omnix_core | Main entrypoint |
| `bootstrap/wsgi_entry.py` | omnix_dashboard | WSGI factory |
| `bootstrap/container.py` | omnix_core, omnix_services | DI Container |
| `infrastructure/adapters/*.py` | omnix_services, omnix_core | Adapter wrappers |
| `domain/trading/strategies/*.py` | omnix_core, omnix_services | Strategy re-exports |

**Status**: Expected behavior - these are thin wrappers that delegate to legacy code.

## Dead Code Identified

The following modules have **zero imports** and are candidates for removal:

### 1. omnix_services/alerts/
- `smart_alerts.py` - Alert system
- **Imports found**: 0
- **Status**: DORMANT - can be safely removed

### 2. omnix_strategies/regime_switcher.py
- Regime switching logic
- **Imports found**: 0
- **Status**: DORMANT - can be safely removed

### 3. omnix_services/on_chain_service/
- `on_chain_service.py` - On-chain data service
- **Imports found**: 0
- **Status**: DORMANT - can be safely removed

## Recommendations

1. **Phase 4.10**: Remove dead code after final verification
2. **Phase 4.11**: Update documentation to reflect removals
3. **Future**: Continue migrating legacy code to `src/omnix/` hexagonal structure

## Verification Commands

```bash
# Check for any imports of dead modules
grep -r "from omnix_services.alerts" --include="*.py"
grep -r "from omnix_strategies.regime_switcher" --include="*.py"
grep -r "from omnix_services.on_chain_service" --include="*.py"
```

## Next Steps

1. Configure import-linter with permissive contract
2. Remove dead code after architect review
3. Update MIGRATION_PLAN.md with Phase 4 completion
