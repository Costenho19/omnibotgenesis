# Session Log: January 28, 2026

## Summary
Improvements to OMNIX Web landing pages and navigation.

## Changes Made

### 1. Navigation Fix - `/terminal` Redirect
**File:** `omnix_web/src/App.tsx`

**Problem:** When users switched to port 3000, the URL retained `/terminal` from the Flask Dashboard, showing a black screen.

**Solution:** Added automatic redirects:
- `/terminal` → `/` (redirects to commercial landing)
- `*` (any unknown route) → `/` (catch-all redirect)

**Code:**
```tsx
import { Navigate } from 'react-router-dom'

<Route path="/terminal" element={<Navigate to="/" replace />} />
<Route path="*" element={<Navigate to="/" replace />} />
```

### 2. Port Configuration (Confirmed Working)
| Port | Application | Purpose |
|------|-------------|---------|
| 3000 | OMNIX Web (React/Vite) | Public landing pages |
| 5000 | Flask Dashboard | Internal analytics |
| 8080 | Streamlit | Shadow analytics |

### 3. Institutional Landing Enhancements (Completed)
Based on analysis of alternative HTML design, added:
- [x] FAQ section with 5 investor-focused questions
- [x] Comparison table: OMNIX vs Traditional Trading (7 features)
- [ ] Scroll-reveal animations (optional future enhancement)

### 4. Comparison Table Features
Added table comparing OMNIX vs Traditional Algorithmic Trading:
- Execution Model
- Default State
- Regime Awareness
- Risk Validation
- Auditability
- Capital Preservation
- Black Swan Protection

### 5. FAQ Section
Added 5 investor-focused FAQ questions:
1. Is OMNIX a trading bot?
2. How does OMNIX integrate with existing systems?
3. What makes OMNIX institutional-grade?
4. How is performance measured?
5. Who controls the risk parameters?

## Files Modified
- `omnix_web/src/App.tsx` - Added redirects
- `omnix_web/src/pages/InstitutionalPage.tsx` - Added FAQ and comparison table
- `replit.md` - Updated port configuration and recent changes
- `docs/history/2026-01/2026-01-28-landing-improvements.md` - This file

## Future Enhancements (Optional)
- [ ] Add scroll-reveal animations for sections
- [ ] Enhance animated counters

## Commits
- `628aa62` - Improve website navigation by redirecting terminal and invalid paths
