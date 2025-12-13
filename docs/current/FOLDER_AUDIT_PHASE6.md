# OMNIX Folder Audit - Phase 6 Consolidation Plan

**Date**: December 13, 2025  
**Version**: V7.0 Migration  
**Status**: 🔄 IN PROGRESS

## Executive Summary

Automated import audit of OMNIX folder structure to identify dead code and consolidation opportunities.

## Audit Results

### ✅ ESSENTIAL (Keep - Active Imports)

| Folder | Import Count | Purpose | Status |
|--------|-------------|---------|--------|
| `omnix_core/` | 325+ | Bot, strategies, cache, trading | ✅ KEEP |
| `omnix_services/` | 200+ | AI, Telegram, Database, Execution | ✅ KEEP |
| `omnix_config/` | 50+ | Env manager, configuration | ✅ KEEP |
| `omnix_dashboard/` | 80+ | Flask API, 12 widgets | ✅ KEEP |
| `omnix_api/` | 20+ | API endpoints | ✅ KEEP |
| `src/omnix/` | Growing | New hexagonal architecture V7.0 | ✅ KEEP |
| `docs/` | N/A | Documentation | ✅ KEEP |
| `tests/` | N/A | Test suite | ✅ KEEP |
| `scripts/` | N/A | Utility scripts | ✅ KEEP |
| `sql/` | N/A | SQL migrations | ✅ KEEP |

### ⚠️ DEAD CODE (Remove)

| Folder | Import Count | Evidence | Action |
|--------|-------------|----------|--------|
| `omnix_reports/` | **0** | `grep "from omnix_reports\|import omnix_reports"` = 0 matches | **DELETE** |
| `reports/` | **0** | Contains only 1 PDF artifact | **MOVE to docs/history/** |

### 🔄 REVIEW (Consolidate)

| Folder | Import Count | Notes | Action |
|--------|-------------|-------|--------|
| `omnix_risk/` | **1** | Only internal reference in dead_man_switch.py | **CONSOLIDATE to src/omnix/** |
| `omnix_testing/` | **24** | All internal (backtesting tools import each other) | **KEEP as dev tools** |
| `omnix/ports/` | **18** | DUPLICATED with src/omnix/ports/ | **MIGRATE refs → DELETE legacy** |

## Phase 6 Execution Plan

### Step 1: Remove Dead Code
```bash
# Remove omnix_reports (0 external imports)
rm -rf omnix_reports/

# Move reports/ artifact to docs history
mkdir -p docs/history/investor_reports/
mv reports/*.pdf docs/history/investor_reports/
rm -rf reports/
```

### Step 2: Consolidate omnix_risk/
Files to migrate to `src/omnix/domain/risk/`:
- `audit_logger.py` → May already exist in new architecture
- `cascade_protection.py` → Evaluate if needed
- `dead_man_switch.py` → Evaluate if needed
- `portfolio_summary.py` → Evaluate if needed
- `reactivation_engine.py` → Evaluate if needed
- `usd_risk_calculator.py` → Evaluate if needed

### Step 3: Migrate omnix/ports/ → src/omnix/ports/
1. Update test imports from `omnix.ports` to `src.omnix.ports`
2. Verify all references migrated
3. Delete `omnix/ports/`

### Step 4: Evaluate omnix_testing/
Keep as standalone dev tools but:
- Move to `tools/backtesting/` for clarity
- Or keep in place if disruption risk is high

## Verification Commands

```bash
# Verify no remaining imports after deletion
grep -r "from omnix_reports" --include="*.py"
grep -r "from reports\." --include="*.py"

# Verify omnix/ports migration complete
grep -r "from omnix\.ports" --include="*.py"
grep -r "import omnix\.ports" --include="*.py"
```

## Risk Assessment

| Action | Risk | Mitigation |
|--------|------|------------|
| Delete omnix_reports/ | LOW | 0 imports confirmed |
| Delete reports/ | LOW | Only PDF artifact |
| Consolidate omnix_risk/ | MEDIUM | Check if risk functions used at runtime |
| Migrate omnix/ports/ | MEDIUM | Update test imports first |
| Move omnix_testing/ | LOW | Dev tools only |

## Post-Cleanup Structure

```
OMNIX/
├── src/omnix/           <- Hexagonal V7.0 (growing)
├── omnix_core/          <- Legacy runtime (essential)
├── omnix_services/      <- Legacy services (essential)
├── omnix_config/        <- Configuration (essential)
├── omnix_dashboard/     <- Dashboard (essential)
├── omnix_api/           <- API (essential)
├── omnix_testing/       <- Dev/backtesting tools (optional)
├── docs/                <- Documentation
├── tests/               <- Test suite
├── scripts/             <- Utility scripts
└── sql/                 <- Migrations
```

**Folders Removed**: omnix_reports/, reports/, omnix/ports/, omnix_risk/ (after consolidation)

---

*Audit completed: December 13, 2025*  
*Auditor: OMNIX Automated Import Scanner*
