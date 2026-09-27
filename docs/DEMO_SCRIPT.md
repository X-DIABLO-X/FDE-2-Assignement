# FlashEats FDE Project: 5-Minute Video Demonstration Script

**Candidate:** Harshit Tiwari (Roll: `24BCS10277`)  
**Project:** Track A — FlashEats Delivery Delay Root-Cause & Dependable KPI Pipeline  
**Target Duration:** Exactly 5 Minutes (0:00 – 5:00)  
**Tone:** Confident, structured, business-driven Forward Deployed Engineer (FDE)  

---

## Quick Navigation / Scene Breakdown

| Timestamp | Scene / Section | On-Screen Action | Core Message & Objective |
| :--- | :--- | :--- | :--- |
| **0:00 – 0:50** | **1. The Business Crisis & Misconception** | Show `README.md` & `24BCS10277_Harshit_Tiwari.pdf` Header | Establish the problem first: P90 delivery at 54.4m, 56.4% SLA breach, $36k/day refunds. Leadership assumed courier shortage. |
| **0:50 – 1:40** | **2. Architecture & Multi-Source Ingestion** | Show `docs/source_map.png` & run Ingest command | 4 fragmented client sources, Bronze immutability, SHA-256 hashes, exact penny GMV reconciliation. |
| **1:40 – 2:40** | **3. Data Profiling & The Core FDE Judgement Call** | Run Validation stage & open `quarantine_audit.parquet` | Why naive `dropna()` is fatal (discards 15.2% orders / $35k GMV). Defensible calibration vs Quarantine DLQ. |
| **2:40 – 3:35** | **4. Workflow Modeling & The Delay Nexus** | Show `docs/workflow_fsm.png` & run State Machine | Decomposing 5 stages. Proving 52.8% delay is Rider Store Wait (15.8m) due to premature immediate dispatch. |
| **3:35 – 4:25** | **5. Gold Marts & Counterfactual Interventions** | Run Marts & terminal dashboard | Evaluating Staged Offset Dispatch: P90 drops to 33.6m, SLA breach drops to 6.6%, unlocks +21.4% fleet capacity. |
| **4:25 – 5:00** | **6. Conclusion & Executive Decision Loop** | Show Evidence Table in `docs/evidence_table.md` | Summarize issues, solutions, KUAL framework, and business impact. "From client data to dependable business decision." |

---

## Detailed Minute-by-Minute Narration & Screen Directions

---

### [0:00 – 0:50] Scene 1: The Business Problem & The Client Misconception

#### 🖥️ What to Show on Screen:
1. Open the GitHub repository: `https://github.com/X-DIABLO-X/FDE-2-Assignement`.
2. Scroll to the top of `README.md` or display Page 1 of `24BCS10277_Harshit_Tiwari.pdf`.
3. Highlight the headline metrics: **P90 OTD: 54.4 min**, **SLA Breach: 56.4%**, **Refunds: $36,080/day**.

#### 🎙️ Spoken Narration:
> *"Hello everyone! My name is Harshit Tiwari, roll number 24BCS10277. Today, I'm presenting my Forward Deployed Engineer project for FlashEats quick-commerce logistics.*
>
> *Before touching any code or discussing AI models, an FDE must answer one critical question: **Which business problem deserves to be solved?***
>
> *FlashEats promises ultra-fast 30-minute delivery with a contractual SLA ceiling of 35 minutes. Over the past quarter, delivery performance collapsed. 90th percentile delivery times surged to **54.4 minutes**, triggering an alarming **56.4% SLA breach rate** and burning over **$36,000 every single day** in customer refunds. Customer retention dropped by 14%.*
>
> *Leadership’s immediate reaction was: 'We have a courier shortage. We need to hire hundreds of new drivers and increase wage subsidies.'*
>
> *As the FDE, my objective was to resist speculative hiring, connect the client's fragmented operational systems, and build a trustworthy, explainable path from raw data to an actionable business decision."*

---

### [0:50 – 1:40] Scene 2: Multi-Source Architecture & Mathematical Completeness Proofs

#### 🖥️ What to Show on Screen:
1. Display the architectural diagram: `docs/source_map.png`.
2. Open terminal and run:
   ```bash
   python -c "from src.ingest.ingest_manager import IngestionManager; IngestionManager().run_all()"
   ```
3. Highlight the terminal output showing: `Mathematical completeness verified: True` and `Financial GMV Control Total: $231,406.85`.

#### 🎙️ Spoken Narration:
> *"The first engineering challenge was fragmentation across four distinct operational systems:*
> 1. *The Core Order Management System in a transactional SQLite/Postgres database,*
> 2. *The Fleet Telematics Service exposing driver dispatches via REST API JSON,*
> 3. *Merchant Kitchen Display Systems (KDS) exporting daily prep CSV logs, and*
> 4. *Customer Support ticket dumps in Zendesk JSON.*
>
> *Notice our ingestion execution on screen. As an FDE, you never just 'load data'—you prove completeness.*
>
> *We land raw inputs bit-for-bit into an immutable Bronze Parquet layer, stamping every partition with SHA-256 checksums, batch IDs, and ingestion timestamps.*
>
> *Most importantly, we run an automated **Financial Control Total Proof**: the sum of order subtotals ($231,406.85) reconciles penny-for-penny with line-item sums, with an exact delta of zero dollars. Zero rows leaked, zero financial drift."*

---

### [1:40 – 2:40] Scene 3: Data Profiling & The Core FDE Judgement Call

#### 🖥️ What to Show on Screen:
1. In terminal, run:
   ```bash
   python -c "from src.validate.validator import DataValidator; DataValidator().validate_and_calibrate()"
   ```
2. Point out the output:
   - `POS Clock Drift instances detected & calibrated: 914`
   - `Missing KDS bump bars defensibly imputed: 239`
   - `Critical anomalies quarantined: 12 (Logged to data/quarantine/quarantine_audit.parquet)`
3. Briefly show the code in `src/validate/validator.py` around line 140–165.

#### 🎙️ Spoken Narration:
> *"Now let's examine data validation and the single most important FDE judgement call I made.*
>
> *When profiling client data, we found 5 real-world anomalies. The most dangerous was **POS Hardware Clock Drift**: 914 orders across merchant Android tablets had clocks lagging true cellular UTC by up to 5 minutes, making it appear that tickets were printed before the customer even ordered!*
>
> *A naive data engineer would look at these negative durations and simply execute `df.dropna()` or `df = df[dwell >= 0]`.*
>
> *Why is that fatal for the business? Dropping those 914 rows would have silently erased **15.2% of all orders** and over **$35,000 in GMV**, clustered disproportionately in the highest-volume Downtown district. It hides the merchant bottleneck and blinds executive leadership.*
>
> *Instead, I applied **Defensible Temporal Calibration**: we anchor to physical timestamps (order placement and courier pickup), calibrate ticket print time to order plus 15 seconds, and preserve the full financial ledger with explicit audit flags.*
>
> *Meanwhile, truly irrecoverable corruptions—just 12 rows—were routed to a Dead-Letter Queue in `quarantine_audit.parquet` protected by an automated circuit breaker."*

---

### [2:40 – 3:35] Scene 4: Workflow State Machine & The Delay Friction Nexus

#### 🖥️ What to Show on Screen:
1. Display the workflow state diagram: `docs/workflow_fsm.png`.
2. In terminal, run:
   ```bash
   python -c "from src.model.state_machine import WorkflowStateMachine; WorkflowStateMachine().build_fact_order_lifecycle()"
   ```
3. Highlight the primary bottleneck output:
   - `RIDER_WAIT_AT_STORE: 5,285 orders`
   - `KITCHEN_PREP_OVERRUN: 337 orders`

#### 🎙️ Spoken Narration:
> *"Next, we reconstructed the business workflow as an Event State Machine, moving from Submitted to Confirmed, Prep Started, Food Ready, Rider Assigned, Arrived at Store, Picked Up, and Delivered.*
>
> *This allowed us to decompose total delivery time into 5 mathematically discrete stages:*
> - *Stage 1, Merchant confirmation lag, was only 1.1 minutes.*
> - *Stage 2, Kitchen prep overrun during peak hours, averaged 11.1 minutes.*
> - *Stage 3, Rider transit to store, was fast and dependable at 8.2 minutes.*
> - *Stage 5, Last-mile delivery, averaged 12.4 minutes.*
>
> *Now look at **Stage 4—The Store Synchronization Friction Nexus**.*
>
> *Because FlashEats dispatches couriers immediately upon order confirmation, couriers reach the store in 8 minutes, but kitchen prep takes 24 minutes. **Couriers spend an average of 15.8 minutes waiting idly outside restaurants**.*
>
> *Here is the diagnostic breakthrough: **Courier shortages were an illusion.** 52.8% of excess delay occurs because couriers are trapped waiting for unfinished food. Hiring more couriers would simply pay more drivers to sit on restaurant curbs!"*

---

### [3:35 – 4:25] Scene 5: Gold Marts & Counterfactual Operational Interventions

#### 🖥️ What to Show on Screen:
1. In terminal, execute the end-to-end dependable pipeline:
   ```bash
   python run_pipeline.py
   ```
2. Highlight the ASCII executive table rendered in the terminal:
   - Baseline P90: `54.43 min` &rarr; Staged Dispatch P90: `33.60 min`
   - SLA Breach: `56.43%` &rarr; `6.63%`
   - Rider Wait: `15.84 min` &rarr; `3.25 min`
   - Effective Fleet Gain: `+21.4%`
   - Refunds: `$36,081` &rarr; `$20,927` (or `$10,463` combined)
3. Open `run_manifest.json` to show the execution duration (~1.2s) and idempotency status.

#### 🎙️ Spoken Narration:
> *"Now we transition from diagnostic analytics to kinetic business decisions. We built counterfactual simulation models in our Gold Marts to evaluate operational interventions.*
>
> *Look at the table on screen:*
> - *Under **Baseline Immediate Dispatch**, our P90 OTD is 54.4 minutes, SLA breach is 56.4%, and refunds cost $36,081 daily.*
> - *In **Intervention 1: Staged Offset Dispatch**, we change the dispatch trigger logic. Instead of pinging a driver immediately, we offset dispatch by the estimated kitchen prep minus courier travel time. The courier arrives just-in-time—2 minutes before food packaging.*
>
> *The result is transformative:*
> - *Average rider store wait drops from **15.8 minutes down to 3.3 minutes**.*
> - *P90 delivery time plummets from **54.4 minutes to 33.6 minutes**, safely bringing FlashEats inside its 35-minute contractual SLA.*
> - *SLA breach rate falls from **56.4% to just 6.6%**.*
> - *And most importantly, this unlocks **+21.4% effective delivery fleet capacity**—equivalent to hiring 75 full-time couriers—**at zero recruitment cost**."*

---

### [4:25 – 5:00] Scene 6: Conclusion & Executive Summary

#### 🖥️ What to Show on Screen:
1. Show Section 7 (KUAL Framework) in `docs/evidence_table.md` or Page 2 of `24BCS10277_Harshit_Tiwari.pdf`.
2. Display the GitHub repository link: `https://github.com/X-DIABLO-X/FDE-2-Assignement`.

#### 🎙️ Spoken Narration:
> *"To conclude, let's summarize our findings using the FDE Epistemological Framework:*
> - ***Facts:** 52.8% of delivery delay was courier kitchen idle time, not road traffic or driver scarcity.*
> - ***Assumptions:** Calibrating POS clock drift preserved $35,000 in GMV without distorting prep metrics.*
> - ***Unknowns:** In-kitchen station bottlenecks and elevator transit times remain unobserved by mobile GPS.*
> - ***Limitations:** Production deployment requires migrating this batch model to sub-second streaming dispatch.*
>
> *The entire pipeline is open-source, fully tested with pytest, idempotent, and produces a complete run manifest in 1.2 seconds.*
>
> *The final 2-page executive PDF, `24BCS10277_Harshit_Tiwari.pdf`, contains all empirical evidence tables and is submitted on the portal.*
>
> *Thank you! I am ready for your questions."*

---

## 💡 Practical Recording Tips for the Candidate

1. **Terminal Setup:**
   - Font size: `16pt` or `18pt` (easy to read on 1080p).
   - Window size: Half screen or 75% width.
2. **Commands to have ready in your terminal history (Up Arrow):**
   ```bash
   # Quick pipeline run
   python run_pipeline.py
   
   # Tests verification
   python -m pytest tests/
   ```
3. **Pacing:** Keep a brisk, steady pace. Don't pause between terminal output and speaking—speak *while* the output renders.
4. **Energy:** Emphasize the monetary and operational impact ($36k saved, +21.4% fleet capacity unlocked). That is what executive leaders and grading evaluators look for in a Forward Deployed Engineer!
