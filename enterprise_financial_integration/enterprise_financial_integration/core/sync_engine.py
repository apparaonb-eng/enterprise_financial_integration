"""
core/sync_engine.py
---------------------
Orchestrates the integration: pulls data from every registered
connector, normalizes it (already done by the connector), and
upserts it into the central database. This is the piece that would
run on a schedule (cron / Airflow / Celery beat) in a real deployment.
"""

import datetime
import json
from typing import List

from core.database import get_session
from core.models import TransactionRecord
from connectors.base_connector import BaseConnector


class SyncEngine:
    def __init__(self, connectors: List[BaseConnector]):
        self.connectors = connectors

    def run_sync(self) -> dict:
        """Fetch from every connector and upsert into the DB.
        Returns a summary dict of how many records came from each source."""
        session = get_session()
        summary = {}

        try:
            for connector in self.connectors:
                records = connector.fetch()
                count = 0
                for rec in records:
                    existing = (
                        session.query(TransactionRecord)
                        .filter_by(source_system=rec.source_system, source_id=rec.source_id)
                        .first()
                    )
                    date_obj = datetime.date.fromisoformat(rec.date)

                    if existing:
                        # Update in place (idempotent sync)
                        existing.amount = rec.amount
                        existing.currency = rec.currency
                        existing.date = date_obj
                        existing.counterparty = rec.counterparty
                        existing.transaction_type = rec.transaction_type
                        existing.raw_data = json.dumps(rec.raw_data)
                    else:
                        session.add(TransactionRecord(
                            source_system=rec.source_system,
                            source_id=rec.source_id,
                            amount=rec.amount,
                            currency=rec.currency,
                            date=date_obj,
                            counterparty=rec.counterparty,
                            transaction_type=rec.transaction_type,
                            status="unmatched",
                            raw_data=json.dumps(rec.raw_data),
                        ))
                    count += 1
                summary[connector.source_name] = count

            session.commit()
            summary["synced_at"] = datetime.datetime.utcnow().isoformat() + "Z"
            return summary
        finally:
            session.close()
