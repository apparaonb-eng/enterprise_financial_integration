"""
connectors/ledger_connector.py
--------------------------------
Connector for the general ledger / accounting system. Reads mock
JSON here; in production this could hit NetSuite, SAP, QuickBooks,
Xero, or an internal ledger database.
"""

import json
import os
from typing import List

from connectors.base_connector import BaseConnector
from core.models import UnifiedTransaction

DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "mock_data", "ledger_entries.json"
)


class LedgerConnector(BaseConnector):
    source_name = "LEDGER"

    def __init__(self, data_path: str = DATA_PATH):
        self.data_path = data_path

    def fetch(self) -> List[UnifiedTransaction]:
        with open(self.data_path, "r") as f:
            entries = json.load(f)

        return [
            UnifiedTransaction(
                source_system=self.source_name,
                source_id=entry["entry_id"],
                amount=float(entry["amount"]),
                currency=entry["currency"],
                date=entry["date"],
                counterparty=entry["counterparty"],
                transaction_type=entry["account"],
                raw_data=entry,
            )
            for entry in entries
        ]
