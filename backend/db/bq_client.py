"""BigQuery client with graceful fallback detection."""
import logging
from typing import Optional
from backend.config import settings

logger = logging.getLogger(__name__)


class BigQueryClient:
    """Wraps google-cloud-bigquery; sets available=False when credentials missing."""

    def __init__(self):
        self.project = settings.google_cloud_project
        self.dataset = settings.bigquery_dataset
        self.available = False
        self._client = None

        if not self.project or self.project in ("placeholder-project", "your-project-id", ""):
            logger.info("BigQuery: project placeholder — using SQLite fallback")
            return

        try:
            from google.cloud import bigquery
            self._client = bigquery.Client(project=self.project)
            # Cheap validation: list datasets (fails fast on auth errors)
            list(self._client.list_datasets(max_results=1))
            self.available = True
            logger.info(f"BigQuery connected: {self.project}.{self.dataset}")
        except Exception as exc:
            logger.warning(f"BigQuery unavailable ({exc}), using SQLite fallback")

    def query(self, sql: str, params: Optional[dict] = None) -> list[dict]:
        """Execute a parameterized BigQuery query and return rows as dicts."""
        if not self.available:
            raise RuntimeError("BigQuery not configured")
        try:
            from google.cloud import bigquery as bq
            job_config = bq.QueryJobConfig()
            if params:
                job_config.query_parameters = [
                    bq.ScalarQueryParameter(k, "STRING", v) for k, v in params.items()
                ]
            result = self._client.query(sql, job_config=job_config).result()
            return [dict(row) for row in result]
        except Exception as exc:
            logger.error(f"BigQuery query error: {exc}")
            raise

    def insert_rows(self, table: str, rows: list[dict]) -> None:
        """Streaming insert into a BigQuery table."""
        if not self.available:
            raise RuntimeError("BigQuery not configured")
        if not rows:
            return
        full_table = f"{self.project}.{self.dataset}.{table}"
        errors = self._client.insert_rows_json(full_table, rows)
        if errors:
            logger.error(f"BigQuery insert errors on {table}: {errors}")
            raise RuntimeError(f"Insert failed: {errors}")

    def table_exists(self, table: str) -> bool:
        """Return True if the table exists in the configured dataset."""
        if not self.available:
            return False
        try:
            from google.cloud import bigquery as bq
            ref = self._client.dataset(self.dataset).table(table)
            self._client.get_table(ref)
            return True
        except Exception:
            return False


_instance: Optional[BigQueryClient] = None


def get_bq_client() -> BigQueryClient:
    global _instance
    if _instance is None:
        _instance = BigQueryClient()
    return _instance
