"""
Stage 3: Workflow State Machine Modeling & Bottleneck Decomposition
Class 7 Skill: Represent entities, events/states, interactions/outcomes.

Decomposes the end-to-end order lifecycle into 5 distinct operational stages:
- Stage 1: Merchant Lag (t_confirmed - t_placed)
- Stage 2: Kitchen Prep Overrun ((t_food_ready - t_confirmed) - estimated_prep)
- Stage 3: Dispatch & Courier Travel to Store (t_arrived_store - t_confirmed)
- Stage 4: Store Synchronization Gap:
    * Courier Store Wait: Courier idle waiting for kitchen (t_food_ready > t_arrived_store)
    * Cold Food Counter Dwell: Food waiting for courier (t_arrived_store > t_food_ready)
- Stage 5: Last-Mile Doorstep Transit (t_delivered - t_picked_up)

Builds unified Silver model: `fact_order_lifecycle.parquet`
"""

import os
import pandas as pd
import numpy as np

class WorkflowStateMachine:
    def __init__(self, silver_dir: str = "data/silver"):
        self.silver_dir = silver_dir

    def build_fact_order_lifecycle(self) -> pd.DataFrame:
        print("[*] Reconstructing Workflow State Machine & Decomposing Delay Stages...")
        
        orders = pd.read_parquet(os.path.join(self.silver_dir, "silver_orders.parquet"))
        merchants = pd.read_parquet(os.path.join(self.silver_dir, "silver_merchants.parquet"))
        kds = pd.read_parquet(os.path.join(self.silver_dir, "silver_kds_calibrated.parquet"))
        dispatch = pd.read_parquet(os.path.join(self.silver_dir, "silver_dispatch_terminal.parquet"))
        support = pd.read_parquet(os.path.join(self.silver_dir, "silver_support_tickets.parquet"))

        # Standardize datetimes
        orders["order_placed_at"] = pd.to_datetime(orders["order_timestamp"], utc=True)
        orders["promised_sla_at"] = pd.to_datetime(orders["promised_sla_timestamp"], utc=True)
        
        kds["kds_printed_at"] = pd.to_datetime(kds["calibrated_ticket_printed_at"], utc=True)
        kds["kds_ready_at"] = pd.to_datetime(kds["calibrated_food_ready_at"], utc=True)

        for col in ["offered_at", "responded_at", "arrived_at_store_at", "picked_up_at", "delivered_at"]:
            dispatch[col] = pd.to_datetime(dispatch[col], utc=True)

        # Merge entities into unified workflow lifecycle
        fact = orders.merge(
            merchants[["merchant_id", "merchant_name", "cluster_id", "cuisine_type", "kitchen_capacity", "nominal_prep_min"]],
            on="merchant_id",
            how="inner"
        ).merge(
            kds[["order_id", "kds_printed_at", "kds_ready_at", "active_kitchen_queue_depth", "estimated_prep_sec", "clock_drift_calibrated_flag", "is_food_ready_imputed_flag"]],
            on="order_id",
            how="inner"
        ).merge(
            dispatch[["order_id", "driver_id", "attempt_number", "offered_at", "responded_at", "arrived_at_store_at", "picked_up_at", "delivered_at", "network_jitter_clamped_flag"]],
            on="order_id",
            how="left"
        )

        # Merge support ticket summary
        support_agg = support.groupby("order_id").agg(
            ticket_count=("ticket_id", "count"),
            refund_amount_cents=("compensation_amount_cents", "sum"),
            min_csat=("csat_score", "min")
        ).reset_index()

        fact = fact.merge(support_agg, on="order_id", how="left")
        fact["ticket_count"] = fact["ticket_count"].fillna(0).astype(int)
        fact["refund_amount_cents"] = fact["refund_amount_cents"].fillna(0).astype(int)

        # -------------------------------------------------------------
        # STAGE CALCULATIONS (Durations in Minutes)
        # -------------------------------------------------------------
        # Stage 1: Merchant Confirmation Lag
        fact["stage1_merchant_lag_min"] = (fact["kds_printed_at"] - fact["order_placed_at"]).dt.total_seconds() / 60.0
        fact["stage1_merchant_lag_min"] = fact["stage1_merchant_lag_min"].clip(lower=0)

        # Stage 2: Kitchen Prep Time & Overrun
        fact["actual_prep_min"] = (fact["kds_ready_at"] - fact["kds_printed_at"]).dt.total_seconds() / 60.0
        fact["nominal_prep_min"] = fact["estimated_prep_sec"] / 60.0
        fact["stage2_prep_overrun_min"] = (fact["actual_prep_min"] - fact["nominal_prep_min"]).clip(lower=0)

        # Stage 3: Dispatch & Courier Travel to Store
        fact["stage3_dispatch_and_travel_min"] = (fact["arrived_at_store_at"] - fact["kds_printed_at"]).dt.total_seconds() / 60.0
        fact["stage3_dispatch_and_travel_min"] = fact["stage3_dispatch_and_travel_min"].clip(lower=0)

        # Stage 4: Store Synchronization Gap (Friction Nexus)
        # Did courier arrive before or after food was ready?
        sync_delta_min = (fact["arrived_at_store_at"] - fact["kds_ready_at"]).dt.total_seconds() / 60.0
        
        # Courier Wait: Rider is waiting at store because food is not ready
        fact["rider_store_wait_min"] = (-sync_delta_min).clip(lower=0)
        
        # Cold Food Counter Dwell: Food is sitting on counter because courier hasn't arrived
        fact["food_counter_dwell_min"] = sync_delta_min.clip(lower=0)
        
        # Total store handoff duration
        fact["stage4_store_handoff_min"] = (fact["picked_up_at"] - fact["arrived_at_store_at"]).dt.total_seconds() / 60.0
        fact["stage4_store_handoff_min"] = fact["stage4_store_handoff_min"].clip(lower=0)

        # Stage 5: Last-Mile Delivery Transit
        fact["stage5_last_mile_min"] = (fact["delivered_at"] - fact["picked_up_at"]).dt.total_seconds() / 60.0
        fact["stage5_last_mile_min"] = fact["stage5_last_mile_min"].clip(lower=0)

        # -------------------------------------------------------------
        # TOTAL LIFECYCLE & SLA METRICS
        # -------------------------------------------------------------
        fact["total_otd_min"] = (fact["delivered_at"] - fact["order_placed_at"]).dt.total_seconds() / 60.0
        fact["is_completed"] = fact["order_status"] == "COMPLETED"
        fact["is_sla_breached"] = (fact["total_otd_min"] > 35.0) & fact["is_completed"]
        
        # Bottleneck attribution: which stage consumed the highest fraction of delay?
        def attribute_bottleneck(row):
            if not row["is_completed"] or pd.isna(row["total_otd_min"]):
                return "CANCELLED_OR_INCOMPLETE"
            
            stages = {
                "MERCHANT_LAG": row["stage1_merchant_lag_min"],
                "KITCHEN_PREP_OVERRUN": row["stage2_prep_overrun_min"],
                "RIDER_WAIT_AT_STORE": row["rider_store_wait_min"],
                "LAST_MILE_CONGESTION": max(0, row["stage5_last_mile_min"] - 10.0) # > 10 min normal transit
            }
            return max(stages, key=stages.get)

        fact["primary_delay_bottleneck"] = fact.apply(attribute_bottleneck, axis=1)

        # Save to Silver layer
        fact_path = os.path.join(self.silver_dir, "fact_order_lifecycle.parquet")
        fact.to_parquet(fact_path, index=False)

        completed_count = int(fact["is_completed"].sum())
        sla_breach_pct = round(float(fact[fact["is_completed"]]["is_sla_breached"].mean()) * 100, 2)
        p50_otd = round(float(fact[fact["is_completed"]]["total_otd_min"].median()), 2)
        p90_otd = round(float(fact[fact["is_completed"]]["total_otd_min"].quantile(0.90)), 2)

        print(f"[+] State Machine Modeling complete:")
        print(f"    - Completed orders modeled: {completed_count}")
        print(f"    - Overall P50 OTD: {p50_otd} min | P90 OTD: {p90_otd} min")
        print(f"    - Overall SLA Breach Rate (> 35 min): {sla_breach_pct}%")
        print(f"    - Primary Bottleneck Breakdown:")
        print(fact["primary_delay_bottleneck"].value_counts().to_string())

        return fact

if __name__ == "__main__":
    sm = WorkflowStateMachine()
    sm.build_fact_order_lifecycle()
