import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models import Transaction, RuleEvaluation, NotificationLog, ReviewAudit
from app.schemas import TransactionCreate
from app.engine.evaluator import fraud_engine
from app.services.notification_service import notification_service
import logging

logger = logging.getLogger(__name__)

def generate_txn_id() -> str:
    return f"TXN-{uuid.uuid4().hex[:8].upper()}"

class TransactionService:
    @staticmethod
    def get_user_history(db: Session, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        records = db.query(Transaction).filter(
            Transaction.user_id == user_id
        ).order_by(Transaction.timestamp.desc()).limit(limit).all()

        history = []
        for r in records:
            history.append({
                "transaction_id": r.transaction_id,
                "amount": r.amount,
                "currency": r.currency,
                "latitude": r.latitude,
                "longitude": r.longitude,
                "location_name": r.location_name,
                "timestamp": r.timestamp,
                "merchant": r.merchant,
                "category": r.category
            })
        return history

    @staticmethod
    def process_and_create_transaction(db: Session, txn_in: TransactionCreate) -> Transaction:
        txn_id = generate_txn_id()
        txn_timestamp = txn_in.timestamp or datetime.now(timezone.utc)
        if txn_timestamp.tzinfo is None:
            txn_timestamp = txn_timestamp.replace(tzinfo=timezone.utc)

        txn_dict = {
            "transaction_id": txn_id,
            "user_id": txn_in.user_id,
            "amount": txn_in.amount,
            "currency": txn_in.currency,
            "merchant": txn_in.merchant,
            "category": txn_in.category,
            "latitude": txn_in.latitude,
            "longitude": txn_in.longitude,
            "location_name": txn_in.location_name,
            "ip_address": txn_in.ip_address,
            "device_id": txn_in.device_id,
            "timestamp": txn_timestamp
        }

        # 1. Fetch user history
        user_history = TransactionService.get_user_history(db, txn_in.user_id)

        # 2. Run pluggable rule engine
        report = fraud_engine.evaluate_transaction(txn_dict, user_history)

        # 3. Create Transaction DB model
        db_txn = Transaction(
            transaction_id=txn_id,
            user_id=txn_in.user_id,
            amount=txn_in.amount,
            currency=txn_in.currency,
            merchant=txn_in.merchant,
            category=txn_in.category,
            latitude=txn_in.latitude,
            longitude=txn_in.longitude,
            location_name=txn_in.location_name,
            ip_address=txn_in.ip_address,
            device_id=txn_in.device_id,
            timestamp=txn_timestamp,
            risk_score=report.risk_score,
            risk_level=report.risk_level,
            status=report.status
        )
        db.add(db_txn)
        db.flush() # ensure db_txn is available for foreign keys

        # 4. Save Rule Evaluations
        for rule_res in report.rule_evaluations:
            res_dict = rule_res.to_dict()
            eval_record = RuleEvaluation(
                transaction_id=txn_id,
                rule_id=rule_res.rule_id,
                rule_name=rule_res.rule_name,
                is_flagged=rule_res.is_flagged,
                risk_score=rule_res.risk_score,
                severity=rule_res.severity,
                reason=rule_res.reason,
                metadata_json=res_dict.get("metadata_json", "{}")
            )
            db.add(eval_record)

        # 5. Check if high-risk threshold crossed -> Send AWS SES and SNS notifications
        if report.is_high_risk:
            logger.info(f"Transaction {txn_id} crossed high-risk threshold ({report.risk_score}). Sending AWS SES & SNS alerts.")
            
            # Send AWS SES Email
            ses_result = notification_service.send_ses_email(txn_dict, report)
            ses_log = NotificationLog(
                transaction_id=txn_id,
                channel=ses_result["channel"],
                recipient=ses_result["recipient"],
                subject=ses_result["subject"],
                message=ses_result["message"],
                status=ses_result["status"],
                message_id=ses_result.get("message_id"),
                error_details=ses_result.get("error")
            )
            db.add(ses_log)

            # Send AWS SNS Notification
            sns_result = notification_service.send_sns_notification(txn_dict, report)
            sns_log = NotificationLog(
                transaction_id=txn_id,
                channel=sns_result["channel"],
                recipient=sns_result["recipient"],
                subject=sns_result["subject"],
                message=sns_result["message"],
                status=sns_result["status"],
                message_id=sns_result.get("message_id"),
                error_details=sns_result.get("error")
            )
            db.add(sns_log)

        db.commit()
        db.refresh(db_txn)
        return db_txn

transaction_service = TransactionService()
