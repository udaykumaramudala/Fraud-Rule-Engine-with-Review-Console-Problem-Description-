# 🛡️ SentinEx Guard - Fraud Rule Engine with Review Console

A full-stack, enterprise-grade **Fraud Detection Engine and Reviewer Console** designed to evaluate transaction risks in real-time, detect multi-dimensional fraud vectors, notify security response teams via **AWS SES & SNS**, and provide compliance officers with a sleek, interactive investigation workstation.

---

## 📋 Problem Statement & Requirements Traceability

| Requirement | Implementation Details | Status |
| :--- | :--- | :---: |
| **Rule engine for transaction risk evaluation** | Modular evaluation pipeline (`RuleEngine`) calculating weighted composite scores and severity tiers. | ✅ Complete |
| **At least three independent rules** | 1. `transaction_velocity`<br>2. `unusual_transaction_amount`<br>3. `impossible_geographical_location`<br>4. `high_risk_merchant_category` | ✅ Complete (4 rules) |
| **Open-Closed Principle: Pluggable rules without modifying core engine** | `RuleRegistry` with `@register_rule` decorator and dynamic auto-discovery from `app.engine.rules.*`. | ✅ Complete |
| **Persist transactions and fraud flags** | Full relational persistence via SQLAlchemy 2.0 with support for SQLite and PostgreSQL (`transactions`, `rule_evaluations`, `review_audits`, `notification_logs`). | ✅ Complete |
| **React-based reviewer console** | Modern React console with live risk metrics, rule configuration manager, and transaction simulator. | ✅ Complete |
| **Display flagged transactions** | Filterable table supporting status pills (`FLAGGED`, `UNDER_REVIEW`, `CLEARED`, `CONFIRMED_FRAUD`), search queries, and risk badges. | ✅ Complete |
| **Reviewer actions** | In-depth investigation modal with audit note submission, status transitions, and quick-clear actions. | ✅ Complete |
| **AWS SES & SNS notifications** | Rich HTML/Plain-text email dispatch via AWS SES and SMS/Topic dispatch via AWS SNS when risk exceeds threshold (`HIGH_RISK_THRESHOLD`), with automated simulation fallback. | ✅ Complete |

---

## 🏛️ System Architecture

```
                  ┌──────────────────────────────────────────────┐
                  │           React Reviewer Console             │
                  │   - Dashboard KPIs & Analytics               │
                  │   - Flagged Transactions & Quick Review      │
                  │   - Detailed Modal & Rule Telemetry          │
                  │   - Rules Configurator (Enable/Disable/Tune) │
                  │   - Live Transaction Risk Simulator          │
                  └───────────────────────┬──────────────────────┘
                                          │ REST API / CORS
                                          ▼
                  ┌──────────────────────────────────────────────┐
                  │             FastAPI Backend                  │
                  │   - REST Endpoints & Pydantic Validation     │
                  │   - Optional API Key Authentication          │
                  │   - Review Workflow & Audit Trail Service    │
                  └──────┬───────────────────────────────┬───────┘
                         │                               │
                         ▼                               ▼
       ┌─────────────────────────────────┐   ┌──────────────────────────┐
       │     Core Fraud Rule Engine      │   │   Persistence Layer      │
       │  (Closed for Modification)      │   │   (SQLAlchemy 2.0)       │
       │  - Composite Weighted Scoring   │   │   - SQLite / PostgreSQL  │
       │  - Severity Matrix (0 - 100)    │   │   - Transactions         │
       └────────────────┬────────────────┘   │   - Rule Evaluations     │
                        │                    │   - Audit Logs           │
                        ▼                    │   - Notification Logs    │
       ┌─────────────────────────────────┐   └──────────────────────────┘
       │  Dynamic Rule Registry          │                 │
       │  (Open for Extension)           │                 ▼
       │  - Velocity Rule                │   ┌──────────────────────────┐
       │  - Unusual Amount Rule          │   │  AWS Notification Engine │
       │  - Impossible Travel Rule       │──▶│  - AWS SES (Email Alert) │
       │  - Merchant Risk Rule           │   │  - AWS SNS (Topic / SMS) │
       │  - Dynamically Plugged Rules... │   │  - Simulation Fallback   │
       └─────────────────────────────────┘   └──────────────────────────┘
```

---

## 🧩 Open-Closed Extensibility: Adding New Rules

New fraud rules can be added **without touching the core evaluation engine**. Simply create a new file or class inheriting from `BaseRule` and decorate it with `@register_rule`:

```python
from app.engine.base import BaseRule, RuleResult
from app.engine.registry import register_rule

@register_rule
class TorExitNodeRule(BaseRule):
    rule_id = "tor_exit_node_detection"
    rule_name = "Tor Exit Node Connection"
    description = "Flags transactions originating from known anonymizing Tor exit relays"
    enabled = True
    weight = 1.2
    parameters = {"known_relays": ["198.51.100.42", "203.0.113.88"]}

    def evaluate(self, transaction, user_history, system_context=None) -> RuleResult:
        ip = transaction.get("ip_address")
        if ip in self.parameters["known_relays"]:
            return RuleResult(
                is_flagged=True,
                risk_score=85.0,
                severity="HIGH",
                reason=f"Transaction routed through flagged Tor exit node ({ip}).",
                metadata={"ip_address": ip}
            )
        return RuleResult(
            is_flagged=False,
            risk_score=0.0,
            severity="LOW",
            reason="Standard residential/corporate IP address."
        )
```

The engine will automatically discover the rule at startup, expose it to the `/api/rules` API, and incorporate it into the composite risk scoring pipeline.

---

## 🔎 Fraud Detection Rules

1. **Transaction Velocity (`transaction_velocity`)**
   - Monitors frequency of transactions per user within rolling time windows (e.g., 5-minute burst window, 60-minute window).
   - Detects card-testing bots, rapid-fire draining attacks, and script-driven automated fraud.
   - Configurable limits: `short_window_limit`, `critical_burst_limit`, `long_window_limit`.

2. **Unusual Transaction Amount (`unusual_transaction_amount`)**
   - Calculates historical user spending average, variance, standard deviation, and statistical Z-score.
   - Compares the transaction amount against both user-specific multipliers (e.g., 3.0x warning, 5.0x critical) and absolute platform ceilings ($7,500 High, $15,000 Critical).

3. **Impossible Geographical Location (`impossible_geographical_location`)**
   - Computes the spherical great-circle distance between the current transaction and previous geolocations using the **Haversine formula**.
   - Determines implied velocity (km/h) across timestamps.
   - Flags commercial airline violations (>850 km/h) and instant teleportation anomalies (>300 km in <15 minutes).

4. **High-Risk Merchant & Category (`high_risk_merchant_category`)**
   - Monitors MCC categories (crypto exchanges, offshore gambling, darkweb services, cash equivalents).
   - Flags suspicious keyword patterns in merchant descriptors.

---

## 🚀 Quickstart Guide

### Prerequisites
- **Python 3.11+** (Python 3.13 supported)
- **Node.js 18+** & **npm**
- *(Optional)* Docker and Docker Compose

---

### Method 1: Local Development

#### 1. Backend Setup
```bash
# Navigate to backend
cd backend

# Create and activate virtual environment (if not already active)
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI server (runs on http://127.0.0.1:8000)
uvicorn app.main:app --reload --port 8000
```

> **Note**: On startup, if the database is empty, it automatically seeds realistic demo profiles (Alice normal spend, Bob $9,800 anomaly, Carlos Madrid-to-Tokyo teleportation, David bot velocity attack).

Interactive Swagger API docs are accessible at: [http://localhost:8000/docs](http://localhost:8000/docs)

#### 2. Frontend Setup
```bash
# Navigate to frontend (in a separate terminal)
cd frontend

# Install dependencies
npm install

# Start Vite development server (runs on http://localhost:5173)
npm run dev
```

Open your browser to: [http://localhost:5173](http://localhost:5173)

---

### Method 2: Docker Compose (Full Stack with PostgreSQL)

To launch the complete system including a dedicated PostgreSQL 16 container, FastAPI backend, and Nginx-served React frontend:

```bash
docker compose up --build
```

- **Frontend Console**: [http://localhost:8080](http://localhost:8080)
- **Backend API**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧪 Running Automated Tests

A comprehensive test suite of **36 automated tests** covers all fraud rules, haversine speed mechanics, velocity windowing, z-score mathematics, pluggable registry lifecycle, review audit logging, notification dispatch, and REST API integration.

To run all tests from the repository root:

```bash
# Using active virtual environment:
pytest
```

Or from within the `backend/` directory:
```bash
cd backend
pytest -v
```

All 36 tests execute and pass in approximately 2 seconds.

---

## 📡 AWS SES & SNS Notification Configuration

The application includes an AWS notification service using `boto3`.

### Simulation Mode (Out of the Box)
If AWS credentials are not specified, the system automatically runs in **Simulation Mode**, generating realistic delivery logs and tracking mock message IDs without requiring AWS account setup.

### Live Production Mode
Set the following environment variables in `backend/.env` (or via Docker Compose):

```env
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
SES_SENDER_EMAIL=fraud-alerts@yourdomain.com
SES_ALERT_RECIPIENT=security-response@yourdomain.com
SNS_TOPIC_ARN=arn:aws:sns:us-east-1:123456789012:fraud-critical-alerts
FORCE_MOCK_NOTIFICATIONS=false
```

When a transaction crosses `HIGH_RISK_THRESHOLD` (default: 60.0):
1. **AWS SES** formats and dispatches an HTML email report complete with transaction metadata, highlighted fraud vectors, and direct links to the review console.
2. **AWS SNS** publishes a concise alert to the specified SNS Topic ARN or SMS endpoint.
3. Every dispatch attempt is recorded in the `notification_logs` database table.

---

## 📁 Repository Structure

```
codeathon/
├── backend/
│   ├── app/
│   │   ├── engine/                # Core Evaluation Engine
│   │   │   ├── base.py            # BaseRule & RuleResult models
│   │   │   ├── evaluator.py       # RuleEngine (orchestration & composite scoring)
│   │   │   ├── registry.py        # RuleRegistry (dynamic auto-discovery)
│   │   │   └── rules/             # Pluggable Fraud Detection Rules
│   │   │       ├── impossible_travel.py
│   │   │       ├── merchant_risk.py
│   │   │       ├── unusual_amount.py
│   │   │       └── velocity.py
│   │   ├── services/
│   │   │   ├── notification_service.py # AWS SES & SNS integration
│   │   │   ├── review_service.py       # Review status updates & audit trail
│   │   │   └── transaction_service.py  # Ingestion & user history
│   │   ├── config.py              # Pydantic v2 Settings
│   │   ├── database.py            # SQLAlchemy engine & session factory
│   │   ├── main.py                # FastAPI endpoints & lifespan
│   │   ├── models.py              # SQLAlchemy ORM Models
│   │   ├── schemas.py             # Pydantic Schemas & DTOs
│   │   └── seed_data.py           # Demo dataset generator
│   ├── tests/                     # 36 Automated Test Cases
│   │   ├── test_api.py
│   │   ├── test_api_endpoints.py
│   │   ├── test_notifications.py
│   │   ├── test_pluggability.py
│   │   ├── test_rules.py
│   │   └── test_services.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── pytest.ini
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.jsx         # App header & navigation tabs
│   │   │   ├── MetricsCards.jsx   # Top-level KPI statistics cards
│   │   │   ├── NotificationInbox.jsx # Dispatched SES/SNS alerts viewer
│   │   │   ├── RulesManager.jsx   # Rules configuration & toggling UI
│   │   │   ├── TransactionModal.jsx # Detailed investigation & review dialog
│   │   │   ├── TransactionSimulator.jsx # Real-time transaction generator
│   │   │   └── TransactionTable.jsx # Filterable transaction table
│   │   ├── App.jsx                # Main application state & layout
│   │   ├── index.css              # Custom styling & glassmorphic tokens
│   │   └── main.jsx
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── docker-compose.yml             # Full-stack orchestrator
├── pytest.ini                     # Root test discovery configuration
├── problem statement.txt          # Original specification
└── README.md                      # Comprehensive documentation
```
