"""
core/models.py
---------------
Defines the UNIFIED schema that every connector must normalize its
source-system data into, plus the SQLAlchemy ORM model used to
persist unified transactions in the central database.

This is the heart of an integration platform: no matter how many
different systems you plug in (ERP, bank, ledger, payment gateway,
CRM...), everything downstream (reconciliation, reporting, APIs)
only ever has to deal with ONE consistent shape of data.
"""

import datetime
import json
from dataclasses import dataclass, field, asdict
from typing import Optional

from sqlalchemy import Column, Integer, String, Float, Date, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


@dataclass
class UnifiedTransaction:
    """In-memory representation produced by connectors before persistence."""
    source_system: str          # e.g. "ERP", "BANK", "LEDGER"
    source_id: str              # the ID in the source system
    amount: float
    currency: str
    date: str                   # ISO format YYYY-MM-DD
    counterparty: str
    transaction_type: str = "unknown"
    status: str = "unmatched"   # unmatched | matched | discrepancy
    matched_with: Optional[str] = None   # composite key of matched record, if any
    raw_data: dict = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)


class TransactionRecord(Base):
    """SQLAlchemy ORM table storing all normalized transactions centrally."""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_system = Column(String(50), nullable=False)
    source_id = Column(String(100), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), nullable=False)
    date = Column(Date, nullable=False)
    counterparty = Column(String(200))
    transaction_type = Column(String(50))
    status = Column(String(20), default="unmatched")
    matched_with = Column(String(100), nullable=True)
    raw_data = Column(Text)  # JSON-serialized original payload

    def to_dict(self):
        return {
            "id": self.id,
            "source_system": self.source_system,
            "source_id": self.source_id,
            "amount": self.amount,
            "currency": self.currency,
            "date": self.date.isoformat() if isinstance(self.date, (datetime.date,)) else self.date,
            "counterparty": self.counterparty,
            "transaction_type": self.transaction_type,
            "status": self.status,
            "matched_with": self.matched_with,
            "raw_data": json.loads(self.raw_data) if self.raw_data else {},
        }
