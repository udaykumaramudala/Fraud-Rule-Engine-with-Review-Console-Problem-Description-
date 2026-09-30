import os
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import or_, func, text

from app.database import Base, engine, get_db
from app.models import Transaction, RuleEvaluation, ReviewAudit, NotificationLog
from app.schemas import (
    TransactionCreate, TransactionOut, ReviewActionRequest,
    RuleInfoOut, RuleConfigUpdate, DashboardStatsOut, NotificationLogOut
)
from app.engine.registry import rule_registry
from app.services.transaction_service import transaction_service
from app.services.review_service import review_service
from app.seed_data import seed_database
from app.config import settings
from contextlib import asynccontextmanager
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# Initialize database schema
Base.metadata.create_all(bind=engine)

# Auto-discover rules
rule_registry.auto_discover_rules()

@asynccontextmanager
async def lifespan(app: FastAPI):
    db = next(get_db())
    try:
        # Check if database has any transactions; if empty, automatically seed
        if db.query(Transaction).count() == 0:
            logger.info("Database is empty. Automatically seeding demo dataset...")
            seed_database(reset=False)
    finally:
        db.close()
    yield

app = FastAPI(
    title="Fraud Rule Engine & Review Console API",
    description="Intelligent transaction risk evaluation, pluggable rules, reviewer console, and AWS SES/SNS alerts",
    version="1.0.0",
    lifespan=lifespan
)

PUBLIC_PATHS = {"/", "/health", "/docs", "/openapi.json", "/redoc"}

@app.middleware("http")
async def require_api_key(request: Request, call_next):
    if settings.API_KEY and request.method != "OPTIONS" and request.url.path not in PUBLIC_PATHS:
        supplied_key = request.headers.get("X-API-Key")
        if supplied_key != settings.API_KEY:
            return JSONResponse(status_code=401, content={"detail": "A valid X-API-Key header is required."})
    return await call_next(request)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "service": "Fraud Rule Engine API",
        "status": "operational",
        "active_rules_count": len(rule_registry.get_active_rules()),
        "high_risk_threshold": settings.HIGH_RISK_THRESHOLD,
        "docs_url": "/docs"
    }

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {
        "status": "healthy",
        "environment": settings.ENV,
        "database": "connected",
        "notifications": "live" if settings.REQUIRE_LIVE_NOTIFICATIONS else "live-or-simulated"
    }

# -------------------------------------------------------------------
# Transaction Endpoints
# -------------------------------------------------------------------
@app.get("/api/transactions", response_model=List[TransactionOut])
def list_transactions(
    status: Optional[str] = None,
    risk_level: Optional[str] = None,
    user_id: Optional[str] = None,
    flagged_only: bool = False,
    search: Optional[str] = None,
    limit: int = Query(100, le=500),
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(Transaction)

    if flagged_only:
        query = query.filter(Transaction.status.in_(["FLAGGED", "UNDER_REVIEW", "CONFIRMED_FRAUD"]))
    elif status:
        query = query.filter(Transaction.status == status)

    if risk_level:
        query = query.filter(Transaction.risk_level == risk_level)

    if user_id:
        query = query.filter(Transaction.user_id == user_id)

    if search:
        term = f"%{search}%"
        query = query.filter(
            or_(
                Transaction.transaction_id.ilike(term),
                Transaction.user_id.ilike(term),
                Transaction.merchant.ilike(term),
                Transaction.location_name.ilike(term)
            )
        )

    return query.order_by(Transaction.timestamp.desc()).offset(offset).limit(limit).all()

@app.get("/api/transactions/{transaction_id}", response_model=TransactionOut)
def get_transaction(transaction_id: str, db: Session = Depends(get_db)):
    txn = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail=f"Transaction '{transaction_id}' not found.")
    return txn

@app.post("/api/transactions", response_model=TransactionOut)
def create_transaction(txn_in: TransactionCreate, db: Session = Depends(get_db)):
    """
    Ingest a new transaction, evaluate against registered rules, persist,
    and trigger AWS SES/SNS if risk crosses threshold.
    """
    return transaction_service.process_and_create_transaction(db, txn_in)

@app.post("/api/transactions/{transaction_id}/review", response_model=TransactionOut)
def review_transaction_endpoint(
    transaction_id: str,
    action: ReviewActionRequest,
    db: Session = Depends(get_db)
):
    """
    Reviewer Console Action: Mark transaction as CLEARED, UNDER_REVIEW, or CONFIRMED_FRAUD.
    """
    return review_service.update_transaction_status(
        db,
        transaction_id=transaction_id,
        new_status=action.status,
        reviewer=action.reviewer,
        notes=action.notes
    )

# -------------------------------------------------------------------
# Rules Management Endpoints (Open-Closed Pluggability)
# -------------------------------------------------------------------
@app.get("/api/rules", response_model=List[RuleInfoOut])
def get_all_rules():
    rules = rule_registry.get_all_rules()
    return [r.get_info() for r in rules]

@app.post("/api/rules/{rule_id}/toggle")
def toggle_rule(rule_id: str):
    rule = rule_registry.get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule '{rule_id}' not found.")
    rule.enabled = not rule.enabled
    return {"rule_id": rule_id, "enabled": rule.enabled}

@app.post("/api/rules/{rule_id}/config")
def update_rule_config(rule_id: str, config: RuleConfigUpdate):
    rule = rule_registry.update_rule(
        rule_id,
        enabled=config.enabled,
        weight=config.weight,
        parameters=config.parameters
    )
    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule '{rule_id}' not found.")
    return rule.get_info()

# -------------------------------------------------------------------
# Analytics & Audit / Notifications Endpoints
# -------------------------------------------------------------------
@app.get("/api/analytics", response_model=DashboardStatsOut)
def get_analytics(db: Session = Depends(get_db)):
    total_tx = db.query(Transaction).count()
    flagged = db.query(Transaction).filter(Transaction.status == "FLAGGED").count()
    cleared = db.query(Transaction).filter(Transaction.status == "CLEARED").count()
    under_review = db.query(Transaction).filter(Transaction.status == "UNDER_REVIEW").count()
    confirmed = db.query(Transaction).filter(Transaction.status == "CONFIRMED_FRAUD").count()
    high_risk = db.query(Transaction).filter(Transaction.risk_score >= settings.HIGH_RISK_THRESHOLD).count()
    notifications_count = db.query(NotificationLog).count()

    avg_score_res = db.query(func.avg(Transaction.risk_score)).scalar()
    avg_score = round(float(avg_score_res), 1) if avg_score_res is not None else 0.0

    # Rule trigger stats
    trigger_counts = {}
    evals = db.query(RuleEvaluation.rule_name, func.count(RuleEvaluation.id))\
              .filter(RuleEvaluation.is_flagged == True)\
              .group_by(RuleEvaluation.rule_name).all()
    for name, cnt in evals:
        trigger_counts[name] = cnt

    return DashboardStatsOut(
        total_transactions=total_tx,
        flagged_count=flagged,
        cleared_count=cleared,
        under_review_count=under_review,
        confirmed_fraud_count=confirmed,
        high_risk_count=high_risk,
        notifications_sent_count=notifications_count,
        average_risk_score=avg_score,
        rules_trigger_stats=trigger_counts
    )

@app.get("/api/notifications", response_model=List[NotificationLogOut])
def get_notifications(limit: int = 50, db: Session = Depends(get_db)):
    return db.query(NotificationLog).order_by(NotificationLog.created_at.desc()).limit(limit).all()

@app.post("/api/seed")
def reseed_database():
    seed_database(reset=True)
    return {"message": "Database reseeded successfully with realistic demo scenarios."}
