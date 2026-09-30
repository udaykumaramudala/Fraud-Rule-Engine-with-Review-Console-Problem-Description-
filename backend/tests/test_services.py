import os
import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

from app.database import Base
from app.models import Transaction, RuleEvaluation, ReviewAudit, NotificationLog
from app.schemas import TransactionCreate
from app.services.transaction_service import transaction_service
from app.services.review_service import review_service


@pytest.fixture
def db_session():
    test_db_url = "sqlite:///:memory:"
    engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_transaction_service_creates_and_evaluates(db_session):
    txn_in = TransactionCreate(
        user_id="USR-SERV-1",
        amount=50.0,
        currency="USD",
        merchant="Corner Coffee",
        category="food_and_beverage",
        latitude=40.7128,
        longitude=-74.0060,
        location_name="New York, USA",
        ip_address="192.168.1.10",
        device_id="iphone_14"
    )

    created = transaction_service.process_and_create_transaction(db_session, txn_in)

    assert created.id is not None
    assert created.transaction_id.startswith("TXN-")
    assert created.user_id == "USR-SERV-1"
    assert created.amount == 50.0
    assert created.status == "CLEARED"

    # Verify rule evaluations persisted
    evals = db_session.query(RuleEvaluation).filter(RuleEvaluation.transaction_id == created.transaction_id).all()
    assert len(evals) >= 3

    # Cleared transaction should have 0 notification logs
    notifications = db_session.query(NotificationLog).filter(NotificationLog.transaction_id == created.transaction_id).all()
    assert len(notifications) == 0


def test_high_risk_transaction_triggers_notifications(db_session):
    # An extreme amount transaction that crosses the high risk threshold
    txn_in = TransactionCreate(
        user_id="USR-SERV-2",
        amount=25000.0,
        currency="USD",
        merchant="Crypto Offshore Escrow",
        category="crypto_exchange",
        latitude=40.7128,
        longitude=-74.0060,
        location_name="New York, USA",
        ip_address="185.220.101.5",
        device_id="unknown_bot"
    )

    created = transaction_service.process_and_create_transaction(db_session, txn_in)

    assert created.status == "FLAGGED"
    assert created.risk_score >= 60.0
    assert created.risk_level in ["HIGH", "CRITICAL"]

    # Verify notifications were created (both SES and SNS)
    notifications = db_session.query(NotificationLog).filter(NotificationLog.transaction_id == created.transaction_id).all()
    channels = {n.channel for n in notifications}
    assert "AWS_SES" in channels
    assert "AWS_SNS" in channels


def test_review_service_status_transition_and_audit(db_session):
    # Setup initial transaction
    txn_in = TransactionCreate(
        user_id="USR-SERV-3",
        amount=150.0,
        currency="USD",
        merchant="Online Electronics Store",
        category="electronics",
        latitude=40.7128,
        longitude=-74.0060,
        location_name="New York, USA",
        ip_address="192.168.1.15",
        device_id="pixel_7"
    )
    created = transaction_service.process_and_create_transaction(db_session, txn_in)

    # Reviewer marks transaction as UNDER_REVIEW
    reviewed = review_service.update_transaction_status(
        db=db_session,
        transaction_id=created.transaction_id,
        new_status="UNDER_REVIEW",
        reviewer="Analyst Alex",
        notes="Contacting cardholder to verify charge."
    )
    assert reviewed.status == "UNDER_REVIEW"
    assert reviewed.reviewed_by == "Analyst Alex"
    assert reviewed.review_notes == "Contacting cardholder to verify charge."

    # Reviewer subsequently marks transaction as CLEARED
    cleared = review_service.update_transaction_status(
        db=db_session,
        transaction_id=created.transaction_id,
        new_status="CLEARED",
        reviewer="Analyst Alex",
        notes="Cardholder confirmed charge."
    )
    assert cleared.status == "CLEARED"

    # Verify audit logs trail
    audits = db_session.query(ReviewAudit).filter(ReviewAudit.transaction_id == created.transaction_id).order_by(ReviewAudit.created_at.asc()).all()
    assert len(audits) == 2
    assert audits[0].new_status == "UNDER_REVIEW"
    assert audits[0].action_type == "INVESTIGATION_STARTED"
    assert audits[1].new_status == "CLEARED"
    assert audits[1].action_type == "CLEARED_BY_REVIEWER"


def test_review_service_rejects_invalid_status(db_session):
    with pytest.raises(HTTPException) as exc_info:
        review_service.update_transaction_status(
            db=db_session,
            transaction_id="TXN-NON-EXISTENT",
            new_status="INVALID_STATUS",
            reviewer="Analyst"
        )
    assert exc_info.value.status_code == 400


def test_review_service_handles_missing_transaction(db_session):
    with pytest.raises(HTTPException) as exc_info:
        review_service.update_transaction_status(
            db=db_session,
            transaction_id="TXN-DOES-NOT-EXIST",
            new_status="CLEARED",
            reviewer="Analyst"
        )
    assert exc_info.value.status_code == 404
