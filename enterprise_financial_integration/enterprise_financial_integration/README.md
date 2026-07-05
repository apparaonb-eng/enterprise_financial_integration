# Enterprise Financial Integration Hub (Base Project)

A base project demonstrating the core pattern behind enterprise
financial integration platforms: connecting multiple disparate
financial systems (ERP, Bank, General Ledger), normalizing their
data into one **unified schema**, syncing it into a **central
database**, and running **cross-system reconciliation** — all
exposed through a REST API and a lightweight dashboard.

This mirrors what real integration platforms do (think: MuleSoft,
Boomi, or a custom middleware layer) just scoped down to something
you can run and understand in one sitting.

## Architecture

```
enterprise_financial_integration/
├── app.py                       # Flask app: API + dashboard
├── requirements.txt
├── connectors/                  # One connector per external system
│   ├── base_connector.py        # Abstract contract all connectors follow
│   ├── erp_connector.py         # Pulls & normalizes ERP invoices
│   ├── bank_connector.py        # Pulls & normalizes bank transactions
│   └── ledger_connector.py      # Pulls & normalizes GL entries
├── core/
│   ├── models.py                 # UnifiedTransaction schema + ORM model
│   ├── database.py               # SQLAlchemy engine/session (SQLite)
│   ├── sync_engine.py            # Orchestrates connector -> DB sync
│   └── reconciliation.py         # Cross-system transaction matching
├── mock_data/                   # Simulated source-system data (JSON)
│   ├── erp_invoices.json
│   ├── bank_transactions.json
│   └── ledger_entries.json
├── templates/
│   └── dashboard.html
└── static/
    └── style.css
```

### The Connector Pattern

Every external system is wrapped in a connector implementing:

```python
class BaseConnector(ABC):
    source_name: str
    def fetch(self) -> List[UnifiedTransaction]: ...
```

To integrate a **new** system (Stripe, SAP, NetSuite, a real bank
API, etc.), you only need to:
1. Create `connectors/my_system_connector.py` implementing `fetch()`.
2. Add an instance of it to `CONNECTORS` in `app.py`.

Nothing else in the platform — the database, sync engine,
reconciliation logic, or API — needs to change. That's the whole
point of the pattern: isolate system-specific quirks in the
connector layer, keep everything downstream generic.

### Sync Engine

`SyncEngine.run_sync()` calls `fetch()` on every registered connector
and upserts the results into the central `transactions` table
(idempotent — running it repeatedly won't create duplicates). In
production this would run on a schedule (cron, Celery beat, Airflow).

### Reconciliation Engine

`ReconciliationEngine.run()` treats bank transactions as the "source
of truth to explain" and tries to match each one against ERP
invoices / ledger entries using counterparty name, currency, date
proximity, and amount tolerance. Each bank transaction ends up
`matched`, `discrepancy` (found a likely match but amounts differ
beyond tolerance), or `unmatched`.

## Setup & Run

```bash
# 1. Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app (creates the SQLite DB automatically)
python app.py
```

Open **http://127.0.0.1:5000** — then click **"Sync All Systems"**
followed by **"Run Reconciliation"** to see the pipeline work
end-to-end against the bundled mock data.

## API Reference

| Method | Endpoint                     | Description                              |
|--------|-------------------------------|-------------------------------------------|
| POST   | `/api/sync`                   | Pull latest data from all connectors      |
| GET    | `/api/transactions`           | List transactions (`?source=`, `?status=`)|
| POST   | `/api/reconcile`              | Run cross-system reconciliation           |
| GET    | `/api/reconciliation/report`  | Get the last reconciliation report        |
| POST   | `/api/reset`                  | Wipe the database (demo/testing)          |
| GET    | `/api/health`                 | Health check                              |

Example:
```bash
curl -X POST http://127.0.0.1:5000/api/sync
curl -X POST http://127.0.0.1:5000/api/reconcile
curl "http://127.0.0.1:5000/api/transactions?status=discrepancy"
```

## Extending This Base Project

- **Real connectors**: replace the mock JSON reads with actual API/DB calls
  (Plaid/Open Banking for bank data, SAP/NetSuite SDKs for ERP, etc.).
- **Scheduling**: wire `SyncEngine.run_sync()` into Celery beat, APScheduler, or a cron job.
- **Swap the database**: change `DATABASE_URL` in `core/database.py` to Postgres/MySQL for production.
- **Smarter matching**: replace the rule-based reconciliation with fuzzy string
  matching (e.g. `rapidfuzz`) or a small ML classifier trained on historical matches.
- **Auth & multi-tenancy**: add API keys/OAuth and scope data per company/tenant.
- **Event-driven sync**: replace polling with webhooks from source systems where available.
- **Audit trail**: log every sync/reconciliation run with who/when/what-changed for compliance.

## Disclaimer

This is a **demo/educational base project** using synthetic mock data
stored as local JSON files. It is not a production-ready financial
integration system and should undergo significant security, compliance,
and real-data validation work before handling real financial data.
