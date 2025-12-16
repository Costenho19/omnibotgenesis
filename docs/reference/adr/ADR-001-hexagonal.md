# ADR-001: Hexagonal Architecture Migration Strategy

**Status:** Accepted  
**Date:** December 11, 2025  
**Deciders:** OMNIX Development Team  
**Technical Story:** Migrate OMNIX V6.5.4d to clean hexagonal architecture for B2C scalability

---

## Context and Problem Statement

OMNIX V6.5.4d is an enterprise-grade trading system with ~114,000 lines of Python code across 268 files. The system runs 24/7 on Railway generating a paper trading track record for investor presentations ($1M seed at $11.5M pre-money).

**Current Problems:**
1. Hexagonal ports defined in `omnix/ports/` but adapters don't implement them
2. `main.py` is monolithic (cache cleanup, migrations, bot init, trading loop)
3. 80 bare except clauses causing silent failures
4. `enterprise_bot.py` has 7,812 lines
5. Services import infrastructure directly (no dependency inversion)
6. Test coverage <1%

**Constraint:** Cannot disrupt production during 500-trade milestone generation.

---

## Decision Drivers

1. **Production Stability**: Railway deployment must remain stable 24/7
2. **Incremental Migration**: No "big bang" rewrites
3. **Testability**: Enable unit testing without full infrastructure
4. **B2C Scalability**: Prepare for multi-tenant SaaS model
5. **Developer Velocity**: Easier onboarding for future team members

---

## Considered Options

### Option 1: Big Bang Rewrite
Rewrite entire system from scratch using clean architecture.

**Pros:** Clean slate, optimal design  
**Cons:** 3-6 months, high risk, track record blocked

### Option 2: Strangler Fig Pattern (SELECTED)
Gradually replace legacy components with new hexagonal modules while maintaining backward compatibility.

**Pros:** Zero downtime, rollback possible, production continues  
**Cons:** Longer duration, temporary code duplication

### Option 3: Freeze Until Funding
Defer all refactoring until post-funding.

**Pros:** No risk during track record  
**Cons:** Technical debt compounds, B2C launch delayed

---

## Decision Outcome

**Chosen Option:** Strangler Fig Pattern with phased rollout

### Implementation Phases

| Phase | Name | Duration | Trigger | Risk |
|-------|------|----------|---------|------|
| 0 | Foundation | 1-2 days | NOW | Low |
| 1 | Bootstrap & Config | 3-5 days | NOW | Low |
| 2 | Domain/Application | 1-2 weeks | 500 trades | Medium |
| 3 | Interfaces | 1 week | 500 trades | Medium |
| 4 | Cleanup | 1 week | +14 days stable | Low |

### Key Decisions

1. **Use AI Service as Reference Model**
   - `omnix_services/ai_service/` already implements SOLID + DI correctly
   - Replicate this pattern across all services

2. **Implement Existing Ports**
   - 8 protocols already defined in `omnix/ports/`
   - Create adapters that implement these protocols
   - Use dependency injection to wire adapters

3. **Create `src/omnix/` Structure**
   ```
   src/omnix/
   ├── domain/          # Business logic (no external deps)
   ├── application/     # Use cases, orchestration
   ├── infrastructure/  # Adapters (DB, Redis, APIs)
   ├── interfaces/      # Flask, Telegram, CLI
   ├── config/          # Pydantic settings
   └── bootstrap/       # DI container, startup
   ```

4. **Maintain Re-exports for Compatibility**
   ```python
   # Legacy import still works:
   from omnix_core.config import TradingProfiles
   
   # Actually forwards to:
   from src.omnix.config.profiles import TradingProfiles
   ```

5. **Phase 0-1 Safe to Execute Now**
   - Foundation work (tooling, docs) has no production impact
   - Bootstrap refactoring is isolated from trading logic

---

## Consequences

### Positive
- Production remains stable during migration
- Each phase is independently deployable and testable
- Enables unit testing of domain logic
- Prepares codebase for B2C multi-tenancy
- Improves developer onboarding

### Negative
- Temporary code duplication during migration
- Extended timeline (6-8 weeks total)
- Need to maintain backward compatibility

### Risks and Mitigation

| Risk | Mitigation |
|------|------------|
| Railway deploy fails | Feature flags, rollback scripts |
| Circular imports | Import linter in CI |
| Regression | Tests before moving code |
| Track record impact | Phases 2-4 blocked until 500 trades |

---

## Validation Criteria

### Phase 0 Complete When:
- [x] Dependency graph documented
- [x] `src/omnix/` structure created
- [x] pytest baseline established (13/13 tests pass)
- [x] mypy configured (pyproject.toml)
- [x] Module catalog documented
- [x] ADR-001 approved (Dec 11, 2025)

### Phase 1 Complete When:
- [ ] Pydantic settings centralizes all env vars
- [ ] DI container scaffolded
- [ ] `main.py` uses container
- [ ] Re-exports maintain compatibility
- [ ] Railway deploy works

### Migration Complete When:
- [ ] All services use dependency injection
- [ ] Adapters implement ports
- [ ] Test coverage >60% for core logic
- [ ] Legacy packages removed
- [ ] Documentation updated

---

## Related Documents

- `docs/architecture/MIGRATION_ROADMAP.md` - Detailed phase tasks
- `docs/core/TECHNICAL_DEBT.md` - Known issues registry
- `docs/architecture/phase0/DEPENDENCY_GRAPH.md` - Import analysis
- `docs/architecture/MODULE_CATALOG.md` - Module documentation (pending)

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2025-12-11 | Initial ADR created | OMNIX Dev |
| 2025-12-11 | Added Phase 0 validation | OMNIX Dev |

---

*This ADR follows the MADR template (Markdown Any Decision Records)*
