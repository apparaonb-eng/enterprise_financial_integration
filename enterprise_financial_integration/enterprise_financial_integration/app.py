"""
app.py
------
Flask application exposing the Enterprise Financial Integration hub:
  - GET  /                          dashboard UI
  - POST /api/sync                  pull latest data from all connectors
  - GET  /api/transactions          list unified transactions (optional ?source=)
  - POST /api/reconcile             run reconciliation across systems
  - GET  /api/health                health check

Run with:
    python app.py
Then open http://127.0.0.1:5000
"""

from flask import Flask, render_template, jsonify, request

from core.database import init_db, get_session, reset_db
from core.models import TransactionRecord
from core.sync_engine import SyncEngine
from core.reconciliation import ReconciliationEngine
from connectors.erp_connector import ERPConnector
from connectors.bank_connector import BankConnector
from connectors.ledger_connector import LedgerConnector

app = Flask(__name__)

# Register all active connectors here. To add a new system, write a
# new Connector class (see connectors/base_connector.py) and add an
# instance to this list — nothing else needs to change.
CONNECTORS = [ERPConnector(), BankConnector(), LedgerConnector()]

sync_engine = SyncEngine(CONNECTORS)
reconciliation_engine = ReconciliationEngine(primary_source="BANK", reference_sources=("ERP", "LEDGER"))

_last_sync_summary = None
_last_reconciliation_report = None


@app.route("/")
def dashboard():
    session = get_session()
    try:
        total = session.query(TransactionRecord).count()
        by_source = {}
        for source in ("ERP", "BANK", "LEDGER"):
            by_source[source] = session.query(TransactionRecord).filter_by(source_system=source).count()
        by_status = {}
        for status in ("matched", "unmatched", "discrepancy"):
            by_status[status] = session.query(TransactionRecord).filter_by(status=status).count()
    finally:
        session.close()

    return render_template(
        "dashboard.html",
        total=total,
        by_source=by_source,
        by_status=by_status,
        last_sync=_last_sync_summary,
        last_reconciliation=_last_reconciliation_report.summary() if _last_reconciliation_report else None,
    )


@app.route("/api/sync", methods=["POST"])
def api_sync():
    global _last_sync_summary
    _last_sync_summary = sync_engine.run_sync()
    return jsonify(_last_sync_summary), 200


@app.route("/api/transactions", methods=["GET"])
def api_transactions():
    source = request.args.get("source")
    status = request.args.get("status")

    session = get_session()
    try:
        query = session.query(TransactionRecord)
        if source:
            query = query.filter_by(source_system=source.upper())
        if status:
            query = query.filter_by(status=status.lower())
        records = query.order_by(TransactionRecord.date.desc()).all()
        return jsonify([r.to_dict() for r in records]), 200
    finally:
        session.close()


@app.route("/api/reconcile", methods=["POST"])
def api_reconcile():
    global _last_reconciliation_report
    _last_reconciliation_report = reconciliation_engine.run()
    return jsonify(_last_reconciliation_report.to_dict()), 200


@app.route("/api/reconciliation/report", methods=["GET"])
def api_reconciliation_report():
    if _last_reconciliation_report is None:
        return jsonify({"message": "No reconciliation has been run yet."}), 404
    return jsonify(_last_reconciliation_report.to_dict()), 200


@app.route("/api/reset", methods=["POST"])
def api_reset():
    """Convenience endpoint to wipe the DB and start fresh (demo/testing only)."""
    global _last_sync_summary, _last_reconciliation_report
    reset_db()
    _last_sync_summary = None
    _last_reconciliation_report = None
    return jsonify({"message": "Database reset."}), 200


@app.route("/api/health", methods=["GET"])
def api_health():
    return jsonify({
        "status": "ok",
        "connectors": [c.source_name for c in CONNECTORS],
    }), 200


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
