import logging
from typing import Optional
logger = logging.getLogger(__name__)

class BigQueryClient:
    """BigQuery client with SQLite fallback for local development."""

    def __init__(self, project: str, dataset: str):
        self.project = project
        self.dataset = dataset
        self._use_stub = False
        try:
            from google.cloud import bigquery
            self.client = bigquery.Client(project=project)
            logger.info(f"BigQuery connected: {project}.{dataset}")
        except Exception as e:
            logger.warning(f"BigQuery unavailable ({e}), using SQLite stub")
            self._use_stub = True
            self._init_sqlite_stub()

    def _init_sqlite_stub(self):
        import sqlite3, os
        os.makedirs("backend/db/local", exist_ok=True)
        self.sqlite_conn = sqlite3.connect("backend/db/local/aitm_stub.db", check_same_thread=False)
        logger.info("SQLite stub initialized at backend/db/local/aitm_stub.db")

    def execute_query(self, sql: str) -> list:
        if self._use_stub:
            try:
                cursor = self.sqlite_conn.cursor()
                cursor.execute(sql)
                cols = [d[0] for d in cursor.description] if cursor.description else []
                return [dict(zip(cols, row)) for row in cursor.fetchall()]
            except Exception as e:
                logger.error(f"SQLite query error: {e}")
                return []
        try:
            result = self.client.query(sql).result()
            return [dict(row) for row in result]
        except Exception as e:
            logger.error(f"BigQuery error: {e}")
            return []

    def insert_rows(self, table: str, rows: list) -> bool:
        if not rows:
            return True
        if self._use_stub:
            logger.info(f"[STUB] Would insert {len(rows)} rows into {table}")
            return True
        try:
            full_table = f"{self.project}.{self.dataset}.{table}"
            errors = self.client.insert_rows_json(full_table, rows)
            if errors:
                logger.error(f"BQ insert errors: {errors}")
                return False
            return True
        except Exception as e:
            logger.error(f"BigQuery insert error: {e}")
            return False
