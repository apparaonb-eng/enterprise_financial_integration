"""
core/reconciliation.py
------------------------
Matches transactions across source systems (typically: does this
BANK debit correspond to an ERP invoice / ledger entry?). Flags
unmatched or mismatched records for human review — the classic
"reconciliation" problem in enterprise finance integration.

Matching strategy (simple, explainable — swap in fuzzy matching /
ML later if needed):
  - same counterparty (case-insensitive)
  - same currency
  - amount within AMOUNT_TOLERANCE
  - date within DATE_TOLERANCE_DAYS
"""

import datetime
from dataclasses import dataclass, field
from typing import List

from core.database import get_session
from core.models import TransactionRecord

AMOUNT_TOLERANCE = 10.00     # allow small differences (e.g. bank fees)
DATE_TOLERANCE_DAYS = 3


@dataclass
class ReconciliationReport:
    matched: List[dict] = field(default_factory=list)
    unmatched: List[dict] = field(default_factory=list)
    discrepancies: List[dict] = field(default_factory=list)
    run_at: str = ""

    def summary(self):
        return {
            "matched_count": len(self.matched),
            "unmatched_count": len(self.unmatched),
            "discrepancy_count": len(self.discrepancies),
            "run_at": self.run_at,
        }

    def to_dict(self):
        return {
            **self.summary(),
            "matched": self.matched,
            "unmatched": self.unmatched,
            "discrepancies": self.discrepancies,
        }


class ReconciliationEngine:
    def __init__(self, primary_source="BANK", reference_sources=("ERP", "LEDGER")):
        self.primary_source = primary_source
        self.reference_sources = reference_sources

    def _is_close(self, a: TransactionRecord, b: TransactionRecord) -> bool:
        if a.currency != b.currency:
            return False
        if a.counterparty.strip().lower() != b.counterparty.strip().lower():
            return False
        if abs(a.date - b.date).days > DATE_TOLERANCE_DAYS:
            return False
        return True

    def run(self) -> ReconciliationReport:
        session = get_session()
        report = ReconciliationReport(run_at=datetime.datetime.utcnow().isoformat() + "Z")

        try:
            primary_records = (
                session.query(TransactionRecord)
                .filter_by(source_system=self.primary_source)
                .all()
            )
            reference_records = (
                session.query(TransactionRecord)
                .filter(TransactionRecord.source_system.in_(self.reference_sources))
                .all()
            )

            for primary in primary_records:
                best_match = None
                for ref in reference_records:
                    if ref.status == "matched":
                        continue
                    if self._is_close(primary, ref):
                        best_match = ref
                        break

                if best_match is None:
                    primary.status = "unmatched"
                    report.unmatched.append(primary.to_dict())
                    continue

                amount_diff = round(abs(primary.amount - best_match.amount), 2)
                match_key = f"{best_match.source_system}:{best_match.source_id}"

                if amount_diff <= AMOUNT_TOLERANCE:
                    primary.status = "matched"
                    primary.matched_with = match_key
                    best_match.status = "matched"
                    best_match.matched_with = f"{primary.source_system}:{primary.source_id}"
                    report.matched.append({
                        "bank": primary.to_dict(),
                        "reference": best_match.to_dict(),
                        "amount_diff": amount_diff,
                    })
                else:
                    primary.status = "discrepancy"
                    primary.matched_with = match_key
                    report.discrepancies.append({
                        "bank": primary.to_dict(),
                        "reference": best_match.to_dict(),
                        "amount_diff": amount_diff,
                    })

            session.commit()
            return report
        finally:
            session.close()
