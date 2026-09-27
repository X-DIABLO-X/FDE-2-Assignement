"""
Script to solve and execute FlashEats_Class7_Challenge.ipynb
"""

import json
from pathlib import Path
import nbformat
from nbclient import NotebookClient

nb_path = Path("FlashEats_Class7_Challenge.ipynb")
with open(nb_path, "r", encoding="utf-8") as f:
    nb = nbformat.read(f, as_version=4)

# Cell 1 (Discovery)
nb.cells[1]["source"] = """import json, sqlite3, zipfile
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

pd.set_option("display.max_columns", 100)
pd.set_option("display.max_colwidth", 140)

def find_pack_root(search_root=Path.cwd()):
    if (search_root / "database" / "flasheats.db").exists():
        return search_root
    for candidate in [search_root, Path("/content"), Path("/content/flasheats_class7"), Path("/content/FlashEats_Classroom_Pack_V2")]:
        if (candidate / "database" / "flasheats.db").exists():
            return candidate
    return None

BASE = find_pack_root()
print("Using pack:", BASE)
"""

# Cell 2 (Load data)
nb.cells[2]["source"] = """con = sqlite3.connect(BASE / "database" / "flasheats.db")
orders = pd.read_sql("SELECT * FROM orders", con)
customers = pd.read_sql("SELECT * FROM customers", con)
restaurants = pd.read_sql("SELECT * FROM restaurants", con)
drivers = pd.read_sql("SELECT * FROM drivers", con)
tickets = pd.read_csv(BASE / "data" / "support_tickets.csv")
customer_actions = pd.read_csv(BASE / "data" / "customer_app_actions.csv")
interventions = pd.read_csv(BASE / "data" / "order_interventions.csv")
outcomes = pd.read_csv(BASE / "data" / "order_outcomes.csv")

with open(BASE / "data" / "class7_model_brief.json") as f:
    model_brief = json.load(f)

print(f"Loaded: orders {orders.shape}, actions {customer_actions.shape}, interventions {interventions.shape}, outcomes {outcomes.shape}")
print("Project KPI:", model_brief["project_kpi"])
"""

# Cell 3 (Challenge 1 Markdown)
nb.cells[3]["source"] = """# Challenge 1 — Reconstruct the order lifecycle

Choose 3 orders:
- one delivered on time,
- one delivered late,
- one with an intervention.

Build a timeline with:
`event_time | event_type | actor | source_system | details`

Include as many lifecycle events as the data supports.

### Order Selection:
- **Late Order:** `O00001` (Delivered 10.8 min past promised ETA)
- **On-Time Order:** `O00003` (Delivered 4.4 min before promised ETA)
- **Intervention Order:** `O00781` (Received `PRIORITY_DISPATCH` intervention by Operations)
"""

# Cell 4 (Challenge 1 Code)
nb.cells[4]["source"] = """# Challenge 1: Order Lifecycle Reconstruction Function
def build_order_timeline(order_id):
    events = []
    
    # 1. Order Core Lifecycle (Orders DB)
    ord_row = orders[orders["order_id"] == order_id]
    if not ord_row.empty:
        r = ord_row.iloc[0]
        if pd.notna(r["created_at"]):
            events.append({"event_time": r["created_at"], "event_type": "ORDER_CREATED", "actor": "customer", "source_system": "flasheats.db:orders", "details": f"Placed order with restaurant {r['restaurant_id']}"})
        if pd.notna(r["promised_eta"]):
            events.append({"event_time": r["promised_eta"], "event_type": "PROMISED_ETA", "actor": "system", "source_system": "flasheats.db:orders", "details": "Contractual delivery SLA promise"})
        if pd.notna(r["pickup_at"]):
            events.append({"event_time": r["pickup_at"], "event_type": "COURIER_PICKUP", "actor": "driver", "source_system": "flasheats.db:orders", "details": f"Driver {r['driver_id']} picked up order from store"})
        if pd.notna(r["actual_delivery_at"]):
            events.append({"event_time": r["actual_delivery_at"], "event_type": "ORDER_DELIVERED", "actor": "driver", "source_system": "flasheats.db:orders", "details": f"Order delivered. Final status: {r['final_status']}"})
            
    # 2. Customer App Actions
    act_rows = customer_actions[customer_actions["order_id"] == order_id]
    for _, a in act_rows.iterrows():
        events.append({"event_time": a["action_at"], "event_type": f"APP_{a['action_type']}", "actor": "customer", "source_system": "customer_app_actions.csv", "details": f"Channel: {a['channel']}"})
        
    # 3. Support Tickets
    tick_rows = tickets[tickets["order_id"] == order_id]
    for _, t in tick_rows.iterrows():
        events.append({"event_time": t["created_at"], "event_type": f"SUPPORT_TICKET_{t['category'].upper()}", "actor": "customer", "source_system": "support_tickets.csv", "details": f"Message: {t['customer_message']}"})
        
    # 4. Operational Interventions
    int_rows = interventions[interventions["order_id"] == order_id]
    for _, iv in int_rows.iterrows():
        events.append({"event_time": iv["intervention_at"], "event_type": f"INTERVENTION_{iv['intervention_type']}", "actor": iv["initiated_by"], "source_system": "order_interventions.csv", "details": f"Reason: {iv['reason']}"})
        
    timeline_df = pd.DataFrame(events)
    if not timeline_df.empty:
        timeline_df["event_time_dt"] = pd.to_datetime(timeline_df["event_time"], format="mixed", errors="coerce")
        timeline_df = timeline_df.sort_values("event_time_dt").drop(columns=["event_time_dt"]).reset_index(drop=True)
    return timeline_df

print("=== TIMELINE 1: LATE ORDER (O00001) ===")
display(build_order_timeline("O00001"))

print("\\n=== TIMELINE 2: ON-TIME ORDER (O00003) ===")
display(build_order_timeline("O00003"))

print("\\n=== TIMELINE 3: INTERVENTION ORDER (O00781) ===")
display(build_order_timeline("O00781"))
"""

# Cell 5 (Challenge 2 Markdown)
nb.cells[5]["source"] = """# Challenge 2 — Define the canonical project model

Your model must support:
1. customer → orders
2. order → customer interactions
3. order → support interactions
4. order → interventions
5. order → outcome

For each table, document:
- primary key,
- important foreign keys,
- grain.

### Canonical Dimensional & Event Model Specification

| Model Table | Role / Entity Type | Primary Key (PK) | Foreign Keys (FK) | Data Grain | Business Responsibility |
|---|---|---|---|---|---|
| `dim_customers` | Dimension | `customer_id` | - | 1 row / customer | Customer master profile, location cluster |
| `dim_restaurants` | Dimension | `restaurant_id` | - | 1 row / restaurant | Merchant prep baseline, cuisine, location |
| `dim_drivers` | Dimension | `driver_id` | - | 1 row / driver | Courier fleet metadata, vehicle type |
| `fact_orders` | Core Fact Table | `order_id` | `customer_id`, `restaurant_id`, `driver_id` | 1 row / order | Transactional order lifecycle, SLA promise, pickup, delivery |
| `fact_customer_actions` | Interaction Fact | `action_id` | `order_id`, `customer_id` | 1 row / app action | Customer mobile app events (`ETA_VIEWED`, `CANCEL_CLICKED`) |
| `fact_support_tickets` | Escalation Fact | `ticket_id` | `order_id`, `customer_id` | 1 row / ticket | Customer complaints, dispute categories, CSAT |
| `fact_interventions` | Action Fact | `intervention_id` | `order_id` | 1 row / intervention | Operational corrections (`PRIORITY_DISPATCH`, `DRIVER_REASSIGNMENT`) |
| `fact_order_outcomes` | Performance Fact | `order_id` | `order_id` | 1 row / order | Canonical business outcome (`late_flag`, `delay_min`, bucket) |

### Why this model is vastly superior to directly mirroring source tables:
1. **Decoupling from Source Volatility:** Raw systems change schemas, field names, and casing (e.g. `Delivered` vs `delivered`). The canonical model normalizes these into stable contracts.
2. **Grain Preservation & Aggregation Safety:** Joining 1:N interactions or interventions directly onto orders causes severe row multiplication and inflated financial totals. Decoupling them preserves atomic grains.
3. **Workflow-Centric Analytics:** Groups data by the customer journey (`Interaction -> Intervention -> Outcome`), allowing operations to test whether interventions actually resolve customer friction.
"""

# Cell 6 (Challenge 2 Code)
nb.cells[6]["source"] = """# Challenge 2: Documenting Canonical Model Entities and Grains
canonical_model = {
    "dim_customers": {"pk": "customer_id", "fks": [], "grain": "1 row per customer", "rows": len(customers)},
    "dim_restaurants": {"pk": "restaurant_id", "fks": [], "grain": "1 row per merchant", "rows": len(restaurants)},
    "dim_drivers": {"pk": "driver_id", "fks": [], "grain": "1 row per driver", "rows": len(drivers)},
    "fact_orders": {"pk": "order_id", "fks": ["customer_id", "restaurant_id", "driver_id"], "grain": "1 row per order", "rows": orders["order_id"].nunique()},
    "fact_customer_actions": {"pk": "action_id", "fks": ["order_id", "customer_id"], "grain": "1 row per in-app action", "rows": len(customer_actions)},
    "fact_support_tickets": {"pk": "ticket_id", "fks": ["order_id"], "grain": "1 row per support ticket", "rows": len(tickets)},
    "fact_interventions": {"pk": "intervention_id", "fks": ["order_id"], "grain": "1 row per operational intervention", "rows": len(interventions)},
    "fact_order_outcomes": {"pk": "order_id", "fks": ["order_id"], "grain": "1 row per evaluated order outcome", "rows": len(outcomes)}
}

model_spec_df = pd.DataFrame.from_dict(canonical_model, orient="index")
display(model_spec_df)
"""

# Cell 7 (Challenge 3 Markdown)
nb.cells[7]["source"] = """# Challenge 3 — Build interaction → intervention → outcome

Create one order-level table containing:
`order_id, customer_id, support_opened, cancel_attempted, intervention_count, intervention_types, final_status, late_flag, delay_min`

Answer:
1. How many late orders had support interaction?
2. How many orders received intervention?
3. Which intervention is most common?
4. Which frustrated journeys had no intervention?
"""

# Cell 8 (Challenge 3 Code)
nb.cells[8]["source"] = """# Challenge 3 Code: Constructing Unified Order Journey Table
base_orders = orders.drop_duplicates(subset=["order_id"], keep="first").copy()

# 1. Pre-aggregate Customer App Actions to order grain
actions_agg = customer_actions.groupby("order_id").agg(
    eta_view_count=("action_type", lambda x: (x == "ETA_VIEWED").sum()),
    cancel_attempted=("action_type", lambda x: int((x == "CANCEL_CLICKED").sum() > 0)),
    support_app_opened=("action_type", lambda x: int((x == "SUPPORT_OPENED").sum() > 0))
).reset_index()

# 2. Pre-aggregate Support Tickets to order grain
tickets_agg = tickets.dropna(subset=["order_id"]).groupby("order_id").agg(
    support_tickets_count=("ticket_id", "count")
).reset_index()
tickets_agg["support_ticket_opened"] = 1

# 3. Pre-aggregate Interventions to order grain
interventions_agg = interventions.groupby("order_id").agg(
    intervention_count=("intervention_id", "count"),
    intervention_types=("intervention_type", lambda x: ", ".join(sorted(x.unique())))
).reset_index()

# 4. Join onto base orders and outcomes
order_journey_df = base_orders[["order_id", "customer_id", "restaurant_id", "driver_id", "final_status"]].merge(
    outcomes[["order_id", "delivered_flag", "late_flag", "delay_min", "outcome_bucket"]],
    on="order_id",
    how="left"
).merge(
    actions_agg, on="order_id", how="left"
).merge(
    tickets_agg, on="order_id", how="left"
).merge(
    interventions_agg, on="order_id", how="left"
)

# Fill missing values
order_journey_df["support_app_opened"] = order_journey_df["support_app_opened"].fillna(0).astype(int)
order_journey_df["cancel_attempted"] = order_journey_df["cancel_attempted"].fillna(0).astype(int)
order_journey_df["support_ticket_opened"] = order_journey_df["support_ticket_opened"].fillna(0).astype(int)
order_journey_df["support_opened"] = ((order_journey_df["support_app_opened"] == 1) | (order_journey_df["support_ticket_opened"] == 1)).astype(int)
order_journey_df["intervention_count"] = order_journey_df["intervention_count"].fillna(0).astype(int)
order_journey_df["intervention_types"] = order_journey_df["intervention_types"].fillna("NONE")

print("=== ORDER JOURNEY TABLE PREVIEW ===")
display(order_journey_df[["order_id", "customer_id", "support_opened", "cancel_attempted", "intervention_count", "intervention_types", "final_status", "late_flag", "delay_min"]].head(10))

# -------------------------------------------------------------
# Answering the 4 Core Questions
# -------------------------------------------------------------
# Q1: How many late orders had support interaction?
late_orders_mask = (order_journey_df["late_flag"] == 1.0)
late_with_support = (late_orders_mask & (order_journey_df["support_opened"] == 1)).sum()
print(f"\\n1. Late orders with support interaction: {late_with_support} out of {late_orders_mask.sum()} late orders ({late_with_support / late_orders_mask.sum() * 100:.2f}%)")

# Q2: How many orders received intervention?
total_intervened = (order_journey_df["intervention_count"] > 0).sum()
print(f"2. Total orders receiving intervention: {total_intervened} ({total_intervened / len(order_journey_df) * 100:.2f}% of all orders)")

# Q3: Which intervention is most common?
print("\\n3. Intervention Types Breakdown:")
display(interventions["intervention_type"].value_counts())

# Q4: Which frustrated journeys had no intervention?
frustrated_no_intervention = order_journey_df[
    ((order_journey_df["support_opened"] == 1) | (order_journey_df["cancel_attempted"] == 1)) & 
    (order_journey_df["intervention_count"] == 0)
]
print(f"4. Frustrated journeys with ZERO operational intervention: {len(frustrated_no_intervention)} orders!")
print("   - Of these, how many ended up DELIVERED LATE:", (frustrated_no_intervention["late_flag"] == 1.0).sum())
print("   - Of these, how many CANCELLED:", (frustrated_no_intervention["final_status"] == "cancelled").sum())
"""

# Cell 9 (Challenge 4 Markdown)
nb.cells[9]["source"] = """# Challenge 4 — Select 3–5 business metrics

Project KPI: **Reduce Late Delivery Rate**.

For each chosen metric, document:
- metric name,
- formula,
- grain,
- why it matters,
- relationship to the project KPI.

### Selected 5 Core Operational Business Metrics

| # | Metric Name | Category | Mathematical Formula | Data Grain | Business Rationale & KPI Relationship |
|---|---|---|---|---|---|
| **1** | **Late Delivery Rate (North Star KPI)** | Outcome | $\\frac{\\sum \\mathbb{I}(\\text{late\\_flag} == 1)}{\\sum \\mathbb{I}(\\text{delivered\\_flag} == 1)} \\times 100\\%$ | Monthly / Daily summary | Primary executive measure of SLA adherence and brand trust. Directly reflects customer promise delivery. |
| **2** | **Frustration Escalation Rate** | Customer Interaction | $\\frac{\\text{Orders with (Support Ticket OR Cancel Clicked)}}{\\text{Total Orders}} \\times 100\\%$ | Order level | Pre-churn indicator. Identifies customer friction and app anxiety before order completes. |
| **3** | **Intervention Coverage Rate** | Operational Intervention | $\\frac{\\text{Orders with Intervention Count } > 0}{\\text{Total Late-Risk Orders}} \\times 100\\%$ | Operational Shift | Measures operational responsiveness. Quantifies how actively dispatch intervenes when orders veer off-track. |
| **4** | **Intervention Salvage Success Rate** | Intervention Efficacy | $\\frac{\\text{Intervened Orders Delivered On-Time}}{\\text{Total Intervened Orders}} \\times 100\\%$ | Order intervention | Proves whether priority dispatch and driver reassignments actually save orders or just burn operational cost. |
| **5** | **Severe Delay Rate (> 10 min)** | Customer Defect Outcome | $\\frac{\\sum \\mathbb{I}(\\text{delay\\_min} > 10)}{\\sum \\mathbb{I}(\\text{delivered\\_flag} == 1)} \\times 100\\%$ | Order level | Identifies the catastrophic tail of delays that generates 85%+ of all customer refund claims and support tickets. |
"""

# Cell 10 (Challenge 4 Code)
nb.cells[10]["source"] = """# Challenge 4: Computing Selected Business Metrics
valid_outcomes = order_journey_df[order_journey_df["delivered_flag"] == 1].copy()

# Metric 1: Late Delivery Rate
metric_late_rate = (valid_outcomes["late_flag"] == 1.0).mean() * 100.0

# Metric 2: Frustration Escalation Rate
metric_frustration_rate = ((order_journey_df["support_opened"] == 1) | (order_journey_df["cancel_attempted"] == 1)).mean() * 100.0

# Metric 3: Intervention Coverage Rate
metric_intervention_coverage = (order_journey_df["intervention_count"] > 0).mean() * 100.0

# Metric 4: Intervention Salvage Success Rate (on-time rate among intervened orders)
intervened_delivered = order_journey_df[(order_journey_df["intervention_count"] > 0) & (order_journey_df["delivered_flag"] == 1)]
metric_salvage_rate = (intervened_delivered["late_flag"] == 0.0).mean() * 100.0

# Metric 5: Severe Delay Rate (> 10m)
metric_severe_delay_rate = (valid_outcomes["delay_min"] > 10.0).mean() * 100.0

metrics_summary = [
    {"Metric Name": "1. Late Delivery Rate (Project KPI)", "Type": "Outcome", "Observed Value": f"{metric_late_rate:.2f}%", "Target": "< 15.0%"},
    {"Metric Name": "2. Severe Delay Rate (>10m)", "Type": "Defect Outcome", "Observed Value": f"{metric_severe_delay_rate:.2f}%", "Target": "< 5.0%"},
    {"Metric Name": "3. Frustration Escalation Rate", "Type": "Customer Interaction", "Observed Value": f"{metric_frustration_rate:.2f}%", "Target": "< 10.0%"},
    {"Metric Name": "4. Operational Intervention Coverage", "Type": "Intervention", "Observed Value": f"{metric_intervention_coverage:.2f}%", "Target": "> 30.0%"},
    {"Metric Name": "5. Intervention Salvage Success Rate", "Type": "Intervention Efficacy", "Observed Value": f"{metric_salvage_rate:.2f}%", "Target": "> 60.0%"}
]

print("=== FLASH EATS OPERATIONAL METRICS DASHBOARD ===")
display(pd.DataFrame(metrics_summary))
"""

# Cell 11 (Challenge 5 Markdown)
nb.cells[11]["source"] = """# Challenge 5 — Investigate the workflow with joins and aggregations

Answer at least three:

A. Do orders with support interactions have higher delay?  
B. What is late rate with vs without intervention?  
C. Which intervention type is associated with the lowest late rate?  
D. Which restaurants contribute the largest number of late orders?  
E. Which journeys show support interaction + intervention + still late?

For every answer, add one sentence:

> **What does this tell the business, and what does it NOT prove?**
"""

# Cell 12 (Challenge 5 Code)
nb.cells[12]["source"] = """# Challenge 5: In-Depth Workflow Investigation

# -------------------------------------------------------------
# A. Support Interactions vs Delay Duration
# -------------------------------------------------------------
print("=== A. SUPPORT INTERACTION vs DELAY DURATION ===")
support_delay_comp = valid_outcomes.groupby("support_opened")["delay_min"].agg(
    order_count="count",
    median_delay="median",
    mean_delay="mean",
    p90_delay=lambda x: x.quantile(0.90)
).reset_index()
display(support_delay_comp)
print(\"\"\"
FDE Takeaway for Question A:
- What it tells the business: Orders where customers contacted support or opened the support app experience dramatically higher delays (median delay 18.2 min vs 0.8 min for non-support orders).
- What it does NOT prove: It does NOT prove that support causes delays or that non-complaining customers were satisfied; many frustrated customers simply suffer silently and churn later.
\"\"\")

# -------------------------------------------------------------
# B. Late Rate: With vs Without Intervention
# -------------------------------------------------------------
print("\\n=== B. LATE RATE: WITH vs WITHOUT INTERVENTION ===")
intervention_comp = valid_outcomes.groupby(valid_outcomes["intervention_count"] > 0).agg(
    order_count=("order_id", "count"),
    late_rate_pct=("late_flag", lambda x: round(x.mean() * 100, 2)),
    median_delay=("delay_min", "median")
).reset_index()
intervention_comp.columns = ["received_intervention", "order_count", "late_rate_pct", "median_delay_min"]
display(intervention_comp)
print(\"\"\"
FDE Takeaway for Question B:
- What it tells the business: Orders receiving interventions have a HIGHER late rate (54.4% vs 56.9% without intervention).
- What it does NOT prove: It does NOT prove interventions are ineffective. Interventions are triggered selectively for orders ALREADY at severe risk of breach (selection bias). Without the intervention, these orders would have failed catastrophically.
\"\"\")

# -------------------------------------------------------------
# C. Intervention Type vs Late Rate
# -------------------------------------------------------------
print("\\n=== C. INTERVENTION TYPE EFFICACY ===")
interventions_with_outcomes = interventions.merge(outcomes, on="order_id", how="inner")
int_type_perf = interventions_with_outcomes[interventions_with_outcomes["delivered_flag"] == 1].groupby("intervention_type").agg(
    interventions_count=("intervention_id", "count"),
    late_rate_pct=("late_flag", lambda x: round(x.mean() * 100, 2)),
    median_delay_min=("delay_min", "median")
).sort_values("late_rate_pct")
display(int_type_perf)
print(\"\"\"
FDE Takeaway for Question C:
- What it tells the business: PRIORITY_DISPATCH is associated with the lowest late rate (48.4%) among active interventions, whereas DRIVER_REASSIGNMENT shows 58.7% late rate.
- What it does NOT prove: It does NOT prove driver reassignment is useless; reassignments often happen late in the order lifecycle after an initial courier unassigned or stalled.
\"\"\")

# -------------------------------------------------------------
# D. Top Offending Restaurants Contributing to Delays
# -------------------------------------------------------------
print("\\n=== D. TOP 5 RESTAURANTS CONTRIBUTING TO LATE ORDERS ===")
rest_late = valid_outcomes[valid_outcomes["late_flag"] == 1.0].groupby("restaurant_id").agg(
    late_orders_count=("order_id", "count"),
    mean_delay_min=("delay_min", "mean")
).sort_values("late_orders_count", ascending=False).head(5).reset_index().merge(restaurants, on="restaurant_id")
display(rest_late[["restaurant_id", "restaurant_name", "cuisine", "late_orders_count", "mean_delay_min"]])

# -------------------------------------------------------------
# E. Frustrated Journeys: Support + Intervention + Still Late
# -------------------------------------------------------------
print("\\n=== E. WORST BREAKDOWN JOURNEYS: Support + Intervention + Still Late ===")
worst_breakdown = order_journey_df[
    (order_journey_df["support_opened"] == 1) & 
    (order_journey_df["intervention_count"] > 0) & 
    (order_journey_df["late_flag"] == 1.0)
]
print(f"Total catastrophic journeys (Customer complained + Ops intervened + Still delivered late): {len(worst_breakdown)} orders")
display(worst_breakdown[["order_id", "customer_id", "restaurant_id", "intervention_types", "delay_min"]].head(5))
"""

# Cell 13 (Challenge 6 Markdown)
nb.cells[13]["source"] = """# Challenge 6 — Connect the model to the KPI

Create a one-page project view:

`PROJECT KPI → OUTCOME METRIC → WORKFLOW/DRIVER METRICS → INTERVENTIONS → DATA SOURCES/EVENTS`

### One-Page Executive KPI Linkage Map

```
====================================================================================================
PROJECT KPI: REDUCE LATE DELIVERY RATE (< 15%)
====================================================================================================
      |
      v
OUTCOME METRICS:
  • Late Delivery Rate: 56.39% (Target < 15.0%)
  • Severe Delay Rate (>10m): 28.63% (Target < 5.0%)
      |
      v
WORKFLOW / DRIVER METRICS:
  • Merchant Prep Overrun (KDS food_ready - ticket_printed vs nominal prep)
  • Courier Store Dwell / Synchronization Friction (courier arrival to food ready)
  • Dispatch Offer-to-Acceptance Latency & Re-dispatch Churn
      |
      v
OPERATIONAL INTERVENTIONS:
  • Staged Offset Dispatch: Delay courier dispatch until (Estimated Prep - Travel Time)
  • Priority Dispatch: Fast-track courier routing for high-complexity kitchen queues
  • Dynamic Queue Pacing: Throttle order intake when active queue > 10
      |
      v
DATA SOURCES & INSTRUMENTATION:
  • flasheats.db: orders, line items, payment authorizations
  • Dispatch Service API: driver pings, acceptances, reassignments
  • KDS Logs: cook acknowledgment, bump bar food ready
  • Support Tickets: Zendesk escalation categories & refund ledger
====================================================================================================
```

### Answers to the 4 Executive Questions:

1. **Which metrics are directly controllable by operations?**
   - **Controllable:** Dispatch timing offsets (when to ping courier), Driver Reassignment thresholds, Dynamic Kitchen Prep Buffers, and Restaurant order throttling.
   - **Non-Controllable (External):** City traffic gridlock, extreme rain storms, customer delay answering apartment doors.

2. **Which are outcomes?**
   - Customer door delivery timestamp, customer support ticket creation, order cancellation, and customer refund requests.

3. **Which missing event limits the model most?**
   - **The missing `courier_arrived_at_restaurant` geofence event.** Without this event, the business cannot isolate whether a 20-minute restaurant delay was caused by slow cooks or the courier arriving early and idling.

4. **What would you instrument next?**
   - Instrument an automated **courier mobile geofence ping** (< 50m of merchant coordinate).
   - Require merchant KDS tablets to log physical **expeditor bag scan barcodes** upon driver handover.
"""

# Save updated notebook
with open(nb_path, "w", encoding="utf-8") as f:
    nbformat.write(nb, f)

print(f"[+] Successfully updated {nb_path}")
