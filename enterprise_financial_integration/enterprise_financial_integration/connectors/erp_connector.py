"""
connectors/erp_connector.py
-----------------------------
Connector for the ERP system's invoice data.

In production this would call the ERP's REST/SOAP API or read from
its database. Here it reads a mock JSON file so the project runs
without external dependencies, but the fetch() contract is identical
to a real integration.
"""

import json
import os
from typing import List

from connectors.base_connector import BaseConnector
from core.models import UnifiedTransaction

DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "mock_data", "erp_invoices.json"
)


class ERPConnector(BaseConnector):
    source_name = "ERP"

    def __init__(self, data_path: str = DATA_PATH):
        self.data_path = data_path

    def fetch(self) -> List[UnifiedTransaction]:
        with open(self.data_path, "r") as f:
            invoices = json.load(f)

        return [
            UnifiedTransaction(
                source_system=self.source_name,
                source_id=inv["invoice_id"],
                amount=float(inv["amount"]),
                currency=inv["currency"],
                date=inv["date"],
                counterparty=inv["counterparty"],
                transaction_type="invoice",
                raw_data=inv,
            )
            for inv in invoices
        ]
