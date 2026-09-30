from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError
from app.services.notification_service import NotificationService
from app.engine.evaluator import EvaluationReport
from app.engine.base import RuleResult


def test_email_body_formatting():
    service = NotificationService()
    txn = {
        "transaction_id": "TXN-ALERT-1",
        "user_id": "USR-ALERT",
        "amount": 12500.0,
        "currency": "USD",
        "merchant": "Luxury Watches",
        "category": "retail",
        "location_name": "London, UK",
        "timestamp": "2026-09-30T12:00:00Z"
    }
    report = EvaluationReport(
        risk_score=92.5,
        risk_level="CRITICAL",
        status="FLAGGED",
        is_high_risk=True,
        rule_evaluations=[
            RuleResult(
                rule_id="unusual_transaction_amount",
                rule_name="Unusual Transaction Amount",
                is_flagged=True,
                risk_score=90.0,
                severity="CRITICAL",
                reason="Severe amount anomaly: USD 12,500.00 is 10.0x higher than average."
            )
        ]
    )

    formatted = service.format_email_body(txn, report)
    assert "TXN-ALERT-1" in formatted["subject"]
    assert "92.5" in formatted["subject"]
    assert "Luxury Watches" in formatted["text"]
    assert "Unusual Transaction Amount" in formatted["html"]
    assert "CRITICAL" in formatted["html"]


def test_ses_simulated_dispatch_when_keys_missing():
    service = NotificationService()
    service.ses_client = None  # Force simulation fallback

    txn = {"transaction_id": "TXN-SIM-1", "amount": 5000.0, "merchant": "Test"}
    report = EvaluationReport(
        risk_score=75.0,
        risk_level="HIGH",
        status="FLAGGED",
        is_high_risk=True,
        rule_evaluations=[]
    )

    res = service.send_ses_email(txn, report)
    assert res["channel"] == "AWS_SES"
    assert res["status"] == "SIMULATED_SUCCESS"
    assert res["message_id"].startswith("ses-sim-")
    assert res["error"] is None


def test_sns_simulated_dispatch_when_keys_missing():
    service = NotificationService()
    service.sns_client = None

    txn = {"transaction_id": "TXN-SIM-2", "amount": 5000.0, "merchant": "Test Merchant"}
    report = EvaluationReport(
        risk_score=80.0,
        risk_level="HIGH",
        status="FLAGGED",
        is_high_risk=True,
        rule_evaluations=[]
    )

    res = service.send_sns_notification(txn, report)
    assert res["channel"] == "AWS_SNS"
    assert res["status"] == "SIMULATED_SUCCESS"
    assert res["message_id"].startswith("sns-sim-")
    assert "Test Merchant" in res["message"]


from app.config import settings


def test_ses_live_dispatch_with_mocked_boto3(monkeypatch):
    monkeypatch.setattr(settings, "FORCE_MOCK_NOTIFICATIONS", False)
    service = NotificationService()
    mock_boto_ses = MagicMock()
    mock_boto_ses.send_email.return_value = {"MessageId": "ses-live-msg-12345"}
    service.ses_client = mock_boto_ses

    txn = {"transaction_id": "TXN-LIVE-1", "amount": 6000.0, "merchant": "Live Store"}
    report = EvaluationReport(
        risk_score=70.0,
        risk_level="HIGH",
        status="FLAGGED",
        is_high_risk=True,
        rule_evaluations=[]
    )

    res = service.send_ses_email(txn, report)
    assert res["status"] == "SENT"
    assert res["message_id"] == "ses-live-msg-12345"
    mock_boto_ses.send_email.assert_called_once()


def test_ses_live_dispatch_error_handling(monkeypatch):
    monkeypatch.setattr(settings, "FORCE_MOCK_NOTIFICATIONS", False)
    service = NotificationService()
    mock_boto_ses = MagicMock()
    mock_boto_ses.send_email.side_effect = ClientError(
        {"Error": {"Code": "MessageRejected", "Message": "Email address not verified."}},
        "SendEmail"
    )
    service.ses_client = mock_boto_ses

    txn = {"transaction_id": "TXN-ERR-1", "amount": 6000.0, "merchant": "Live Store"}
    report = EvaluationReport(
        risk_score=70.0,
        risk_level="HIGH",
        status="FLAGGED",
        is_high_risk=True,
        rule_evaluations=[]
    )

    res = service.send_ses_email(txn, report)
    assert res["status"] == "FAILED"
    assert res["message_id"] is None
    assert "Email address not verified" in res["error"]

