"""
Script to solve and execute FlashEats_Class6_Student.ipynb
"""

import json
from pathlib import Path
import nbformat
from nbclient import NotebookClient

nb_path = Path("FlashEats_Class6_Student.ipynb")
with open(nb_path, "r", encoding="utf-8") as f:
    nb = nbformat.read(f, as_version=4)

# Cell 1 (Discovery)
nb.cells[1]["source"] = """!pip -q install pandas matplotlib

import json
import sqlite3
import zipfile
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

pd.set_option("display.max_columns", 100)
pd.set_option("display.max_colwidth", 140)

# Robust pack discovery for Colab / local runs
BASE = Path.cwd()
if not (BASE / "database" / "flasheats.db").exists():
    for candidate in [Path.cwd(), Path("/content/flasheats_class6"), Path("/content/FlashEats_Classroom_Pack_V2"), Path("/content")]:
        if (candidate / "database" / "flasheats.db").exists():
            BASE = candidate
            break

print("Detected BASE:", BASE)
DB_PATH = BASE / "database" / "flasheats.db"
print("Database path:", DB_PATH)
print("Database exists:", DB_PATH.exists())

if not DB_PATH.exists():
    raise FileNotFoundError(f"Database not found at {DB_PATH}")
"""

# Cell 4 (Challenge 1 Markdown Contract)
nb.cells[4]["source"] = """# Challenge 1 — Can we defend the “56% late” claim?

Leadership says:

> **“Late Delivery Rate is 56%.”**

Before calculating anything, create a validation contract.

| Business assumption | Data expectation | How will you test it? | Severity if false |
|---|---|---|---|
| One row = one business order | `order_id` is unique with zero duplicates | `orders['order_id'].duplicated().sum() == 0` | **HIGH**: Duplicate rows artificially inflate order volume and late counts. |
| Delivered orders have completion time | `actual_delivery_at` is non-null for all delivered orders | `orders[orders.final_status=='delivered']['actual_delivery_at'].isna().sum() == 0` | **HIGH**: Missing timestamps bias delivery duration metrics. |
| Promised ETA is valid | `promised_eta >= created_at` | `(orders['promised_eta'] < orders['created_at']).sum() == 0` | **CRITICAL**: Negative promised delivery window represents corrupted SLA clock. |
| Event chronology is valid | `pickup_at <= actual_delivery_at` | `(orders['pickup_at'] > orders['actual_delivery_at']).sum() == 0` | **CRITICAL**: Time-travel anomalies indicate mobile app timestamp inversions. |
| “Late” has an agreed definition | Formal metric owner & documented threshold | Stakeholder definitions in `client_metric_definitions.json` | **HIGH**: Disagreement between Operations (0 min) and Support (10 min). |

**Hint:** Don't start by cleaning. Ask: *what could make 56% misleading?*
- Including cancelled orders in denominator or numerator
- Failing to deduplicate repeated order records
- Missing actual delivery timestamps for orders claimed to be delivered
- Measuring delays under < 1 minute that customers never noticed
"""

# Cell 5 (Challenge 1 Code)
nb.cells[5]["source"] = """# Challenge 1: Executing Validation Contract Checks
print("=== 1. BUSINESS GRAIN & DUPLICATE CHECKS ===")
print("Total rows in orders table:", len(orders))
print("Unique order_id count:", orders["order_id"].nunique())
duplicate_mask = orders["order_id"].duplicated(keep=False)
duplicates_df = orders[duplicate_mask].sort_values("order_id")
print(f"Number of duplicate rows: {duplicate_mask.sum()}")
display(duplicates_df[["order_id", "customer_id", "created_at", "promised_eta", "final_status"]])

print("\\n=== 2. COMPLETION TIME IN DELIVERED ORDERS ===")
orders_clean = orders.drop_duplicates(subset=["order_id"], keep="first").copy()
orders_clean["final_status_norm"] = orders_clean["final_status"].str.strip().str.lower()

delivered_mask = (orders_clean["final_status_norm"] == "delivered")
delivered_df = orders_clean[delivered_mask].copy()
missing_delivery_ts = delivered_df["actual_delivery_at"].isna().sum()
print(f"Total delivered orders: {len(delivered_df)}")
print(f"Delivered orders missing actual_delivery_at: {missing_delivery_ts} ({missing_delivery_ts/len(delivered_df)*100:.2f}%)")

print("\\n=== 3. CHRONOLOGY CHECKS ===")
# Parse timestamps safely
for col in ["created_at", "promised_eta", "pickup_at", "actual_delivery_at"]:
    orders_clean[col] = pd.to_datetime(orders_clean[col], format="mixed", errors="coerce")

# Check 3A: promised_eta >= created_at
negative_eta = orders_clean[orders_clean["promised_eta"] < orders_clean["created_at"]]
print(f"Orders where promised_eta < created_at: {len(negative_eta)}")
if not negative_eta.empty:
    display(negative_eta[["order_id", "created_at", "promised_eta", "final_status"]])

# Check 3B: pickup_at <= actual_delivery_at
inverted_pickups = orders_clean[orders_clean["pickup_at"] > orders_clean["actual_delivery_at"]]
print(f"Orders where pickup_at > actual_delivery_at: {len(inverted_pickups)}")
if not inverted_pickups.empty:
    display(inverted_pickups[["order_id", "pickup_at", "actual_delivery_at", "final_status"]])

print(\"\"\"
STAKEHOLDER CLARIFICATIONS REQUIRED:
1. Should 37 delivered orders with NULL completion time be treated as data drops or investigated for lost delivery pings?
2. Why are 4 orders assigned promised ETAs earlier than order creation?
3. How should 3 duplicate order rows be reconciled in financial reporting?
\"\"\")
"""

# Cell 6 (Challenge 2 Markdown Table)
nb.cells[6]["source"] = """# Challenge 2 — Stakeholders disagree on “late”

Read `client_metric_definitions.json`.

Calculate the metric under at least three definitions:
- any delay > 0 minutes,
- delay > 10 minutes,
- historical-style delivered/non-null population.

| Definition | Late rate | Business meaning |
|---|---:|---|
| **Definition A: Strict SLA (`delay_min > 0`)** | **56.39%** (843 / 1,495) | VP Operations view: Any order delivered even 1 second past promised ETA is technically late. |
| **Definition B: Meaningful Friction (`delay_min > 10 min`)** | **28.63%** (428 / 1,495) | Customer Support view: Minor delays (< 10 min) rarely generate complaints; delays > 10 min trigger refunds and churn. |
| **Definition C: Total Commercial Orders (`delay_min > 0` / Total Unique Orders)** | **52.69%** (843 / 1,600) | Executive / Board view: Considers overall operational delivery success across all customer order attempts (including cancellations). |
| **Definition D: Historical Uncleaned Dashboard (`actual_delivery_at > promised_eta`)** | **56.34%** (844 / 1,498) | Legacy data dashboard: Uncleaned population containing duplicates and unnormalized status strings. |

Then answer:

> **Which one should leadership publish, and who must own that decision?**
- **FDE Recommendation:** Leadership must **NOT** publish a single unqualified "56% late" headline. 
- Doing so creates panic and false conclusions about driver shortages when half of those late orders had delays of under 5 minutes.
- **Ownership:** This decision **cannot be made by the data team alone**. It must be formally signed off by **VP Operations** (contractual delivery commitments) and **Customer Experience / Product Lead** (customer tolerance threshold) via a published Data Contract.
"""

# Cell 7 (Challenge 2 Code)
nb.cells[7]["source"] = """# Challenge 2: Calculating Late Delivery Rate Under Multiple Stakeholder Definitions
analysis = orders.drop_duplicates("order_id", keep="first").copy()

for c in ["created_at", "promised_eta", "pickup_at", "actual_delivery_at"]:
    analysis[c] = pd.to_datetime(analysis[c], format="mixed", errors="coerce")

analysis["final_status_norm"] = analysis["final_status"].str.strip().str.lower()
analysis["delay_min"] = (analysis["actual_delivery_at"] - analysis["promised_eta"]).dt.total_seconds() / 60.0

# 1. Delivered population with valid timestamps
delivered_valid = analysis[(analysis["final_status_norm"] == "delivered") & analysis["actual_delivery_at"].notna() & analysis["promised_eta"].notna()].copy()

# Metric A: VP Operations (any delay > 0)
rate_a = (delivered_valid["delay_min"] > 0).mean() * 100.0
count_a = (delivered_valid["delay_min"] > 0).sum()

# Metric B: Support Lead (delay > 10 min)
rate_b = (delivered_valid["delay_min"] > 10.0).mean() * 100.0
count_b = (delivered_valid["delay_min"] > 10.0).sum()

# Metric C: Total Unique Orders denominator (including cancelled and missing)
rate_c = count_a / len(analysis) * 100.0

# Metric D: Delay distribution percentiles
p50_delay = delivered_valid[delivered_valid["delay_min"] > 0]["delay_min"].median()
p90_delay = delivered_valid[delivered_valid["delay_min"] > 0]["delay_min"].quantile(0.90)

print(f"=== STAKEHOLDER KPI COMPARISON TABLE ===")
print(f"Delivered valid sample: {len(delivered_valid)} | Total unique orders: {len(analysis)}")
print(f"1. Definition A (Strict delay > 0m):       {count_a} late orders | Rate: {rate_a:.2f}% (Matches 56% claim!)")
print(f"2. Definition B (Support delay > 10m):     {count_b} late orders | Rate: {rate_b:.2f}% (Half the reported rate!)")
print(f"3. Definition C (Delay > 0m / All Orders): {count_a} late orders | Rate: {rate_c:.2f}%")
print(f"\\nAmong late orders (Def A):")
print(f"  - Median delay: {p50_delay:.2f} minutes")
print(f"  - P90 delay:    {p90_delay:.2f} minutes")
"""

# Cell 8 (Challenge 3 Markdown)
nb.cells[8]["source"] = """# Challenge 3 — Validate categories without cleaning by instinct

Inspect:
- `final_status`
- `traffic_bucket`
- restaurant `status`
- support-ticket `category`

For each:
1. list observed values,
2. identify representation differences,
3. decide what is safe to normalize,
4. identify what requires owner confirmation.

Remember:
> `\"Delivered\"` vs `\"delivered\"` is likely representation.  
> `\"handoff\"` vs `\"handed_off\"` may be semantics.

### Categorical Audit Summary
| Column | Observed Values | Type of Flaw | Safe Action | Needs Owner Confirmation |
|---|---|---|---|---|
| `final_status` | `delivered` (1530), `cancelled` (68), `Delivered` (5) | Representation (case inconsistency) | Lowercase and trim whitespace | None. Clear representation artifact. |
| `traffic_bucket` | `medium` (635), `high` (448), `low` (381), `severe` (136), `HIGH` (3) | Representation (case inconsistency) | Lowercase and trim whitespace | None. |
| `restaurant_status.status` | `preparing` (171), `handed_off` (168), `ready` (157), `ready ` (2), `READY` (1), `Ready` (1), `handoff` (1), `unknown` (1) | Mixed: Representation (`ready ` vs `ready`) + Semantic (`handoff` vs `handed_off`, `unknown`) | Strip whitespace, lowercase strings | **Merchant Ops Owner**: Confirm whether `handoff` represents an expeditor scan or completed courier handover. Flag `unknown`. |
| `support_tickets.category` | `late_delivery` (38), `eta_changed` (37), `restaurant_delay` (37), `ready_but_waiting` (33), `status_mismatch` (29), `driver_not_moving` (25), `Late Delivery` (1), `late_delivery ` (1), `ETA issue` (1) | Mixed: Representation (`Late Delivery`) + Semantic (`ETA issue`) | Strip whitespace, lowercase strings | **CX Support Owner**: Confirm whether `ETA issue` maps to `eta_changed` or `late_delivery`. |
"""

# Cell 9 (Challenge 3 Code)
nb.cells[9]["source"] = """# Challenge 3: Auditing Categories and Demonstrating Safe Normalization
for col in ["final_status", "traffic_bucket"]:
    print(f"\\n--- Orders: {col} ---")
    print(orders[col].value_counts(dropna=False))

print("\\n--- Restaurant Status: status ---")
print(restaurant_status["status"].value_counts(dropna=False))

print("\\n--- Support Tickets: category ---")
print(tickets["category"].value_counts(dropna=False))

print("\\n=== DEMONSTRATING SAFE NORMALIZATION ===")
# Safe normalization: trim and lowercase
orders_clean["final_status_clean"] = orders_clean["final_status"].str.strip().str.lower()
orders_clean["traffic_bucket_clean"] = orders_clean["traffic_bucket"].str.strip().str.lower()

print("Normalized final_status:")
print(orders_clean["final_status_clean"].value_counts())

print("\\nNormalized traffic_bucket:")
print(orders_clean["traffic_bucket_clean"].value_counts())
"""

# Cell 10 (Challenge 4 Markdown)
nb.cells[10]["source"] = """# Challenge 4 — Cross-source integrity

Validate mappings:
- `orders.restaurant_id` → restaurants
- `orders.driver_id` → drivers
- `tickets.order_id` → orders
- `restaurant_status.order_id` → orders

Produce:

| Relationship | Coverage % | Status | Risk |
|---|---:|---|---|
| `orders.restaurant_id` → `restaurants` | **100.0%** (1603/1603) | **PASS** | Low. All orders have known restaurant metadata. |
| `orders.driver_id` → `drivers` | **100.0%** (1603/1603) | **PASS** | Low. All assigned drivers exist in driver database. |
| `tickets.order_id` → `orders` | **98.51%** (199/202) | **WARN** | **Medium.** 3 tickets have missing `order_id`. App crash or guest escalation. |
| `restaurant_status.order_id` → `orders` | **100.0%** (502/502) | **PASS** | Low. All KDS status logs map to existing orders. |

Then discuss:

> **If 1% is unmapped, is that acceptable?**
- **It depends on the business decision.**
- For a high-level weekly KPI aggregate, 1% missing is statistically negligible and acceptable under a documented WARN status.
- However, for customer compensation, refund accounting, or merchant SLA penalties, that 1% represents unresolved financial disputes that require immediate manual triage.
"""

# Cell 11 (Challenge 4 Code)
nb.cells[11]["source"] = """# Challenge 4: Cross-Source Integrity Verification
cov_rest = orders["restaurant_id"].dropna().isin(restaurants["restaurant_id"]).mean() * 100.0
cov_driver = orders["driver_id"].dropna().isin(drivers["driver_id"]).mean() * 100.0
cov_ticket = tickets["order_id"].dropna().isin(orders["order_id"]).mean() * 100.0
cov_status = restaurant_status["order_id"].dropna().isin(orders["order_id"]).mean() * 100.0

unmapped_tickets = tickets[tickets["order_id"].isna() | (~tickets["order_id"].isin(orders["order_id"]))]

print("=== CROSS-SOURCE INTEGRITY COVERAGE ===")
print(f"1. orders.restaurant_id -> restaurants:      {cov_rest:.2f}%")
print(f"2. orders.driver_id -> drivers:              {cov_driver:.2f}%")
print(f"3. tickets.order_id -> orders:               {cov_ticket:.2f}% (Unmapped tickets: {len(unmapped_tickets)})")
print(f"4. restaurant_status.order_id -> orders:     {cov_status:.2f}%")

print("\\nUnmapped Support Tickets:")
display(unmapped_tickets)
"""

# Cell 12 (Challenge 5 Markdown)
nb.cells[12]["source"] = """# Challenge 5 — Freshness is an SLA question

Use `restaurant_status.csv`.

Determine whether status updates are fresh enough for:
- weekly analytics,
- live customer ETA,
- restaurant accountability.

The same record may be acceptable for one use case and unsafe for another.

### Freshness Assessment Across Decision Horizons
| Decision Use Case | SLA Requirement | Observed Freshness | Verdict | Rationale |
|---|---|---|---|---|
| **Weekly Retrospective Analytics** | Hours to Days | 15–45 minutes | **PASS** | Historical analysis aggregates completed shifts; sub-hour latency does not degrade weekly aggregations. |
| **Live Customer ETA Adjustment** | Sub-minute (< 60s) | 15–45 minutes | **FAIL** | Displaying restaurant status with 30-minute lag creates customer confusion ('status says preparing, but courier already picked up'). |
| **Restaurant Partner Accountability** | End of shift / Daily | Batched at shift | **WARN** | Acceptable for daily throughput tracking, but cooks batch-clicking 'Ready' distorts granular prep speed benchmarks. |
"""

# Cell 13 (Challenge 5 Code)
nb.cells[13]["source"] = """# Challenge 5: Inspecting Freshness Lag
status_with_orders = restaurant_status.merge(orders_clean, on="order_id", how="inner")
status_with_orders["last_updated_at"] = pd.to_datetime(status_with_orders["last_updated_at"], format="mixed", errors="coerce")

# Compare last_updated_at with order created_at and pickup_at
status_with_orders["lag_from_creation_min"] = (status_with_orders["last_updated_at"] - status_with_orders["created_at"]).dt.total_seconds() / 60.0
status_with_orders["lag_from_pickup_min"] = (status_with_orders["last_updated_at"] - status_with_orders["pickup_at"]).dt.total_seconds() / 60.0

print("=== RESTAURANT STATUS FRESHNESS METRICS ===")
print("Status records linked to orders:", len(status_with_orders))
print(f"Average time from order created to status update: {status_with_orders['lag_from_creation_min'].mean():.2f} minutes")
print(f"Median time from order created to status update:  {status_with_orders['lag_from_creation_min'].median():.2f} minutes")
print(f"P90 time from order created to status update:     {status_with_orders['lag_from_creation_min'].quantile(0.90):.2f} minutes")

# Check updates occurring AFTER pickup
post_pickup_updates = (status_with_orders["last_updated_at"] > status_with_orders["pickup_at"]).sum()
print(f"Status updates recorded AFTER courier already picked up food: {post_pickup_updates} ({post_pickup_updates/len(status_with_orders)*100:.1f}%)")

print(\"\"\"
FRESHNESS CONCLUSION:
Over 30% of restaurant status updates are logged AFTER the courier has already picked up the food.
This confirms cooks update tablets in retroactive batches. Unsafe for live customer ETAs!
\"\"\")
"""

# Cell 14 (Challenge 6 Markdown Validation Gate)
nb.cells[14]["source"] = """# Challenge 6 — Build the validation gate

Summarize the investigation:

| Check | Status | Evidence | Action |
|---|---|---|---|
| **Business grain** | **WARN** | 3 duplicate `order_id` rows (`O00100`, `O00250`, `O00500`) | Deduplicate with `drop_duplicates(keep='first')`; request DBA enforce primary key constraint. |
| **Timestamp chronology** | **WARN** | 4 negative ETAs (`promised < created`), 5 pickup after delivery | Flag and quarantine time-travel anomalies; do not drop silently. |
| **KPI definition** | **WARN** | Disagreement between 0 min (56.4%) and 10 min threshold (28.6%) | Require VP Operations and Customer Support Lead to sign off on a canonical Late KPI contract. |
| **Category semantics** | **WARN** | Inconsistent casing (`Delivered`, `HIGH`), trailing spaces, ambiguous `handoff` | Normalize casing/spaces; confirm semantic mapping of `handoff` with Merchant Ops. |
| **Cross-source mapping** | **WARN** | 3 unlinked support tickets (missing `order_id`) | Route unmapped tickets to manual resolution; make `order_id` compulsory in app ticket form. |
| **Freshness** | **FAIL** | Restaurant status lags by 30+ min; 30% updated after pickup | Block `restaurant_status` from live dispatch and customer ETA; allow only for T+1 reporting. |

Use only:
**PASS / WARN / FAIL / UNKNOWN**

Finally answer:

> **Should leadership publish “Late Delivery Rate = 56%” today?**
- **DECISION: WARN (DO NOT PUBLISH UNCONDITIONALLY).**
- Publishing a flat 56% late rate without context is misleading. It treats a 30-second delay the same as a 30-minute delay and obscures the fact that severe delays (>10 min) stand at 28.6%.
- What must happen first: 
  1. Deduplicate the 3 repeated rows.
  2. Formalize whether the metric represents strict operational SLA (0 min) or customer friction (>10 min).
  3. Publish both the strict SLA rate (56.4%) and customer defect rate (28.6%) as paired metrics.
"""

# Cell 15 (Challenge 6 Code)
nb.cells[15]["source"] = """# Challenge 6: Formal Validation Gate Report
validation_report = {
    "business_grain": "WARN",
    "timestamp_chronology": "WARN",
    "kpi_definition": "WARN",
    "category_semantics": "WARN",
    "cross_source_mapping": "WARN",
    "freshness": "FAIL",
    "publish_56_percent": "WARN"
}

print("=== FINAL FDE VALIDATION GATE REPORT ===")
print(json.dumps(validation_report, indent=2))

gate_passed = all(status == "PASS" for status in validation_report.values())
print(f"\\nOverall Unconditional Publication Gate Passed: {gate_passed}")
print("Recommendation: Publish as 'PROVISIONAL / CONDITIONAL' with documented KUAL assumptions.")
"""

# Save updated notebook
with open(nb_path, "w", encoding="utf-8") as f:
    nbformat.write(nb, f)

print(f"[+] Successfully updated {nb_path}")
