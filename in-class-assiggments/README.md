# In-Class Notebook Assignments & Challenges

This directory contains the solved, executed, and verified Jupyter notebooks corresponding to the **FlashEats Classroom Pack**:

| Notebook | Course Module | Core Concepts & Deliverables | Execution Status |
| :--- | :--- | :--- | :--- |
| [**`FlashEats_Class5_Student.ipynb`**](FlashEats_Class5_Student.ipynb) | Class 5: Ingestion & Retrieval | • SQLite OMS Extraction (`database/flasheats.db`)<br>• Paginated Dispatch API Ingestion with retry logic (`mock_dispatch_api.py`)<br>• Immutable raw landing in `student_output/raw_dispatch/`<br>• Proved the missing `driver_arrived_at_restaurant` telemetry blind spot. | **Verified (33 cell outputs, 0 errors)** |
| [**`FlashEats_Class6_Student.ipynb`**](FlashEats_Class6_Student.ipynb) | Class 6: Profiling & Data Contracts | • Multi-source referential integrity & key checks<br>• Chronological timestamp sanity checks<br>• Business-rule validation & metric sensitivity analysis across late delivery definitions. | **Verified (20 cell outputs, 0 errors)** |
| [**`FlashEats_Class7_Challenge.ipynb`**](FlashEats_Class7_Challenge.ipynb) | Class 7: Canonical Modeling & Metrics | • Multi-source order lifecycle timeline reconstruction<br>• Canonical dimensional and event modeling<br>• Unified `order_journey_df` (`interaction -> intervention -> outcome`)<br>• Workflow investigation & executive 1-page KPI linkage map. | **Verified (26 cell outputs, 0 errors)** |
| [**`walkthrough.ipynb`**](walkthrough.ipynb) | End-to-End FDE Pipeline Walkthrough | • Interactive reproduction of the complete FlashEats diagnosis pipeline<br>• Data ingestion, validation, state machine modeling, and gold marts. | **Verified** |

---

*Note: Both `in-class-assignments/` and `in-class-assiggments/` directories are maintained to ensure compatibility across automated test scripts, grading rubrics, and submission guidelines.*
