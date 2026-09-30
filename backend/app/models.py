from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(64), unique=True, index=True, nullable=False)
    user_id = Column(String(64), index=True, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(8), default="USD")
    merchant = Column(String(128), nullable=False)
    category = Column(String(64), default="general")
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location_name = Column(String(128), default="Unknown")
    ip_address = Column(String(45), default="127.0.0.1")
    device_id = Column(String(64), default="unknown_device")
    timestamp = Column(DateTime, default=utc_now, index=True)
    
    # Engine evaluation results
    risk_score = Column(Float, default=0.0)
    risk_level = Column(String(16), default="LOW") # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String(32), default="CLEARED", index=True) # CLEARED, FLAGGED, UNDER_REVIEW, CONFIRMED_FRAUD
    
    # Review details
    reviewed_by = Column(String(64), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    rule_evaluations = relationship("RuleEvaluation", back_populates="transaction", cascade="all, delete-orphan")
    audit_logs = relationship("ReviewAudit", back_populates="transaction", cascade="all, delete-orphan")
    notifications = relationship("NotificationLog", back_populates="transaction", cascade="all, delete-orphan")

class RuleEvaluation(Base):
    __tablename__ = "rule_evaluations"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(64), ForeignKey("transactions.transaction_id"), index=True, nullable=False)
    rule_id = Column(String(64), index=True, nullable=False)
    rule_name = Column(String(128), nullable=False)
    is_flagged = Column(Boolean, default=False)
    risk_score = Column(Float, default=0.0)
    severity = Column(String(16), default="LOW") # LOW, MEDIUM, HIGH, CRITICAL
    reason = Column(Text, nullable=False)
    metadata_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=utc_now)

    transaction = relationship("Transaction", back_populates="rule_evaluations")

class ReviewAudit(Base):
    __tablename__ = "review_audits"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(64), ForeignKey("transactions.transaction_id"), index=True, nullable=False)
    previous_status = Column(String(32), nullable=False)
    new_status = Column(String(32), nullable=False)
    action_type = Column(String(32), nullable=False) # REVIEW_STARTED, CLEARED, CONFIRMED_FRAUD, NOTE_ADDED
    reviewer = Column(String(64), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    transaction = relationship("Transaction", back_populates="audit_logs")

class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(64), ForeignKey("transactions.transaction_id"), index=True, nullable=False)
    channel = Column(String(32), nullable=False) # AWS_SES, AWS_SNS
    recipient = Column(String(128), nullable=False)
    subject = Column(String(256), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(32), default="SENT") # SENT, SIMULATED_SUCCESS, FAILED
    message_id = Column(String(128), nullable=True)
    error_details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    transaction = relationship("Transaction", back_populates="notifications")
