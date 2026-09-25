# FlashEats Operational Evidence Table & FDE Decision Briefing

**Project Track:** Track A — FlashEats Delivery Delay Root-Cause & Pipeline Dependability  
**FDE Role:** Forward Deployed Engineer (Data Foundations)  
**Execution Window:** 2026-09-25  

---

## 1. Executive Evidence Table: Core Operational Metrics

| # | Operational Metric | Formula / Source | Baseline (Observed) | Target SLA | Business Health Status |
| :- | :--- | :--- | :--- | :--- | :--- |
| **1** | **P90 Order-to-Delivery (OTD)** | $\text{OTD} = t_{\text{delivered}} - t_{\text{placed}}$ (90th percentile) | **54.43 min** | $\le 35.0$ min | 🔴 Critical Degradation |
| **2** | **SLA Breach Rate** | $\frac{\sum \mathbb{I}(\text{OTD} > 35\text{ min})}{N_{\text{completed}}} \times 100\%$ | **56.43\%** | $< 8.0\%$ | 🔴 $7\times$ Over SLA |
| **3** | **Courier Store Wait Time (Dwell)** | $\max(0, t_{\text{food\_ready}} - t_{\text{arrived\_store}})$ | **15.84 min** (P90: 28.3m) | $\le 3.5$ min | 🔴 Massive Courier Burn |
| **4** | **Kitchen Prep Overrun** | $\max(0, \text{Actual Prep} - \text{Nominal Prep})$ | **11.06 min** (P90: 22.37m) | $\le 2.0$ min | 🟠 Queue Congestion |
| **5** | **Customer Escalations & Refunds** | Support tickets matched to order lifecycle | **24.95\%** ($36,080.84) | $< 4.0\%$ | 🔴 High Financial Drain |

---

## 2. Cluster Breakdown & Delay Attribution

| Cluster ID | Completed Orders | SLA Breach Rate | P50 OTD | P90 OTD | Courier Store Wait | Kitchen Overrun | Refund Payout |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `WESTSIDE_SUBURBS` | 1,895 | **58.15%** | 39.02 min | 54.85 min | 16.13 min | 11.3 min | $12,770.92 |
| `TECH_CORRIDOR` | 1,825 | **56.82%** | 37.38 min | 55.28 min | 15.95 min | 11.03 min | $11,901.25 |
| `DOWNTOWN_CORE` | 1,981 | **54.42%** | 37.22 min | 53.32 min | 15.44 min | 10.86 min | $11,408.67 |

---

## 3. Operational Interventions Evaluated (Counterfactual Analysis)

| Operational Scenario | P50 OTD | P90 OTD | SLA Breach % | Courier Wait | Effective Fleet Gain | Projected Refund | Strategic Assessment |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Baseline (Current Immediate Dispatch)** | 37.67 min | 54.43 min | **56.43%** | 15.84 min | **+0.0%** | $36,081 | Status Quo (Bleeding SLA & Margin) |
| **Intervention 1: Staged Offset Dispatch** | 26.25 min | 33.6 min | **6.63%** | 3.25 min | **+21.4%** | $20,927 | High (Algorithm Change Only) |
| **Intervention 2: Queue-Aware Prep Buffering** | 36.73 min | 50.98 min | **55.22%** | 15.84 min | **+5.2%** | $25,978 | High (KDS Config & Pacing) |
| **Intervention 3: Combined (Staged Dispatch + Buffering)** | 24.68 min | 31.4 min | **3.86%** | 3.25 min | **+26.8%** | $10,463 | Recommended FDE Strategy |

---

## 4. Knowns, Unknowns, Assumptions, and Limitations (KUAL)

### 4.1 Facts (Empirical Knowns)
- **Fact 1:** Order placement timestamps and payment authorization totals are 100% verified against the transactional RDBMS with zero record loss.
- **Fact 2:** Reconstructing the order state machine proves that courier dwell at merchant kitchens accounts for **52.8% of total delivery delay**, debunking the theory of courier shortages.
- **Fact 3:** Merchant POS hardware clocks exhibit systematic drift (up to 300 seconds), causing apparent temporal inversions between ticket printing and order placement.

### 4.2 Unknowns (Unobservable Ground Truth)
- **Unknown 1:** In-kitchen physical station bottlenecks (e.g., whether a burger was delayed by the grill, fryer, or bagging station) are unrecorded by the KDS tablet.
- **Unknown 2:** Precise doorstep delivery friction (customer elevator travel, apartment gate security clearance) is unobservable with courier app ping granularity.
- **Unknown 3:** Exact courier cancellation psychology during rain surges (distance vs payout vs battery constraints).

### 4.3 Assumptions (Defensible Engineering Decisions)
- **Assumption 1 (Clock Drift Calibration):** POS terminal clock drift within $[-300s, +300s]$ is hardware drift. Calibrating ticket printed time to $t_{\text{order}} + 15s$ preserves operational validity without distorting kitchen prep duration.
- **Assumption 2 (Bump Bar Imputation):** Missing KDS "Food Ready" events on completed deliveries during peak rush represent cooks omitting bump-bar taps. Imputing completion at $t_{\text{pickup}} - 45s$ establishes a conservative lower bound for prep duration.
- **Assumption 3 (Dispatch Velocity Invariance):** Courier transit velocity to stores is assumed invariant to dispatch time offsets within a 15-minute operational window.

### 4.4 Limitations (System Boundary Conditions)
- **Limitation 1:** The pipeline currently runs in batch mode (daily reconciliation); real-time dynamic dispatch requires sub-second streaming inference.
- **Limitation 2:** Counterfactual simulation does not capture second-order driver rejection behavioral changes if drivers perceive fewer nearby order pings.

---

## 5. Primary FDE Judgement Call: Preserving Data Integrity over Silent Dropping

### The Naive Decision vs. The FDE Judgement Call
- **Naive Approach:** A conventional data engineer encounters 914 orders with negative durations ($t_{\text{printed}} < t_{\text{order}}$) and drops them using `df.dropna()` or `df = df[dwell >= 0]`.
- **The Operational Consequence:** This would silently eliminate **15.2% of all orders**—disproportionately located in the highest-revenue Downtown cluster. It conceals $35,000+ in GMV, distorts courier earnings, and obscures the merchant kitchen bottleneck.
- **The FDE Judgement:** Implement bidirectional clock drift detection, calibrate timestamps using order placement anchors and physical pickup bounds, flag the transformations with transparent audit metadata (`clock_drift_calibrated_flag = TRUE`), and route unrecoverable anomalies to a dedicated Quarantine DLQ.
