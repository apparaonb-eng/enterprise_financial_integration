"""
connectors/base_connector.py
-----------------------------
Defines the contract every connector must follow. To integrate a NEW
enterprise system (e.g. Stripe, SAP, NetSuite, QuickBooks, a bank's
real API), you implement a new subclass of BaseConnector with a
fetch() method that returns a list of UnifiedTransaction objects.
Nothing else in the platform needs to change.
"""

from abc import ABC, abstractmethod
from typing import List

from core.models import UnifiedTransaction


class BaseConnector(ABC):
    """All connectors must implement `source_name` and `fetch()`."""

    source_name: str = "UNKNOWN"

    @abstractmethod
    def fetch(self) -> List[UnifiedTransaction]:
        """
        Pull raw data from the source system (file, API, DB, etc.)
        and return it normalized as a list of UnifiedTransaction.
        """
        raise NotImplementedError
