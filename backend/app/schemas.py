from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict

class RuleEvaluationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    rule_id: str
    rule_name: str
    is_flagged: bool
    risk_score: float
    severity: str
    reason: str
    metadata_json: Optional[str] = "{}"
    created_at: Optional[datetime] = None


class ReviewAuditOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    transaction_id: str
    previous_status: str
    new_status: str
    action_type: str
    reviewer: str
    notes: Optional[str] = None
    created_at: datetime


class NotificationLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    transaction_id: str
    channel: str
    recipient: str
    subject: str
    message: str
    status: str
    message_id: Optional[str] = None
    error_details: Optional[str] = None
    created_at: datetime


class TransactionCreate(BaseModel):
    user_id: str = Field(..., examples=["USR-8901"])
    amount: float = Field(..., gt=0, examples=[250.00])
    currency: str = Field("USD", examples=["USD"])
    merchant: str = Field(..., examples=["Amazon.com"])
    category: str = Field("retail", examples=["electronics"])
    latitude: float = Field(..., examples=[40.7128])
    longitude: float = Field(..., examples=[-74.0060])
    location_name: str = Field("New York, USA", examples=["New York, USA"])
    ip_address: str = Field("192.168.1.1", examples=["198.51.100.42"])
    device_id: str = Field("device_chrome_win", examples=["device_chrome_win"])
    timestamp: Optional[datetime] = None


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    transaction_id: str
    user_id: str
    amount: float
    currency: str
    merchant: str
    category: str
    latitude: float
    longitude: float
    location_name: str
    ip_address: str
    device_id: str
    timestamp: datetime
    risk_score: float
    risk_level: str
    status: str
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    created_at: datetime
    rule_evaluations: List[RuleEvaluationOut] = []
    audit_logs: List[ReviewAuditOut] = []
    notifications: List[NotificationLogOut] = []


class ReviewActionRequest(BaseModel):
    status: str = Field(..., description="CLEARED, UNDER_REVIEW, or CONFIRMED_FRAUD")
    reviewer: str = Field("Compliance Officer", examples=["Sarah Connor"])
    notes: Optional[str] = Field("", examples=["Verified customer identity via callback."])


class RuleConfigUpdate(BaseModel):
    enabled: Optional[bool] = None
    weight: Optional[float] = None
    parameters: Optional[Dict[str, Any]] = None


class RuleInfoOut(BaseModel):
    rule_id: str
    rule_name: str
    description: str
    enabled: bool
    weight: float
    parameters: Dict[str, Any]


class DashboardStatsOut(BaseModel):
    total_transactions: int
    flagged_count: int
    cleared_count: int
    under_review_count: int
    confirmed_fraud_count: int
    high_risk_count: int
    notifications_sent_count: int
    average_risk_score: float
    rules_trigger_stats: Dict[str, int]
