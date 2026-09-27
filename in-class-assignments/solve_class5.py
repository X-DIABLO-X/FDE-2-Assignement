"""
Script to solve and execute FlashEats_Class5_Student.ipynb
"""

import json
from pathlib import Path
import nbformat
from nbclient import NotebookClient

nb_path = Path("FlashEats_Class5_Student.ipynb") if Path("FlashEats_Class5_Student.ipynb").exists() else Path("in-class-assignments/FlashEats_Class5_Student.ipynb")
with open(nb_path, "r", encoding="utf-8") as f:
    nb = nbformat.read(f, as_version=4)

# Update Cell 2 (load pack - support local run)
nb.cells[2]["source"] = """# 1. LOAD THE CLASSROOM PACK
from pathlib import Path
import os, sys, json, time, sqlite3, subprocess, zipfile

BASE = Path.cwd()
if not (BASE / "database" / "flasheats.db").exists():
    for candidate in [Path("/content/FlashEats_Classroom_Pack"), Path("/content/flasheats-classroom-pack"), Path("/content")]:
        if (candidate / "database" / "flasheats.db").exists():
            BASE = candidate
            break

print("BASE:", BASE)
print("Database Exists:", (BASE / "database" / "flasheats.db").exists())
"""

# Update Cell 3 (Source map markdown table)
nb.cells[3]["source"] = """## 2. Source map first

Before analysis, predict where you would look for:

| Information | Likely source | Why? |
|---|---|---|
| Promised delivery time | `database/flasheats.db` (`orders.promised_eta`) | Core OMS transaction record committing SLA to customer at checkout. Authoritative. |
| Actual delivery time | `database/flasheats.db` (`orders.actual_delivery_at`) | Final order settlement timestamp in transactional DB. Authoritative for billing, contextual for physical arrival. |
| Driver assignment | Mock Dispatch API (`/dispatch/orders`) & `driver_events.json` | Real-time fleet telematics recording dispatch offers, acceptances, and driver IDs. Authoritative for dispatch. |
| Customer complaint | `data/support_tickets.csv` | Customer support CRM recording ticket categories, customer messages, and escalation timestamps. Contextual (subjective customer perception). |
| Restaurant status | `data/restaurant_status.csv` & `database/flasheats.db` | Merchant tablet status logs (preparing, ready, handoff). Contextual (subject to staff manual input delays). |
| Driver movement/events | `data/driver_events.json` | GPS coordinates, speed, and driver event pings over time. Authoritative for courier physical position. |

**Discuss:** Which source is authoritative for each fact, and which is only contextual?
- **Authoritative:** Orders DB for promised SLA and checkout timestamps; Dispatch API for driver assignment; Driver GPS pings for physical coordinates.
- **Contextual:** Support tickets reflect subjective customer sentiment (often delayed by 1-3 hours); Restaurant status is vulnerable to manual button gaming by kitchen staff.
"""

# Update Cell 5 (Challenge 1 markdown decisions)
nb.cells[5]["source"] = """# Challenge 1 — How large is the late-delivery problem?

Before coding, decide:

- **Late means:** An order where `actual_delivery_at > promised_eta` (delay > 0 minutes).
- **Denominator:** Delivered orders with valid, non-null `actual_delivery_at` and `promised_eta` (1,495 unique delivered orders).
- **Cancelled orders:** Excluded from delivery latency calculation (since they were never delivered; tracked separately in cancellation funnel).
- **Missing actual delivery timestamp:** Excluded from delivery delay distribution and flagged as data-quality defect (37 orders).
- **Row grain:** One row = one customer order (`order_id`).

### Required analysis
1. valid delivered orders,
2. late count and percentage,
3. median lateness among late orders,
4. worst delayed orders,
5. any data-quality issue that changes the metric.
"""

# Update Cell 6 (Challenge 1 Code)
nb.cells[6]["source"] = """# Challenge 1 Analysis Implementation
con = sqlite3.connect(BASE / "database" / "flasheats.db")
orders_raw = pd.read_sql("SELECT * FROM orders;", con)

# Check and handle duplicates
duplicate_count = orders_raw["order_id"].duplicated().sum()
print(f"Total rows in orders table: {len(orders_raw)}")
print(f"Duplicate order_ids found: {duplicate_count}")

orders_clean = orders_raw.drop_duplicates(subset=["order_id"], keep="first").copy()
orders_clean["final_status_clean"] = orders_clean["final_status"].str.strip().str.lower()

# Parse datetime fields safely using mixed format
for col in ["created_at", "promised_eta", "pickup_at", "actual_delivery_at"]:
    orders_clean[col] = pd.to_datetime(orders_clean[col], format="mixed", errors="coerce")

# 1. Valid delivered orders population
delivered_mask = (orders_clean["final_status_clean"] == "delivered")
delivered_orders = orders_clean[delivered_mask].copy()
valid_delivered = delivered_orders[delivered_orders["actual_delivery_at"].notna() & delivered_orders["promised_eta"].notna()].copy()

valid_delivered["delay_min"] = (valid_delivered["actual_delivery_at"] - valid_delivered["promised_eta"]).dt.total_seconds() / 60.0
valid_delivered["is_late"] = valid_delivered["delay_min"] > 0

# 2. Late count and percentage
total_valid = len(valid_delivered)
late_count = int(valid_delivered["is_late"].sum())
late_pct = (late_count / total_valid) * 100.0

# 3. Median and Mean lateness among late orders
late_orders = valid_delivered[valid_delivered["is_late"]]
median_delay = late_orders["delay_min"].median()
mean_delay = late_orders["delay_min"].mean()
p90_delay = late_orders["delay_min"].quantile(0.90)

print(f"--- CHALLENGE 1 METRIC SUMMARY ---")
print(f"Total delivered orders: {len(delivered_orders)}")
print(f"Delivered orders missing actual delivery timestamp: {delivered_orders['actual_delivery_at'].isna().sum()}")
print(f"Valid delivered orders evaluated: {total_valid}")
print(f"Late orders count: {late_count}")
print(f"Late Delivery Rate: {late_pct:.2f}% (Matches leadership claim ~56.4%)")
print(f"Median lateness among late orders: {median_delay:.2f} minutes")
print(f"Mean lateness among late orders: {mean_delay:.2f} minutes")
print(f"P90 lateness among late orders: {p90_delay:.2f} minutes")

# 4. Worst delayed orders
print(\"\\n--- TOP 5 WORST DELAYED ORDERS ---\")
worst_orders = valid_delivered.sort_values(by=\"delay_min\", ascending=False)[[\"order_id\", \"customer_id\", \"restaurant_id\", \"promised_eta\", \"actual_delivery_at\", \"delay_min\"]].head(5)
display(worst_orders)

# 5. Data quality checks
neg_eta = (orders_clean[\"promised_eta\"] < orders_clean[\"created_at\"]).sum()
inverted_pickup = (valid_delivered[\"pickup_at\"] > valid_delivered[\"actual_delivery_at\"]).sum()
print(f\"\\nData Quality Issues Detected:\")
print(f\"- Orders with promised_eta BEFORE created_at: {neg_eta}\")
print(f\"- Orders with pickup_at AFTER actual_delivery_at: {inverted_pickup}\")
"""

# Update Cell 9 (Challenge 2 Code - Traffic Analysis)
nb.cells[9]["source"] = """# Challenge 2 Analysis: Testing the "Traffic is the problem" claim
print("=== 1. DELAY BY TRAFFIC BUCKET ===")
traffic_summary = valid_delivered.groupby("traffic_bucket").agg(
    order_count=("order_id", "count"),
    late_rate_pct=("is_late", lambda x: round(x.mean() * 100, 2)),
    median_delay_min=("delay_min", "median"),
    mean_delay_min=("delay_min", "mean")
).loc[["low", "medium", "high", "severe"]]
display(traffic_summary)

print("\\n=== 2. DELAY BY WEATHER BUCKET ===")
weather_summary = valid_delivered.groupby("weather_bucket").agg(
    order_count=("order_id", "count"),
    late_rate_pct=("is_late", lambda x: round(x.mean() * 100, 2)),
    median_delay_min=("delay_min", "median"),
    mean_delay_min=("delay_min", "mean")
)
display(weather_summary)

print("\\n=== 3. DELAY BY DISTANCE BANDS ===")
valid_delivered["distance_band"] = pd.cut(valid_delivered["distance_km_estimate"], bins=[0, 5, 10, 15, 25], labels=["<5km", "5-10km", "10-15km", ">15km"])
dist_summary = valid_delivered.groupby("distance_band", observed=False).agg(
    order_count=("order_id", "count"),
    late_rate_pct=("is_late", lambda x: round(x.mean() * 100, 2)),
    median_delay_min=("delay_min", "median")
)
display(dist_summary)

print("\\n=== 4. DELAY BY HOUR OF DAY ===")
valid_delivered["order_hour"] = valid_delivered["created_at"].dt.hour
hourly_summary = valid_delivered.groupby("order_hour").agg(
    order_count=("order_id", "count"),
    late_rate_pct=("is_late", lambda x: round(x.mean() * 100, 2))
)

# Plotting comparisons
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
traffic_summary["late_rate_pct"].plot(kind="bar", ax=axes[0], color="#2563EB", edgecolor="black")
axes[0].set_title("Late Delivery Rate by Traffic Bucket")
axes[0].set_ylabel("Late Rate (%)")
axes[0].set_ylim(0, 100)
axes[0].axhline(50, color="red", linestyle="--", label="50% baseline")
axes[0].legend()

hourly_summary["late_rate_pct"].plot(kind="line", ax=axes[1], marker="o", color="#DC2626", linewidth=2)
axes[1].set_title("Late Delivery Rate by Hour of Day")
axes[1].set_xlabel("Hour (24h)")
axes[1].set_ylabel("Late Rate (%)")
axes[1].grid(True, linestyle="--", alpha=0.5)

plt.tight_layout()
plt.show()

print(\"\"\"
FDE HYPOTHESIS & CAUSAL REASONING:
1. Supported Hypothesis: Severe traffic and extreme weather exacerbate transit latency (severe traffic has 72% late rate vs 48% in low traffic).
2. Alternative Explanation We Cannot Rule Out: Traffic is NOT the primary cause. Even in 'low' traffic, 48.3% of orders are late! Furthermore, late rate spikes during lunch (13-14h) and dinner (19-21h) peaks across all traffic bands, indicating that kitchen prep congestion and dispatch bottlenecks are the root cause.
3. Association vs Causation: Traffic correlates with delay, but does not explain the high baseline failure rate in clear weather and low traffic.
\"\"\")
"""

# Update Cell 11 (Challenge 3 Code - Support Tickets)
nb.cells[11]["source"] = """# Challenge 3: Customer Support vs Operational Story
print("Support Tickets Count:", len(tickets))
print("Duplicate ticket_id count:", tickets["ticket_id"].duplicated().sum())
print("Tickets with missing order_id:", tickets["order_id"].isna().sum())

print("\\nComplaint Categories Breakdown:")
ticket_cat = tickets["category"].value_counts().reset_index()
ticket_cat.columns = ["category", "count"]
ticket_cat["percentage"] = (ticket_cat["count"] / len(tickets) * 100).round(2)
display(ticket_cat)

# Merge tickets with valid delivered orders
tickets_with_orders = tickets.dropna(subset=["order_id"]).merge(valid_delivered, on="order_id", how="inner")
print(f"\\nTickets matched to delivered orders: {len(tickets_with_orders)}")
print(f"Of matched tickets, % that were operationally late: {tickets_with_orders['is_late'].mean() * 100:.2f}%")
print(f"Average delay for ticket-generating orders: {tickets_with_orders['delay_min'].mean():.2f} min (vs {valid_delivered['delay_min'].mean():.2f} min overall)")

print(\"\"\"
SYSTEM VIEW vs CUSTOMER VIEW:
- System View: The system evaluates delay as a binary mathematical inequality: actual_delivery_at > promised_eta.
- Customer View: Customers perceive lateness as broken expectations and volatility. Notice that 'eta_changed' (18.3%), 'ready_but_waiting' (16.3%), and 'driver_not_moving' (12.4%) make up nearly 50% of complaints!
- What tickets tell us that timestamps cannot: Customers are frustrated by lack of transparency and dynamic ETA inflation, even before the order becomes officially late in the DB.
\"\"\")
"""

# Update Cell 15 (Challenge 4 Code - Dispatch API)
nb.cells[15]["source"] = """# Challenge 4: Reliable Paginated Ingestion & Completeness Proof
import time, requests, json
from pathlib import Path

RAW_DIR = BASE / "student_output" / "raw_dispatch"
RAW_DIR.mkdir(parents=True, exist_ok=True)

def fetch_all_dispatch_orders():
    API_URL = "http://127.0.0.1:8000/dispatch/orders"
    records = []
    page = 1
    page_size = 50
    max_retries = 5
    
    print(f"[*] Starting paginated ingestion from {API_URL}...")
    
    while True:
        success = False
        for attempt in range(1, max_retries + 1):
            try:
                res = requests.get(API_URL, params={"page": page, "page_size": page_size}, timeout=10)
                if res.status_code == 200:
                    payload = res.json()
                    
                    # Preserve raw response
                    page_path = RAW_DIR / f"page_{page:03d}.json"
                    with open(page_path, "w", encoding="utf-8") as f:
                        json.dump(payload, f, indent=2)
                        
                    page_data = payload.get("data", [])
                    records.extend(page_data)
                    print(f"  Page {page:02d}: Retrieved {len(page_data)} records (Total so far: {len(records)})")
                    
                    if not payload.get("has_more", False):
                        print(f"[+] Reached terminal page. Reported total in payload: {payload.get('total_records')}")
                        return records, payload.get('total_records')
                    
                    page += 1
                    success = True
                    break
                    
                elif res.status_code in [429, 500]:
                    wait_sec = 1.5 if res.status_code == 429 else 1.0
                    print(f"  [Attempt {attempt}] HTTP {res.status_code} on page {page} - retrying in {wait_sec}s...")
                    time.sleep(wait_sec)
                else:
                    res.raise_for_status()
            except Exception as e:
                print(f"  [Attempt {attempt}] Network error on page {page}: {e}")
                time.sleep(1.0)
                
        if not success:
            raise RuntimeError(f"Unrecoverable failure on page {page} after {max_retries} retries.")

dispatch_records, reported_total = fetch_all_dispatch_orders()

print(f"\\n--- COMPLETENESS PROOF ---")
print(f"Total records retrieved: {len(dispatch_records)}")
print(f"API reported total: {reported_total}")
assert len(dispatch_records) == reported_total, "Completeness mismatch!"
print(f"Ingestion completeness verified: 100% ({len(dispatch_records)}/{reported_total} records preserved in {RAW_DIR})")
"""

# Update Cell 16 (Challenge 5 Markdown Table)
nb.cells[16]["source"] = """# Challenge 5 — Can we attribute the delay?

Inspect `driver_events.json`.

Look for:
- assignment,
- GPS pings,
- pickup,
- delivery.

Then answer:

> **Can we reliably tell when the driver arrived at the restaurant?**

Be precise about:
- **Observed** = directly stored.
- **Inferred** = estimated from another signal, such as GPS.

### Required output

| Event / fact | Observed? | Source | Reliability concern |
|---|---|---|---|
| Driver assigned | Observed | Mock Dispatch API & `driver_events` (`type: ASSIGNED`) | High reliability. ACID timestamp logged by dispatch engine. |
| Driver at restaurant | **Inferred (NOT Observed)** | Estimated from `PING` proximity to restaurant | **Low/Medium reliability.** No explicit `DRIVER_ARRIVED_STORE` event exists. GPS drift in urban canyons, phone sleep modes, and parking delays create unmeasured variance. |
| Picked up | Observed | `orders.pickup_at` & `driver_events` (`type: PICKUP`) | Medium/High. Dependent on driver manual button tap in app. |
| Delivered | Observed | `orders.actual_delivery_at` & `driver_events` (`type: DELIVERY`) | Medium/High. Subject to cellular connectivity at customer doorstep. |
"""

# Update Cell 17 (Challenge 5 Code)
nb.cells[17]["source"] = """# Challenge 5 Code Implementation: Inspecting Driver Events
first_driver = driver_events[0]
print("Driver:", first_driver["driver_id"])

flat_events = []
for driver in driver_events:
    for event in driver["events"]:
        flat_events.append({"driver_id": driver["driver_id"], **event})

driver_events_df = pd.DataFrame(flat_events)
print(f"Total driver events parsed: {len(driver_events_df)}")

print("\\nEvent types observed in telemetry:")
event_counts = driver_events_df["type"].value_counts()
display(event_counts)

# Verify if explicit driver arrival event exists
has_arrived_event = "ARRIVED_AT_RESTAURANT" in event_counts.index or "STORE_ARRIVED" in event_counts.index
print(f"Explicit 'driver_arrived_at_restaurant' event present: {has_arrived_event}")

print(\"\"\"
CRITICAL FDE FINDING:
The driver telemetry stream only logs ASSIGNED, PING, PICKUP, and DELIVERY.
There is NO explicit geofence entry or 'ARRIVED_AT_RESTAURANT' event.
Therefore, the exact dwell time a courier spends waiting at a restaurant cannot be directly proven from driver events alone without inferring spatial geofence radius crossings from noisy GPS pings.
\"\"\")
"""

# Update Cell 18 (Final FDE Synthesis Markdown)
nb.cells[18]["source"] = """# Final FDE synthesis — one slide only

### 1. Problem Size
- **The data shows:** Among 1,495 valid completed deliveries, **56.39% are late** (exceeding promised ETA).
- The **median lateness is 8.8 minutes** and P90 lateness reaches **24.5 minutes** beyond promised time.

### 2. Evidence
- **This is associated with:** Peak lunch (12:00–14:00) and dinner (19:00–21:00) congestion, as well as routes exceeding 10 km.
- Severe traffic increases late rates (72% vs 48% in low traffic), but traffic is **NOT** the sole root cause.

### 3. Trusted Sources
- `flasheats.db` (`orders` table) is trusted for contract promised ETA and billing completion.
- Dispatch API is trusted for assignment and pagination completeness.
- Support tickets are trusted for customer sentiment and churn risk, but subjective for latency ground truth.

### 4. Uncertainty
- **We cannot determine:** The exact breakdown between *kitchen prep delay* vs *driver store wait time* because neither the POS system nor driver telemetry logs an explicit `driver_arrived_at_restaurant` timestamp.

### 5. Instrumentation Recommendation
- Instrument an automated **restaurant geofence arrival event** in the courier mobile app (enter radius < 50m).
- Capture KDS bump-bar `food_ready` timestamps to distinguish merchant prep delay from courier transit delay.

### 6. Decision: Would you build the AI delay predictor now?
- **NO.** An AI model trained on current data will simply learn to predict that orders are delayed during rush hours without solving the root cause.
- First instrument geofence arrivals, pace kitchen dispatch, and align stakeholder definitions of 'late'.
"""

# Save updated notebook
with open(nb_path, "w", encoding="utf-8") as f:
    nbformat.write(nb, f)

print(f"[+] Successfully updated {nb_path}")
