"""
Stage 2: Data Profiling, Multi-Tier Business Validation & Quarantine Engine
FDE Discipline: ZERO silent dropping of flawed data.
Categorizes data into:
- Clean & Defensibly Calibrated (proceeds to Silver layer)
- Quarantined (isolated in Dead-Letter Queue with error code, severity, and context)

Handles 5 real-world messy operational anomalies:
1. POS Hardware Clock Drift (-180s to +300s) -> Calibrated with audit flag
2. Missing KDS Bump Bar ('food_ready_at' IS NULL) -> Imputed with lower bound & flag
3. Driver Re-dispatch Churn (1:N attempts) -> Unbundled into attempt tracking
4. Cancelled / Aborted Orders -> Handled gracefully in funnel modeling
5. Mobile Network Jitter (Inverted Arrived/Pickup < 30s) -> Clamped with audit flag
"""

import os
import json
from datetime import datetime
import pandas as pd
import numpy as np

class DataValidator:
    def __init__(
        self,
        bronze_dir: str = "data/bronze",
        silver_dir: str = "data/silver",
        quarantine_dir: str = "data/quarantine"
    ):
        self.bronze_dir = bronze_dir
        self.silver_dir = silver_dir
        self.quarantine_dir = quarantine_dir
        os.makedirs(self.silver_dir, exist_ok=True)
        os.makedirs(self.quarantine_dir, exist_ok=True)
        
        self.validation_manifest = {
            "validation_timestamp": datetime.utcnow().isoformat() + "Z",
            "profiling_summary": {},
            "anomaly_detections": {},
            "calibration_audit": {},
            "quarantine_summary": {}
        }

    def run_profiling(self, orders_df: pd.DataFrame, kds_df: pd.DataFrame, dispatch_df: pd.DataFrame) -> dict:
        """Profiles raw data distributions and quantifies anomaly prevalence."""
        profiling = {
            "total_orders": len(orders_df),
            "completed_orders": int((orders_df["order_status"] == "COMPLETED").sum()),
            "cancelled_orders": int((orders_df["order_status"] == "CANCELLED").sum()),
            "total_dispatch_attempts": len(dispatch_df),
            "unique_dispatched_orders": int(dispatch_df["order_id"].nunique()),
            "total_kds_tickets": len(kds_df),
            "missing_kds_food_ready_count": int(kds_df["food_ready_at"].isna().sum()),
            "missing_kds_food_ready_pct": round(float(kds_df["food_ready_at"].isna().mean()) * 100, 2),
        }

        # Multi-attempt re-dispatch count
        attempts_per_order = dispatch_df.groupby("order_id")["dispatch_id"].count()
        churn_orders = (attempts_per_order > 1).sum()
        profiling["orders_with_driver_churn"] = int(churn_orders)
        profiling["driver_churn_order_pct"] = round(float(churn_orders / len(orders_df)) * 100, 2)

        self.validation_manifest["profiling_summary"] = profiling
        return profiling

    def validate_and_calibrate(self):
        """
        Executes business rules, isolates critical errors to Quarantine,
        and applies defensible calibrations to recoverable anomalies.
        """
        print("[*] Starting Data Profiling & Business Validation...")
        
        orders_df = pd.read_parquet(os.path.join(self.bronze_dir, "bronze_orders.parquet"))
        merchants_df = pd.read_parquet(os.path.join(self.bronze_dir, "bronze_merchants.parquet"))
        kds_df = pd.read_parquet(os.path.join(self.bronze_dir, "bronze_kds_logs.parquet"))
        dispatch_df = pd.read_parquet(os.path.join(self.bronze_dir, "bronze_dispatch_attempts.parquet"))
        support_df = pd.read_parquet(os.path.join(self.bronze_dir, "bronze_support_tickets.parquet"))

        self.run_profiling(orders_df, kds_df, dispatch_df)

        quarantine_records = []

        # -------------------------------------------------------------
        # 1. VALIDATE DISPATCH DATA & SEPARATE ATTEMPTS
        # -------------------------------------------------------------
        # Filter for terminal successful driver assignment vs prior rejections
        terminal_dispatches = dispatch_df[dispatch_df["dispatch_status"].isin(["COMPLETED", "CANCELLED_BY_SYSTEM"])].copy()
        rejected_dispatches = dispatch_df[dispatch_df["dispatch_status"] == "REJECTED"].copy()

        # Save rejected attempts for driver churn analytics
        rejected_dispatches.to_parquet(os.path.join(self.silver_dir, "fact_dispatch_churn.parquet"), index=False)

        # Convert timestamps for terminal dispatches to UTC
        for col in ["offered_at", "responded_at", "arrived_at_store_at", "picked_up_at", "delivered_at"]:
            terminal_dispatches[col] = pd.to_datetime(terminal_dispatches[col], utc=True)

        # Detect Anomaly 5: Mobile Network Jitter (Arrived reported after pickup)
        jitter_mask = (
            terminal_dispatches["arrived_at_store_at"].notna() &
            terminal_dispatches["picked_up_at"].notna() &
            (terminal_dispatches["arrived_at_store_at"] > terminal_dispatches["picked_up_at"])
        )
        jitter_count = int(jitter_mask.sum())
        
        terminal_dispatches["network_jitter_clamped_flag"] = False
        
        # Check severity of jitter: if delta <= 35s, clamp to picked_up - 1s; if > 35s, quarantine
        for idx in terminal_dispatches[jitter_mask].index:
            t_arrived = terminal_dispatches.loc[idx, "arrived_at_store_at"]
            t_picked = terminal_dispatches.loc[idx, "picked_up_at"]
            delta_sec = (t_arrived - t_picked).total_seconds()
            
            if delta_sec <= 35.0:
                # Defensible calibration: Mall/elevator queueing jitter
                terminal_dispatches.loc[idx, "arrived_at_store_at"] = t_picked - pd.Timedelta(seconds=1)
                terminal_dispatches.loc[idx, "network_jitter_clamped_flag"] = True
            else:
                # Severe corruption -> Quarantine
                quarantine_records.append({
                    "entity_id": terminal_dispatches.loc[idx, "order_id"],
                    "source_system": "DISPATCH_API",
                    "error_code": "CRITICAL_TEMPORAL_INVERSION_PICKUP_ARRIVED",
                    "error_description": f"Rider arrived at store {delta_sec}s AFTER pickup (exceeds 35s jitter limit)",
                    "severity": "CRITICAL_DROP",
                    "raw_payload": str(terminal_dispatches.loc[idx].to_dict()),
                    "quarantined_at": datetime.utcnow().isoformat()
                })

        # -------------------------------------------------------------
        # 2. VALIDATE & CALIBRATE KDS PREP LOGS
        # -------------------------------------------------------------
        # Merge KDS with orders (order_timestamp) and terminal dispatch (picked_up_at)
        orders_ts = orders_df[["order_id", "order_timestamp"]].copy()
        orders_ts["order_timestamp"] = pd.to_datetime(orders_ts["order_timestamp"], utc=True)
        
        kds_merged = kds_df.merge(
            terminal_dispatches[["order_id", "picked_up_at"]],
            on="order_id",
            how="left"
        ).merge(orders_ts, on="order_id", how="left")
        
        kds_merged["ticket_printed_at"] = pd.to_datetime(kds_merged["ticket_printed_at"], utc=True)
        kds_merged["food_ready_at"] = pd.to_datetime(kds_merged["food_ready_at"], utc=True)

        kds_merged["clock_drift_calibrated_flag"] = False
        kds_merged["is_food_ready_imputed_flag"] = False
        kds_merged["calibrated_ticket_printed_at"] = kds_merged["ticket_printed_at"]
        kds_merged["calibrated_food_ready_at"] = kds_merged["food_ready_at"]

        # Anomaly 1A: POS Backward Clock Drift (ticket_printed_at recorded before order was placed!)
        backward_drift_mask = (
            kds_merged["ticket_printed_at"].notna() &
            kds_merged["order_timestamp"].notna() &
            (kds_merged["ticket_printed_at"] < kds_merged["order_timestamp"])
        )
        backward_drift_count = int(backward_drift_mask.sum())

        for idx in kds_merged[backward_drift_mask].index:
            t_printed = kds_merged.loc[idx, "ticket_printed_at"]
            t_order = kds_merged.loc[idx, "order_timestamp"]
            drift_sec = (t_order - t_printed).total_seconds()

            if drift_sec <= 300.0: # within 5 min POS tablet drift window
                # Calibrate: Ticket printed 15s after order placement, shift food_ready accordingly
                t_calib_printed = t_order + pd.Timedelta(seconds=15)
                kds_merged.loc[idx, "calibrated_ticket_printed_at"] = t_calib_printed
                if pd.notna(kds_merged.loc[idx, "calibrated_food_ready_at"]):
                    kds_merged.loc[idx, "calibrated_food_ready_at"] += pd.Timedelta(seconds=drift_sec)
                kds_merged.loc[idx, "clock_drift_calibrated_flag"] = True
            else:
                quarantine_records.append({
                    "entity_id": kds_merged.loc[idx, "order_id"],
                    "source_system": "KDS_CSV",
                    "error_code": "SEVERE_BACKWARD_CLOCK_DRIFT_EXCEEDS_5MIN",
                    "error_description": f"KDS ticket printed {drift_sec}s BEFORE order was placed",
                    "severity": "CRITICAL_DROP",
                    "raw_payload": str(kds_merged.loc[idx].to_dict()),
                    "quarantined_at": datetime.utcnow().isoformat()
                })

        # Anomaly 1B: POS Forward Clock Drift (ready timestamp recorded after rider pickup)
        forward_drift_mask = (
            kds_merged["calibrated_food_ready_at"].notna() &
            kds_merged["picked_up_at"].notna() &
            (kds_merged["calibrated_food_ready_at"] > kds_merged["picked_up_at"])
        )
        forward_drift_count = int(forward_drift_mask.sum())

        for idx in kds_merged[forward_drift_mask].index:
            t_ready = kds_merged.loc[idx, "calibrated_food_ready_at"]
            t_pickup = kds_merged.loc[idx, "picked_up_at"]
            drift_sec = (t_ready - t_pickup).total_seconds()

            if drift_sec <= 300.0:
                kds_merged.loc[idx, "calibrated_food_ready_at"] = t_pickup - pd.Timedelta(seconds=30)
                kds_merged.loc[idx, "clock_drift_calibrated_flag"] = True
            else:
                quarantine_records.append({
                    "entity_id": kds_merged.loc[idx, "order_id"],
                    "source_system": "KDS_CSV",
                    "error_code": "SEVERE_FORWARD_CLOCK_DRIFT_EXCEEDS_5MIN",
                    "error_description": f"KDS ready timestamp is {drift_sec}s after courier pickup",
                    "severity": "CRITICAL_DROP",
                    "raw_payload": str(kds_merged.loc[idx].to_dict()),
                    "quarantined_at": datetime.utcnow().isoformat()
                })

        drift_count = backward_drift_count + forward_drift_count

        # Anomaly 2: Missing KDS Bump Bar Imputation (Cook didn't tap screen)
        missing_ready_mask = (
            kds_merged["calibrated_food_ready_at"].isna() &
            kds_merged["picked_up_at"].notna()
        )
        imputed_count = int(missing_ready_mask.sum())

        for idx in kds_merged[missing_ready_mask].index:
            t_pickup = kds_merged.loc[idx, "picked_up_at"]
            # Conservative lower bound imputation: 45s prior to courier handover
            kds_merged.loc[idx, "calibrated_food_ready_at"] = t_pickup - pd.Timedelta(seconds=45)
            kds_merged.loc[idx, "is_food_ready_imputed_flag"] = True


        # -------------------------------------------------------------
        # 3. QUARANTINE ROUTING & AUDIT EXPORT
        # -------------------------------------------------------------
        quarantine_df = pd.DataFrame(quarantine_records)
        quarantine_path = os.path.join(self.quarantine_dir, "quarantine_audit.parquet")
        quarantine_df.to_parquet(quarantine_path, index=False)

        # Exclude quarantined orders from Silver tables
        quarantined_ids = set(quarantine_df["entity_id"].tolist()) if not quarantine_df.empty else set()
        
        clean_orders = orders_df[~orders_df["order_id"].isin(quarantined_ids)].copy()
        clean_kds = kds_merged[~kds_merged["order_id"].isin(quarantined_ids)].copy()
        clean_dispatch = terminal_dispatches[~terminal_dispatches["order_id"].isin(quarantined_ids)].copy()

        # Save cleaned & calibrated silver intermediate tables
        clean_orders.to_parquet(os.path.join(self.silver_dir, "silver_orders.parquet"), index=False)
        merchants_df.to_parquet(os.path.join(self.silver_dir, "silver_merchants.parquet"), index=False)
        clean_kds.to_parquet(os.path.join(self.silver_dir, "silver_kds_calibrated.parquet"), index=False)
        clean_dispatch.to_parquet(os.path.join(self.silver_dir, "silver_dispatch_terminal.parquet"), index=False)
        support_df.to_parquet(os.path.join(self.silver_dir, "silver_support_tickets.parquet"), index=False)

        # Audit manifest
        self.validation_manifest["anomaly_detections"] = {
            "pos_clock_drift_instances": drift_count,
            "missing_bump_bar_instances": imputed_count,
            "network_jitter_instances": jitter_count,
            "quarantined_records_count": len(quarantine_records)
        }
        self.validation_manifest["calibration_audit"] = {
            "clock_drift_calibrated_count": int(clean_kds["clock_drift_calibrated_flag"].sum()),
            "food_ready_imputed_count": int(clean_kds["is_food_ready_imputed_flag"].sum()),
            "network_jitter_clamped_count": int(clean_dispatch["network_jitter_clamped_flag"].sum())
        }
        self.validation_manifest["quarantine_summary"] = {
            "quarantine_file": quarantine_path,
            "total_quarantined": len(quarantine_records),
            "clean_records_passed_to_silver": len(clean_orders)
        }

        report_path = os.path.join(self.silver_dir, "validation_profile_report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(self.validation_manifest, f, indent=2)

        print("[+] Validation & Profiling completed successfully:")
        print(f"    - POS Clock Drift instances detected & calibrated: {drift_count}")
        print(f"    - Missing KDS bump bars defensibly imputed: {imputed_count}")
        print(f"    - Network jitter inversions clamped: {jitter_count}")
        print(f"    - Clean orders passed to Silver: {len(clean_orders)}")
        print(f"    - Critical anomalies quarantined: {len(quarantine_records)} (Logged to {quarantine_path})")

        return self.validation_manifest

if __name__ == "__main__":
    validator = DataValidator()
    validator.validate_and_calibrate()
