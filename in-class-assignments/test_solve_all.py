"""
Test script to compute and verify all numbers across FlashEats Class 5, Class 6, and Class 7 data.
"""

import json
import sqlite3
from pathlib import Path
import pandas as pd
import numpy as np

BASE = Path(".") if (Path(".") / "database" / "flasheats.db").exists() else Path("..")

# 1. Database
con = sqlite3.connect(BASE / "database" / "flasheats.db")
orders = pd.read_sql("SELECT * FROM orders", con)
customers = pd.read_sql("SELECT * FROM customers", con)
restaurants = pd.read_sql("SELECT * FROM restaurants", con)
drivers = pd.read_sql("SELECT * FROM drivers", con)
con.close()

# 2. CSVs and JSONs
tickets = pd.read_csv(BASE / "data" / "support_tickets.csv")
restaurant_status = pd.read_csv(BASE / "data" / "restaurant_status.csv")
customer_actions = pd.read_csv(BASE / "data" / "customer_app_actions.csv")
interventions = pd.read_csv(BASE / "data" / "order_interventions.csv")
outcomes = pd.read_csv(BASE / "data" / "order_outcomes.csv")
with open(BASE / "data" / "driver_events.json") as f:
    driver_events = json.load(f)

print("--- CLASS 5 NUMBERS ---")
print("Total orders in DB:", len(orders))
print("Unique order_id:", orders["order_id"].nunique())
print("Status counts:\n", orders["final_status"].value_counts(dropna=False))

# Parse timestamps
orders["created_at_dt"] = pd.to_datetime(orders["created_at"], errors="coerce")
orders["promised_eta_dt"] = pd.to_datetime(orders["promised_eta"], errors="coerce")
orders["pickup_at_dt"] = pd.to_datetime(orders["pickup_at"], errors="coerce")
orders["actual_delivery_at_dt"] = pd.to_datetime(orders["actual_delivery_at"], errors="coerce")

# Clean final_status
orders["final_status_clean"] = orders["final_status"].str.strip().str.lower()
delivered = orders[orders["final_status_clean"] == "delivered"].copy()
print("Delivered orders:", len(delivered))
delivered["delay_min"] = (delivered["actual_delivery_at_dt"] - delivered["promised_eta_dt"]).dt.total_seconds() / 60.0
delivered["is_late"] = delivered["delay_min"] > 0
print("Late count:", delivered["is_late"].sum())
print("Late %:", round(delivered["is_late"].mean() * 100, 2))
print("Median lateness (late orders):", round(delivered[delivered["is_late"]]["delay_min"].median(), 2))
print("Mean lateness (late orders):", round(delivered[delivered["is_late"]]["delay_min"].mean(), 2))

print("\n--- CLASS 6 NUMBERS ---")
print("Duplicate orders:", orders["order_id"].duplicated().sum())
print("Delivered missing actual_delivery_at:", delivered["actual_delivery_at_dt"].isna().sum())
print("Chronology check (promised_eta < created_at):", (orders["promised_eta_dt"] < orders["created_at_dt"]).sum())
print("Chronology check (pickup_at > actual_delivery_at):", (delivered["pickup_at_dt"] > delivered["actual_delivery_at_dt"]).sum())

print("\nLate rate under different definitions:")
# Def 1: delay > 0
print("Def 1 (delay > 0):", round((delivered["delay_min"] > 0).mean() * 100, 2))
# Def 2: delay > 10 min
print("Def 2 (delay > 10m):", round((delivered["delay_min"] > 10).mean() * 100, 2))
# Def 3: delay > 0 over all unique orders (including cancelled)
print("Def 3 (delay > 0 / all orders):", round((delivered["delay_min"] > 0).sum() / orders["order_id"].nunique() * 100, 2))

print("\nCross-source integrity:")
print("orders.restaurant_id in restaurants:", orders["restaurant_id"].dropna().isin(restaurants["restaurant_id"]).mean() * 100)
print("orders.driver_id in drivers:", orders["driver_id"].dropna().isin(drivers["driver_id"]).mean() * 100)
print("tickets.order_id in orders:", tickets["order_id"].dropna().isin(orders["order_id"]).mean() * 100)
print("tickets missing order_id:", tickets["order_id"].isna().sum())
print("restaurant_status.order_id in orders:", restaurant_status["order_id"].dropna().isin(orders["order_id"]).mean() * 100)

print("\n--- CLASS 7 NUMBERS ---")
print("outcomes shape:", outcomes.shape)
print("interventions shape:", interventions.shape)
print("customer_actions shape:", customer_actions.shape)
print("Intervention types:\n", interventions["intervention_type"].value_counts())
print("Outcome buckets:\n", outcomes["outcome_bucket"].value_counts())
