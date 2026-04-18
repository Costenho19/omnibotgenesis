-- Migration: 001_opportunity_baseline
-- Date: 2026-01-14
-- Purpose: ADR-008 Opportunity Tracker baseline table for institutional auditability
-- Reference: docs/reference/adr/ADR-008-opportunity-tracker.md

CREATE TABLE IF NOT EXISTS opportunity_baseline (
  id SERIAL PRIMARY KEY,
  snapshot_date DATE NOT NULL,
  snapshot_day INTEGER NOT NULL,
  version VARCHAR(50) NOT NULL,
  total_avoided INTEGER NOT NULL,
  total_missed INTEGER NOT NULL,
  avoided_est_loss NUMERIC(15,2),
  missed_est_profit NUMERIC(15,2),
  net_value NUMERIC(15,2),
  recommendation VARCHAR(50),
  thresholds JSONB,
  metadata JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE opportunity_baseline IS 'ADR-008: Historical snapshots for opportunity tracker audits';
COMMENT ON COLUMN opportunity_baseline.snapshot_day IS 'Day number in 30-day tracking period';
COMMENT ON COLUMN opportunity_baseline.net_value IS 'missed_est_profit - avoided_est_loss (negative = protecting)';
COMMENT ON COLUMN opportunity_baseline.thresholds IS 'JSON with missed/avoided/near_miss criteria thresholds';
COMMENT ON COLUMN opportunity_baseline.metadata IS 'ADR reference, review date, shadow events context';

-- Day 1 Baseline Snapshot (2026-01-14)
INSERT INTO opportunity_baseline (
  snapshot_date,
  snapshot_day,
  version,
  total_avoided,
  total_missed,
  avoided_est_loss,
  missed_est_profit,
  net_value,
  recommendation,
  thresholds,
  metadata
) VALUES (
  '2026-01-14',
  1,
  'V6.5.4e INSTITUTIONAL+',
  479,
  0,
  239500.00,
  0.00,
  -239500.00,
  'KEEP_CONSERVATIVE',
  '{"missed": {"coherence": ">=45%", "ema": "25-40%", "black_swan": "<=0.5"}, "avoided": {"coherence": "<30%", "black_swan": ">0.5"}, "near_miss": {"ema": "28-35%", "coherence": ">=40%", "black_swan": "<=0.6"}}',
  '{"adr": "ADR-008", "review_date": "2026-02-13", "tracking_start": "2026-01-14", "shadow_events_total": 55820, "veto_types": {"COHERENCE_GATE": 28017, "BLACK_SWAN": 27803}}'
) ON CONFLICT DO NOTHING;
