"""
connectors/bank_connector.py
------------------------------
Connector for bank transaction data (e.g. a bank statement feed or
Open Banking API in production). Reads mock JSON here.
"""

import json
import os
from typing import List

from connectors.base_connector import BaseConnector
from core.models import UnifiedTransaction

DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "mock_data", "bank_transactions.json"
)


class BankConnector(BaseConnector):
    source_name = "BANK"

    def __init__(self, data_path: str = DATA_PATH):
        self.data_path = data_path

    def fetch(self) -> List[UnifiedTransaction]:
        with open(self.data_path, "r") as f:
            txns = json.load(f)

        return [
            UnifiedTransaction(
                source_system=self.source_name,
                source_id=txn["txn_id"],
                amount=float(txn["amount"]),
                currency=txn["currency"],
                date=txn["date"],
                counterparty=txn["counterparty"],
                transaction_type=txn["type"],
                raw_data=txn,
            )
            for txn in txns
        ]
