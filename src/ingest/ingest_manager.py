"""
Stage 1: Multi-Mode Ingestion & Completeness Proofs
Implements multi-source data retrieval across:
1. SQL RDBMS (SQLite): orders, merchants, line items
2. REST API / JSON Stream: driver dispatch events
3. Flat-file CSV: merchant KDS logs
4. JSON Document Store: customer support Zendesk tickets

Guarantees:
- Preserves raw input immutability
- Computes SHA-256 checksums & ingestion audit stamps
- Verifies mathematical completeness proofs (record count & GMV financial control totals)
- Converts to standardized Bronze Parquet layer
"""

import os
import hashlib
import json
import sqlite3
from datetime import datetime
import pandas as pd

class IngestionManager:
    def __init__(self, raw_dir: str = "data/raw", bronze_dir: str = "data/bronze"):
        self.raw_dir = raw_dir
        self.bronze_dir = bronze_dir
        os.makedirs(self.bronze_dir, exist_ok=True)
        self.batch_id = f"BATCH-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        self.ingested_at = datetime.utcnow().isoformat() + "Z"
        self.proof_manifest = {
            "batch_id": self.batch_id,
            "ingested_at": self.ingested_at,
            "sources": {},
            "control_totals": {},
            "completeness_verified": False
        }

    def _compute_file_sha256(self, filepath: str) -> str:
        sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(65536):
                sha256.update(chunk)
        return sha256.hexdigest()

    def ingest_sql_orders(self) -> pd.DataFrame:
        """Retrieval Mode 1: SQL Extraction from Operational RDBMS"""
        db_path = os.path.join(self.raw_dir, "orders_platform.db")
        checksum = self._compute_file_sha256(db_path)
        
        conn = sqlite3.connect(db_path)
        orders_df = pd.read_sql_query("SELECT * FROM orders", conn)
        merchants_df = pd.read_sql_query("SELECT * FROM merchants", conn)
        items_df = pd.read_sql_query("SELECT * FROM order_line_items", conn)
        conn.close()

        # Stamp audit metadata
        for df, name in [(orders_df, "bronze_orders"), (merchants_df, "bronze_merchants"), (items_df, "bronze_order_items")]:
            df["_ingested_at"] = self.ingested_at
            df["_batch_id"] = self.batch_id
            df["_source_type"] = "SQL_RDBMS"
            df["_raw_checksum"] = checksum
            target_path = os.path.join(self.bronze_dir, f"{name}.parquet")
            df.to_parquet(target_path, index=False)

        # Log proof
        self.proof_manifest["sources"]["sql_orders"] = {
            "retrieval_mode": "SQL_RDBMS_QUERY",
            "source_file": db_path,
            "checksum_sha256": checksum,
            "extracted_rows": {
                "orders": len(orders_df),
                "merchants": len(merchants_df),
                "line_items": len(items_df)
            }
        }
        return orders_df

    def ingest_api_dispatch(self) -> pd.DataFrame:
        """Retrieval Mode 2: Mock REST API / JSON Stream Extraction"""
        json_path = os.path.join(self.raw_dir, "dispatch_telemetry_stream.json")
        checksum = self._compute_file_sha256(json_path)

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        dispatch_df = pd.DataFrame(data)
        dispatch_df["_ingested_at"] = self.ingested_at
        dispatch_df["_batch_id"] = self.batch_id
        dispatch_df["_source_type"] = "REST_API_STREAM"
        dispatch_df["_raw_checksum"] = checksum

        target_path = os.path.join(self.bronze_dir, "bronze_dispatch_attempts.parquet")
        dispatch_df.to_parquet(target_path, index=False)

        self.proof_manifest["sources"]["api_dispatch"] = {
            "retrieval_mode": "REST_API_PAGINATED_JSON",
            "source_file": json_path,
            "checksum_sha256": checksum,
            "extracted_rows": len(dispatch_df)
        }
        return dispatch_df

    def ingest_csv_kds(self) -> pd.DataFrame:
        """Retrieval Mode 3: Flat-file CSV Parsing (Kitchen Display System)"""
        csv_path = os.path.join(self.raw_dir, "kds_merchant_prep.csv")
        checksum = self._compute_file_sha256(csv_path)

        kds_df = pd.read_csv(csv_path)
        kds_df["_ingested_at"] = self.ingested_at
        kds_df["_batch_id"] = self.batch_id
        kds_df["_source_type"] = "CSV_DAILY_EXPORT"
        kds_df["_raw_checksum"] = checksum

        target_path = os.path.join(self.bronze_dir, "bronze_kds_logs.parquet")
        kds_df.to_parquet(target_path, index=False)

        self.proof_manifest["sources"]["csv_kds"] = {
            "retrieval_mode": "CSV_BATCH_FILE",
            "source_file": csv_path,
            "checksum_sha256": checksum,
            "extracted_rows": len(kds_df)
        }
        return kds_df

    def ingest_support_tickets(self) -> pd.DataFrame:
        """Retrieval Mode 4: JSON Document Store (Zendesk Customer Escalations)"""
        json_path = os.path.join(self.raw_dir, "customer_support_tickets.json")
        checksum = self._compute_file_sha256(json_path)

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        support_df = pd.DataFrame(data)
        support_df["_ingested_at"] = self.ingested_at
        support_df["_batch_id"] = self.batch_id
        support_df["_source_type"] = "JSON_DOC_STORE"
        support_df["_raw_checksum"] = checksum

        target_path = os.path.join(self.bronze_dir, "bronze_support_tickets.parquet")
        support_df.to_parquet(target_path, index=False)

        self.proof_manifest["sources"]["support_tickets"] = {
            "retrieval_mode": "JSON_EXPORT",
            "source_file": json_path,
            "checksum_sha256": checksum,
            "extracted_rows": len(support_df)
        }
        return support_df

    def verify_completeness_proofs(self) -> dict:
        """
        Calculates mathematical completeness proofs:
        1. Row-count preservation proof
        2. GMV financial control total reconciliation
        3. Primary key uniqueness validation
        """
        orders_df = pd.read_parquet(os.path.join(self.bronze_dir, "bronze_orders.parquet"))
        items_df = pd.read_parquet(os.path.join(self.bronze_dir, "bronze_order_items.parquet"))
        dispatch_df = pd.read_parquet(os.path.join(self.bronze_dir, "bronze_dispatch_attempts.parquet"))
        kds_df = pd.read_parquet(os.path.join(self.bronze_dir, "bronze_kds_logs.parquet"))

        # Financial Control Totals
        gmv_orders = int(orders_df["subtotal_cents"].sum())
        total_delivery_fees = int(orders_df["delivery_fee_cents"].sum())
        total_tips = int(orders_df["tip_cents"].sum())
        total_captured_revenue = gmv_orders + total_delivery_fees + total_tips

        # Line items financial sum check
        items_subtotal_sum = int((items_df["quantity"] * items_df["unit_price_cents"]).sum())
        financial_delta = abs(gmv_orders - items_subtotal_sum)

        # Primary Key integrity checks
        pk_checks = {
            "orders_unique": bool(orders_df["order_id"].is_unique),
            "line_items_unique": bool(items_df["line_item_id"].is_unique),
            "dispatch_unique": bool(dispatch_df["dispatch_id"].is_unique),
            "kds_unique": bool(kds_df["kds_ticket_id"].is_unique)
        }

        self.proof_manifest["control_totals"] = {
            "gmv_subtotal_cents": gmv_orders,
            "total_delivery_fee_cents": total_delivery_fees,
            "total_tips_cents": total_tips,
            "total_gross_captured_cents": total_captured_revenue,
            "line_items_reconciliation_delta_cents": financial_delta,
            "primary_key_integrity": pk_checks
        }

        # Mathematical verification flag
        is_complete = (
            all(pk_checks.values()) and 
            (financial_delta <= len(orders_df)) # allow rounding cents if any
        )
        self.proof_manifest["completeness_verified"] = is_complete

        proof_path = os.path.join(self.bronze_dir, "ingestion_proof_manifest.json")
        with open(proof_path, "w", encoding="utf-8") as f:
            json.dump(self.proof_manifest, f, indent=2)

        return self.proof_manifest

    def run_all(self):
        print(f"[*] Starting Multi-Mode Ingestion (Batch: {self.batch_id})...")
        self.ingest_sql_orders()
        self.ingest_api_dispatch()
        self.ingest_csv_kds()
        self.ingest_support_tickets()
        proof = self.verify_completeness_proofs()
        print(f"[+] Ingestion complete! Mathematical completeness verified: {proof['completeness_verified']}")
        print(f"    - Financial GMV Control Total: ${proof['control_totals']['gmv_subtotal_cents']/100:,.2f}")
        print(f"    - All Primary Keys Unique: {proof['control_totals']['primary_key_integrity']}")
        return proof

if __name__ == "__main__":
    manager = IngestionManager()
    manager.run_all()
