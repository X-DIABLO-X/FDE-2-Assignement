"""
Synthetic Multi-Source Data Generator for FlashEats (Quick Commerce Delivery)
Simulates 4 disparate client operational systems with realistic noise and 5 domain anomalies.

Systems Simulated:
1. Operational Orders RDBMS (SQLite): orders, merchants, line items
2. Fleet Dispatch & Telemetry Service (JSON API dump)
3. Merchant Kitchen Display System (KDS) (Daily CSV export)
4. Customer Support / Zendesk Escalations (JSON dump)
"""

import os
import json
import sqlite3
import random
import csv
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

def generate_flasheats_dataset(
    output_dir: str = "data/raw",
    num_orders: int = 6000,
    seed: int = 42,
    date_str: str = "2026-09-25"
):
    random.seed(seed)
    np.random.seed(seed)
    os.makedirs(output_dir, exist_ok=True)

    base_date = datetime.strptime(date_str, "%Y-%m-%d")
    
    # -------------------------------------------------------------
    # 1. GENERATE MERCHANTS
    # -------------------------------------------------------------
    clusters = ["DOWNTOWN_CORE", "TECH_CORRIDOR", "WESTSIDE_SUBURBS"]
    cuisines = ["Artisan Burgers", "Neapolitan Pizza", "Hyderabadi Biryani", "Healthy Bowls", "Asian Wok", "Specialty Coffee"]
    
    merchants = []
    for m_idx in range(1, 16):
        m_id = f"MCH-{100 + m_idx}"
        cluster = clusters[(m_idx - 1) % len(clusters)]
        cuisine = cuisines[(m_idx - 1) % len(cuisines)]
        
        # Base coordinates per cluster
        if cluster == "DOWNTOWN_CORE":
            lat = 12.9716 + random.uniform(-0.015, 0.015)
            lon = 77.5946 + random.uniform(-0.015, 0.015)
            capacity = random.randint(8, 14)
        elif cluster == "TECH_CORRIDOR":
            lat = 12.9352 + random.uniform(-0.02, 0.02)
            lon = 77.6245 + random.uniform(-0.02, 0.02)
            capacity = random.randint(10, 18)
        else:
            lat = 12.9900 + random.uniform(-0.025, 0.025)
            lon = 77.5500 + random.uniform(-0.025, 0.025)
            capacity = random.randint(6, 12)
            
        # Specific merchants with hardware clock drift on POS tablets
        clock_drift_sec = 0
        if m_idx in [3, 7, 11]:
            clock_drift_sec = random.choice([-150, -90, 120, 240]) # Anomaly 1: POS Clock Drift
            
        merchants.append({
            "merchant_id": m_id,
            "merchant_name": f"{cuisine} Kitchen {100 + m_idx}",
            "cluster_id": cluster,
            "cuisine_type": cuisine,
            "merchant_lat": round(lat, 5),
            "merchant_lon": round(lon, 5),
            "kitchen_capacity": capacity,
            "nominal_prep_min": random.choice([12, 15, 18]),
            "clock_drift_sec": clock_drift_sec,
            "created_at": "2025-01-15T00:00:00Z"
        })

    # -------------------------------------------------------------
    # 2. GENERATE ORDERS & ORDER WORKFLOW LIFECYCLE
    # -------------------------------------------------------------
    orders = []
    line_items = []
    dispatch_attempts = []
    kds_logs = []
    support_tickets = []

    # Hourly distribution: Peak lunch (12-14), Peak dinner (19-22)
    hour_weights = [
        0.01, 0.005, 0.005, 0.005, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.09,
        0.13, 0.11, 0.06, 0.04, 0.04, 0.05, 0.07, 0.12, 0.14, 0.10, 0.05, 0.02
    ]
    total_w = sum(hour_weights)
    hour_probs = [w / total_w for w in hour_weights]

    drivers = [f"DRV-{2000 + i}" for i in range(1, 351)]

    for o_idx in range(1, num_orders + 1):
        order_id = f"ORD-20260925-{10000 + o_idx}"
        customer_id = f"CUST-{random.randint(10000, 99999)}"
        merchant = random.choice(merchants)
        m_id = merchant["merchant_id"]
        
        # Timestamp based on hourly distribution
        hour = np.random.choice(24, p=hour_probs)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        t_placed = base_date.replace(hour=hour, minute=minute, second=second)
        
        # Peak congestion multiplier
        is_peak = (12 <= hour <= 14) or (19 <= hour <= 21)
        peak_multiplier = 1.45 if is_peak else 1.0

        # Operational status & cancellation probability
        is_cancelled = random.random() < 0.045 # Anomaly 4: Cancelled orders (4.5%)
        order_status = "CANCELLED" if is_cancelled else "COMPLETED"
        payment_status = "REFUNDED" if is_cancelled else "PAID"
        
        # Financials
        subtotal_cents = random.randint(1200, 6500)
        delivery_fee_cents = random.choice([299, 399, 499, 599])
        tip_cents = random.choice([0, 0, 100, 200, 300, 500])
        
        # Geo
        cust_lat = round(merchant["merchant_lat"] + random.uniform(-0.035, 0.035), 5)
        cust_lon = round(merchant["merchant_lon"] + random.uniform(-0.035, 0.035), 5)
        
        # SLA promised: placed + 30 min (or 35 min for distant zones)
        sla_promised_sec = 1800 if merchant["cluster_id"] != "WESTSIDE_SUBURBS" else 2100
        t_sla = t_placed + timedelta(seconds=sla_promised_sec)
        
        cancelled_reason = None
        t_cancellation = None

        # Inject extreme unrecoverable anomaly on 12 orders for quarantine DLQ testing
        is_extreme_quarantine_record = (o_idx in [42, 108, 256, 512, 789, 1024, 1500, 2048, 3000, 3500, 4200, 5000])

        # ---------------------------------------------------------
        # Order Line Items (Exact Penny Reconciliation)
        # ---------------------------------------------------------
        num_items = random.randint(1, 3)
        rem_subtotal = subtotal_cents
        for itm_i in range(num_items):
            qty = 1 if itm_i < num_items - 1 else 1 # standard unit
            if itm_i == num_items - 1:
                item_price = rem_subtotal
            else:
                item_price = random.randint(int(rem_subtotal * 0.25), int(rem_subtotal * 0.6))
                rem_subtotal -= item_price
            
            line_items.append({
                "line_item_id": f"LIT-{order_id}-{itm_i+1}",
                "order_id": order_id,
                "item_name": f"{merchant['cuisine_type']} Specialty {itm_i+1}",
                "category": random.choice(["HOT_MAINS", "HOT_MAINS", "COLD_BEVERAGES", "SIDES"]),
                "prep_complexity": random.choice(["LOW", "MEDIUM", "HIGH"]),
                "prep_time_weight_min": round(random.uniform(4.0, 12.0), 1),
                "quantity": qty,
                "unit_price_cents": item_price
            })

        # ---------------------------------------------------------
        # Stage 1: Merchant Confirmation (t_placed -> t_confirmed)
        # ---------------------------------------------------------
        merchant_lag_sec = int(random.expovariate(1 / 45.0) + 15) # mean ~60s
        if is_peak and random.random() < 0.15:
            merchant_lag_sec += random.randint(120, 300) # distracted merchant
        t_confirmed = t_placed + timedelta(seconds=merchant_lag_sec)

        # ---------------------------------------------------------
        # Stage 2: Kitchen Display System (KDS Prep)
        # ---------------------------------------------------------
        nominal_prep_sec = merchant["nominal_prep_min"] * 60
        # Simulated active queue depth in kitchen
        active_queue = random.randint(2, 6) if not is_peak else random.randint(6, 16)
        queue_penalty_sec = active_queue * random.randint(40, 90)
        actual_prep_sec = int(nominal_prep_sec * peak_multiplier + queue_penalty_sec + random.normalvariate(0, 90))
        actual_prep_sec = max(actual_prep_sec, 300) # minimum 5 min prep
        
        t_prep_start = t_confirmed + timedelta(seconds=random.randint(15, 60))
        t_food_ready = t_confirmed + timedelta(seconds=actual_prep_sec)
        
        # Inject Anomaly 1: Clock drift for specific POS terminals
        drift_offset = merchant["clock_drift_sec"]
        t_printed_pos = t_placed + timedelta(seconds=merchant_lag_sec + drift_offset)
        t_ready_pos = t_food_ready + timedelta(seconds=drift_offset)
        
        # Inject Anomaly 2: Cook missed bump bar (~9% of peak orders)
        missed_bump_bar = is_peak and (random.random() < 0.09)
        food_ready_kds_val = None if missed_bump_bar else t_ready_pos.strftime("%Y-%m-%d %H:%M:%S")

        kds_logs.append({
            "kds_ticket_id": f"KDS-{order_id}",
            "order_id": order_id,
            "merchant_id": m_id,
            "kds_device_id": f"DEV-{m_id[-3:]}-POS",
            "ticket_printed_at": t_printed_pos.strftime("%Y-%m-%d %H:%M:%S"),
            "cook_acknowledged_at": (t_confirmed + timedelta(seconds=drift_offset + 20)).strftime("%Y-%m-%d %H:%M:%S"),
            "prep_started_at": (t_prep_start + timedelta(seconds=drift_offset)).strftime("%Y-%m-%d %H:%M:%S"),
            "food_ready_at": food_ready_kds_val,
            "active_kitchen_queue_depth": active_queue,
            "estimated_prep_sec": nominal_prep_sec
        })

        # ---------------------------------------------------------
        # Stage 3: Fleet Dispatch Service (Mock REST API)
        # ---------------------------------------------------------
        # Immediate dispatch upon confirmation (baseline architecture flaw)
        t_dispatch_offer = t_confirmed + timedelta(seconds=random.randint(5, 25))
        
        # Inject Anomaly 3: Driver re-dispatch churn (1:N attempts)
        churn_probability = 0.22 if is_peak else 0.08
        num_attempts = 1
        if churn_probability > random.random():
            num_attempts = random.choice([2, 2, 3])
            
        cur_offer_ts = t_dispatch_offer
        terminal_driver = None
        t_assigned = None
        t_arrived_store = None
        t_picked_up = None
        t_delivered = None

        for att in range(1, num_attempts + 1):
            disp_id = f"DSP-{order_id}-{att}"
            att_driver = random.choice(drivers)
            
            if att < num_attempts:
                # Driver rejected or timed out
                reason = random.choice(["TIMEOUT_NO_RESPONSE", "DISTANCE_TOO_FAR", "LOW_BATTERY"])
                resp_delay = 45 if reason == "TIMEOUT_NO_RESPONSE" else random.randint(8, 25)
                dispatch_attempts.append({
                    "dispatch_id": disp_id,
                    "order_id": order_id,
                    "driver_id": att_driver,
                    "attempt_number": att,
                    "dispatch_status": "REJECTED",
                    "offered_at": cur_offer_ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "responded_at": (cur_offer_ts + timedelta(seconds=resp_delay)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "arrived_at_store_at": None,
                    "picked_up_at": None,
                    "delivered_at": None,
                    "rejection_reason": reason,
                    "driver_vehicle": random.choice(["MOTORCYCLE", "ELECTRIC_SCOOTER"]),
                    "driver_battery_pct": random.randint(18, 95)
                })
                cur_offer_ts = cur_offer_ts + timedelta(seconds=resp_delay + random.randint(5, 15))
            else:
                # Terminal driver accepted
                resp_delay = random.randint(4, 20)
                t_assigned = cur_offer_ts + timedelta(seconds=resp_delay)
                terminal_driver = att_driver
                
                if is_cancelled and random.random() < 0.6:
                    # Cancelled before pickup
                    cancelled_reason = random.choice(["CUSTOMER_WAIT_TOO_LONG", "MERCHANT_ITEM_STOCKOUT"])
                    t_cancellation = t_assigned + timedelta(seconds=random.randint(60, 300))
                    dispatch_attempts.append({
                        "dispatch_id": disp_id,
                        "order_id": order_id,
                        "driver_id": att_driver,
                        "attempt_number": att,
                        "dispatch_status": "CANCELLED_BY_SYSTEM",
                        "offered_at": cur_offer_ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "responded_at": t_assigned.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "arrived_at_store_at": None,
                        "picked_up_at": None,
                        "delivered_at": None,
                        "rejection_reason": "ORDER_ABORTED",
                        "driver_vehicle": random.choice(["MOTORCYCLE", "ELECTRIC_SCOOTER"]),
                        "driver_battery_pct": random.randint(25, 95)
                    })
                    break

                # Driver transit to store
                driver_transit_sec = int(random.normalvariate(480, 120)) # ~8 mins
                driver_transit_sec = max(driver_transit_sec, 180)
                t_arrived_store = t_assigned + timedelta(seconds=driver_transit_sec)

                # -----------------------------------------------------
                # Stage 4: Store Handoff / Synchronization Gap
                # -----------------------------------------------------
                # Rider arrives BEFORE food ready -> Rider waits!
                # Rider arrives AFTER food ready -> Food cools on counter!
                t_actual_ready_ground_truth = t_food_ready
                handoff_slack = random.randint(30, 90) # physical bag scan & handoff
                
                pickup_base_ts = max(t_arrived_store, t_actual_ready_ground_truth) + timedelta(seconds=handoff_slack)
                t_picked_up = pickup_base_ts

                # Inject Anomaly 5: Mobile network batching jitter (-5s to -25s out-of-order)
                if random.random() < 0.035:
                    # Mall basement/elevator packet batching inversion
                    jitter = random.randint(5, 25)
                    t_arrived_store_reported = t_picked_up + timedelta(seconds=jitter)
                else:
                    t_arrived_store_reported = t_arrived_store

                # -----------------------------------------------------
                # Stage 5: Last-Mile Delivery Transit
                # -----------------------------------------------------
                transit_sec = int(random.normalvariate(600, 180)) # ~10 mins
                transit_sec = max(transit_sec, 300)
                if is_peak:
                    transit_sec += random.randint(120, 360) # traffic surge
                    
                t_delivered = t_picked_up + timedelta(seconds=transit_sec)
                
                # Extreme unrecoverable corruption for designated quarantine test records
                if is_extreme_quarantine_record:
                    # Rider recorded as arriving at store 45 minutes AFTER pickup (severe sensor failure)
                    t_arrived_store_reported = t_picked_up + timedelta(minutes=45)

                dispatch_attempts.append({
                    "dispatch_id": disp_id,
                    "order_id": order_id,
                    "driver_id": att_driver,
                    "attempt_number": att,
                    "dispatch_status": "COMPLETED",
                    "offered_at": cur_offer_ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "responded_at": t_assigned.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "arrived_at_store_at": t_arrived_store_reported.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "picked_up_at": t_picked_up.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "delivered_at": t_delivered.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "rejection_reason": None,
                    "driver_vehicle": random.choice(["MOTORCYCLE", "ELECTRIC_SCOOTER"]),
                    "driver_battery_pct": random.randint(20, 95)
                })

        # Final order record for SQL DB
        orders.append({
            "order_id": order_id,
            "customer_id": customer_id,
            "merchant_id": m_id,
            "order_status": order_status,
            "order_timestamp": t_placed.strftime("%Y-%m-%d %H:%M:%S"),
            "payment_status": payment_status,
            "subtotal_cents": subtotal_cents,
            "delivery_fee_cents": delivery_fee_cents,
            "tip_cents": tip_cents,
            "customer_lat": cust_lat,
            "customer_lon": cust_lon,
            "promised_sla_timestamp": t_sla.strftime("%Y-%m-%d %H:%M:%S"),
            "cancelled_reason": cancelled_reason,
            "cancellation_timestamp": t_cancellation.strftime("%Y-%m-%d %H:%M:%S") if t_cancellation else None
        })

        # ---------------------------------------------------------
        # Source 4: Customer Support / Zendesk Escalation
        # ---------------------------------------------------------
        # If order breached SLA (> 35 min) or food had high counter dwell (> 6 min)
        if order_status == "COMPLETED" and t_delivered:
            total_cycle_sec = (t_delivered - t_placed).total_seconds()
            counter_dwell_sec = max(0, (t_picked_up - t_food_ready).total_seconds())
            
            ticket_prob = 0.03 # baseline random complaint
            if total_cycle_sec > 2100: # SLA breach > 35 min
                ticket_prob += 0.42
            if counter_dwell_sec > 420: # Cold food risk
                ticket_prob += 0.28
                
            if random.random() < ticket_prob:
                is_severe = total_cycle_sec > 2700
                support_tickets.append({
                    "ticket_id": f"ZD-{100000 + len(support_tickets) + 1}",
                    "order_id": order_id,
                    "customer_id": customer_id,
                    "created_at": (t_delivered + timedelta(minutes=random.randint(5, 45))).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "issue_category": "LATE_DELIVERY" if total_cycle_sec > 2100 else ("COLD_FOOD" if counter_dwell_sec > 420 else "WRONG_ITEM"),
                    "secondary_issue": "COLD_FOOD" if (total_cycle_sec > 2100 and counter_dwell_sec > 300) else None,
                    "customer_sentiment": "VERY_NEGATIVE" if is_severe else "NEGATIVE",
                    "channel": random.choice(["IN_APP_CHAT", "IN_APP_CHAT", "PHONE_SUPPORT"]),
                    "resolution_status": "RESOLVED_REFUNDED" if is_severe else "RESOLVED_VOUCHER",
                    "compensation_amount_cents": subtotal_cents if is_severe else 500,
                    "csat_score": 1 if is_severe else 2
                })

    # -------------------------------------------------------------
    # WRITE DATA TO TARGET FILES / DATABASES
    # -------------------------------------------------------------
    # 1. SQLite Database
    db_path = os.path.join(output_dir, "orders_platform.db")
    if os.path.exists(db_path):
        os.remove(db_path)
    conn = sqlite3.connect(db_path)
    
    pd.DataFrame(merchants).to_sql("merchants", conn, index=False)
    pd.DataFrame(orders).to_sql("orders", conn, index=False)
    pd.DataFrame(line_items).to_sql("order_line_items", conn, index=False)
    conn.close()
    
    # 2. Dispatch REST API JSON dump
    disp_path = os.path.join(output_dir, "dispatch_telemetry_stream.json")
    with open(disp_path, "w", encoding="utf-8") as f:
        json.dump(dispatch_attempts, f, indent=2)
        
    # 3. KDS Prep CSV
    kds_path = os.path.join(output_dir, "kds_merchant_prep.csv")
    pd.DataFrame(kds_logs).to_csv(kds_path, index=False)
    
    # 4. Support Tickets JSON
    support_path = os.path.join(output_dir, "customer_support_tickets.json")
    with open(support_path, "w", encoding="utf-8") as f:
        json.dump(support_tickets, f, indent=2)

    print(f"Dataset generated successfully in '{output_dir}':")
    print(f"  - Orders: {len(orders)} (Platform DB: {db_path})")
    print(f"  - Line Items: {len(line_items)}")
    print(f"  - Merchants: {len(merchants)}")
    print(f"  - Dispatch Attempts: {len(dispatch_attempts)} (API Dump: {disp_path})")
    print(f"  - KDS Logs: {len(kds_logs)} (CSV: {kds_path})")
    print(f"  - Support Tickets: {len(support_tickets)} (JSON: {support_path})")

if __name__ == "__main__":
    generate_flasheats_dataset()
