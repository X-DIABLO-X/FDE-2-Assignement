# In-Class Notebook Assignments & Classroom Pack

This directory consolidates all student-facing materials, challenge notebooks, classroom manifests, and solution reproduction scripts for the **FlashEats Classroom Pack** (Classes 5, 6, and 7):

---

## 1. Solved & Executed Notebooks

| Notebook | Course Module | Core Concepts & Deliverables | Execution Status |
| :--- | :--- | :--- | :--- |
| [**`FlashEats_Class5_Student.ipynb`**](FlashEats_Class5_Student.ipynb) | Class 5: Ingestion & Retrieval | • SQLite OMS Extraction (`database/flasheats.db`)<br>• Paginated Dispatch API Ingestion with retry logic (`mock_dispatch_api.py`)<br>• Immutable raw landing in `student_output/raw_dispatch/`<br>• Proved the missing `driver_arrived_at_restaurant` telemetry blind spot. | **Verified (33 cell outputs, 0 errors)** |
| [**`FlashEats_Class6_Student.ipynb`**](FlashEats_Class6_Student.ipynb) | Class 6: Profiling & Data Contracts | • Multi-source referential integrity & key checks<br>• Chronological timestamp sanity checks<br>• Business-rule validation & metric sensitivity analysis across late delivery definitions. | **Verified (20 cell outputs, 0 errors)** |
| [**`FlashEats_Class7_Challenge.ipynb`**](FlashEats_Class7_Challenge.ipynb) | Class 7: Canonical Modeling & Metrics | • Multi-source order lifecycle timeline reconstruction<br>• Canonical dimensional and event modeling<br>• Unified `order_journey_df` (`interaction -> intervention -> outcome`)<br>• Workflow investigation & executive 1-page KPI linkage map. | **Verified (26 cell outputs, 0 errors)** |
| [**`walkthrough.ipynb`**](walkthrough.ipynb) | End-to-End FDE Pipeline Walkthrough | • Interactive reproduction of the complete FlashEats diagnosis pipeline<br>• Data ingestion, validation, state machine modeling, and gold marts. | **Verified** |

---

## 2. Classroom Documentation & Briefs

- [**`README_STUDENTS.md`**](README_STUDENTS.md): Original student overview and setup instructions from the classroom pack.
- [**`README_CLASS6.md`**](README_CLASS6.md): Class 6 briefing on data quality, contracts, and validation rules.
- [**`README_CLASS7.md`**](README_CLASS7.md): Class 7 briefing on lifecycle modeling, metrics, and KPI linkage.

---

## 3. Classroom Manifests

- [**`manifest.json`**](manifest.json): Initial classroom pack dataset checksums and inventory.
- [**`manifest_class6.json`**](manifest_class6.json): Class 6 schema and table file hashes.
- [**`manifest_class7.json`**](manifest_class7.json): Class 7 challenge data specifications.

---

## 4. Automation & Verification Scripts

- [**`solve_class5.py`**](solve_class5.py): Automated solver and headless executor for Class 5 notebook.
- [**`solve_class6.py`**](solve_class6.py): Automated solver and headless executor for Class 6 notebook.
- [**`solve_class7.py`**](solve_class7.py): Automated solver and headless executor for Class 7 notebook.
- [**`test_solve_all.py`**](test_solve_all.py): Cross-dataset verification script testing calculations across all classroom datasets.
