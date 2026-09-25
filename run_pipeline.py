"""
Unified CLI Entrypoint for FlashEats Operational Data Pipeline
Class 8: Dependable Pipeline (Repeatable, Idempotent, Monitored, Resilient)

Pipeline Stages:
1. Ingest (Multi-Mode Retrieval & Completeness Proofs)
2. Validate (Data Profiling, Calibrations & Quarantine DLQ Routing)
3. Model (Workflow State Machine & 5-Stage Delay Decomposition)
4. Marts (Gold Analytics & Intervention Simulations)
5. Report (Terminal Dashboard & Markdown Evidence Export)

Outputs:
- run_manifest.json (Immutable execution audit trail)
"""

import os
import sys
import time
import json
import argparse
from datetime import datetime

# Local pipeline modules
from src.generator.generate_all import generate_flasheats_dataset
from src.ingest.ingest_manager import IngestionManager
from src.validate.validator import DataValidator
from src.model.state_machine import WorkflowStateMachine
from src.marts.gold_marts import GoldMartsManager
from src.reporting.dashboard import FlashEatsReporter

def run_flasheats_pipeline(
    date_str: str = "2026-09-25",
    seed: int = 42,
    force_regenerate: bool = False,
    circuit_breaker_pct: float = 5.0
):
    start_time = time.time()
    run_id = f"FDE-RUN-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
    
    print("\n" + "="*80)
    print(f"       STARTING FLASHEATS REPEATABLE PIPELINE RUN: {run_id}")
    print(f"       Batch Date: {date_str} | Seed: {seed} | Circuit Breaker: {circuit_breaker_pct}%")
    print("="*80 + "\n")

    manifest = {
        "run_id": run_id,
        "pipeline_version": "1.0.0",
        "batch_date": date_str,
        "started_at": datetime.utcnow().isoformat() + "Z",
        "steps": {},
        "status": "RUNNING",
        "quarantine_trip_warning": False,
        "errors": []
    }

    try:
        # Step 0: Ensure Raw Data Exists
        raw_db = "data/raw/orders_platform.db"
        if force_regenerate or not os.path.exists(raw_db):
            print("[Step 0] Generating Multi-System Raw Operational Data...")
            generate_flasheats_dataset(output_dir="data/raw", num_orders=6000, seed=seed, date_str=date_str)
            manifest["steps"]["step0_generation"] = "GENERATED"
        else:
            print("[Step 0] Existing raw operational data found in 'data/raw/'. Preserving bronze landing.")
            manifest["steps"]["step0_generation"] = "EXISTING_PRESERVED"

        # Step 1: Ingest & Completeness Proofs
        print("\n[Step 1] Ingesting Multi-Mode Sources into Immutable Bronze Layer...")
        ingest_mgr = IngestionManager()
        ingest_proof = ingest_mgr.run_all()
        manifest["steps"]["step1_ingest"] = {
            "batch_id": ingest_mgr.batch_id,
            "completeness_verified": ingest_proof["completeness_verified"],
            "gmv_control_total_cents": ingest_proof["control_totals"]["gmv_subtotal_cents"]
        }

        # Step 2: Validate & Quarantine
        print("\n[Step 2] Profiling, Validating, Calibrating & Quarantining...")
        validator = DataValidator()
        val_summary = validator.validate_and_calibrate()
        
        quar_count = val_summary["quarantine_summary"]["total_quarantined"]
        clean_count = val_summary["quarantine_summary"]["clean_records_passed_to_silver"]
        total_records = quar_count + clean_count
        quar_rate_pct = round((quar_count / total_records) * 100.0, 2) if total_records > 0 else 0.0

        manifest["steps"]["step2_validate"] = {
            "total_evaluated": total_records,
            "clean_records": clean_count,
            "quarantined_records": quar_count,
            "quarantine_rate_pct": quar_rate_pct,
            "clock_drift_calibrations": val_summary["calibration_audit"]["clock_drift_calibrated_count"],
            "bump_bar_imputations": val_summary["calibration_audit"]["food_ready_imputed_count"],
            "network_jitter_clamps": val_summary["calibration_audit"]["network_jitter_clamped_count"]
        }

        # Circuit breaker check
        if quar_rate_pct > circuit_breaker_pct:
            warning_msg = f"Quarantine rate of {quar_rate_pct}% exceeds circuit breaker threshold ({circuit_breaker_pct}%)!"
            print(f"[!] CIRCUIT BREAKER WARNING: {warning_msg}")
            manifest["quarantine_trip_warning"] = True
            manifest["errors"].append(warning_msg)

        # Step 3: Workflow State Machine Modeling
        print("\n[Step 3] Reconstructing Workflow State Machine & Decomposing Delay Stages...")
        sm = WorkflowStateMachine()
        fact_df = sm.build_fact_order_lifecycle()
        manifest["steps"]["step3_workflow_model"] = {
            "completed_orders": int(fact_df["is_completed"].sum()),
            "cancelled_orders": int((~fact_df["is_completed"]).sum()),
            "primary_bottleneck": str(fact_df["primary_delay_bottleneck"].mode()[0])
        }

        # Step 4: Gold Analytics & Intervention Simulations
        print("\n[Step 4] Generating Gold Marts & Simulating Operational Interventions...")
        marts_mgr = GoldMartsManager()
        kpis, clusters, sims = marts_mgr.run_all()
        manifest["steps"]["step4_gold_marts"] = {
            "p50_otd_min": float(kpis["p50_otd_min"].iloc[0]),
            "p90_otd_min": float(kpis["p90_otd_min"].iloc[0]),
            "sla_breach_rate_pct": float(kpis["sla_breach_rate_pct"].iloc[0]),
            "staged_dispatch_p90_sim_min": float(sims.loc[sims['scenario'].str.contains('Staged Offset'), 'p90_otd_min'].iloc[0])
        }

        # Step 5: Reporting & Evidence Export
        print("\n[Step 5] Rendering Executive Dashboard & Exporting Evidence Tables...")
        reporter = FlashEatsReporter()
        reporter.print_terminal_dashboard()
        reporter.export_evidence_markdown()
        manifest["steps"]["step5_reporting"] = "EXPORTED"

        duration = round(time.time() - start_time, 2)
        manifest["status"] = "SUCCESS_WITH_WARNINGS" if manifest["quarantine_trip_warning"] else "SUCCESS"
        manifest["completed_at"] = datetime.utcnow().isoformat() + "Z"
        manifest["duration_seconds"] = duration

        with open("run_manifest.json", "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        print(f"[+] PIPELINE RUN COMPLETED IN {duration}s. Manifest written to 'run_manifest.json'.\n")
        return manifest

    except Exception as e:
        manifest["status"] = "FAILED"
        manifest["errors"].append(str(e))
        manifest["failed_at"] = datetime.utcnow().isoformat() + "Z"
        with open("run_manifest.json", "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        print(f"[!] PIPELINE EXECUTION FAILED: {str(e)}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FlashEats Dependable FDE Pipeline Runner")
    parser.add_argument("--date", type=str, default="2026-09-25", help="Target batch date (YYYY-MM-DD)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for repeatable data generation")
    parser.add_argument("--force-regenerate", action="store_true", help="Force regeneration of raw datasets")
    parser.add_argument("--circuit-breaker-threshold", type=float, default=5.0, help="Quarantine rate alarm threshold (pct)")
    args = parser.parse_args()

    run_flasheats_pipeline(
        date_str=args.date,
        seed=args.seed,
        force_regenerate=args.force_regenerate,
        circuit_breaker_pct=args.circuit_breaker_threshold
    )
