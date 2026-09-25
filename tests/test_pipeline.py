"""
Unit & Integration Tests for FlashEats FDE Pipeline
Validates completeness proofs, validation rules, state machine math, and idempotency.
"""

import os
import json
import pytest
import pandas as pd

from src.ingest.ingest_manager import IngestionManager
from src.validate.validator import DataValidator
from src.model.state_machine import WorkflowStateMachine
from src.marts.gold_marts import GoldMartsManager

def test_ingest_completeness_and_financial_reconciliation():
    ingest_mgr = IngestionManager()
    proof = ingest_mgr.run_all()
    
    assert proof["completeness_verified"] is True
    assert proof["control_totals"]["primary_key_integrity"]["orders_unique"] is True
    assert proof["control_totals"]["primary_key_integrity"]["line_items_unique"] is True
    assert proof["control_totals"]["line_items_reconciliation_delta_cents"] == 0

def test_validation_and_quarantine_integrity():
    validator = DataValidator()
    summary = validator.validate_and_calibrate()
    
    assert summary["quarantine_summary"]["total_quarantined"] > 0
    assert summary["calibration_audit"]["clock_drift_calibrated_count"] > 0
    assert summary["calibration_audit"]["food_ready_imputed_count"] > 0
    assert summary["calibration_audit"]["network_jitter_clamped_count"] > 0
    
    quarantine_df = pd.read_parquet(summary["quarantine_summary"]["quarantine_file"])
    assert len(quarantine_df) == summary["quarantine_summary"]["total_quarantined"]
    assert "error_code" in quarantine_df.columns

def test_workflow_state_machine_stages():
    sm = WorkflowStateMachine()
    fact_df = sm.build_fact_order_lifecycle()
    
    completed = fact_df[fact_df["is_completed"]]
    assert len(completed) > 5000
    assert (completed["stage1_merchant_lag_min"] >= 0).all()
    assert (completed["rider_store_wait_min"] >= 0).all()
    assert (completed["stage5_last_mile_min"] >= 0).all()
    assert (completed["total_otd_min"] > 0).all()

def test_gold_marts_kpi_consistency():
    marts = GoldMartsManager()
    kpis, clusters, sims = marts.run_all()
    
    assert len(kpis) == 1
    assert kpis["p90_otd_min"].iloc[0] > kpis["p50_otd_min"].iloc[0]
    assert len(clusters) == 3
    assert len(sims) == 4
    
    # Intervention 1 must show lower P90 OTD than Baseline
    base_p90 = sims.loc[sims["scenario"].str.startswith("Baseline"), "p90_otd_min"].iloc[0]
    staged_p90 = sims.loc[sims["scenario"].str.contains("Staged Offset"), "p90_otd_min"].iloc[0]
    assert staged_p90 < base_p90

def test_idempotency_consecutive_runs():
    """Validates that running the pipeline twice consecutively produces identical outputs."""
    ingest_mgr = IngestionManager()
    proof1 = ingest_mgr.run_all()
    proof2 = ingest_mgr.run_all()
    
    assert proof1["control_totals"]["gmv_subtotal_cents"] == proof2["control_totals"]["gmv_subtotal_cents"]
