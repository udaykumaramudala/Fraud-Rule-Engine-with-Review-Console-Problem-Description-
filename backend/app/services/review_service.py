from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models import Transaction, ReviewAudit

class ReviewService:
    @staticmethod
    def update_transaction_status(
        db: Session,
        transaction_id: str,
        new_status: str,
        reviewer: str,
        notes: Optional[str] = None
    ) -> Transaction:
        valid_statuses = ["CLEARED", "UNDER_REVIEW", "CONFIRMED_FRAUD", "FLAGGED"]
        if new_status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status '{new_status}'. Allowed: {valid_statuses}"
            )

        txn = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
        if not txn:
            raise HTTPException(status_code=404, detail=f"Transaction '{transaction_id}' not found.")

        prev_status = txn.status
        action_map = {
            "CLEARED": "CLEARED_BY_REVIEWER",
            "CONFIRMED_FRAUD": "FRAUD_CONFIRMED",
            "UNDER_REVIEW": "INVESTIGATION_STARTED",
            "FLAGGED": "REFLAGGED"
        }
        action_type = action_map.get(new_status, "STATUS_UPDATED")

        now = datetime.now(timezone.utc)
        txn.status = new_status
        txn.reviewed_by = reviewer
        txn.reviewed_at = now
        txn.review_notes = notes

        # Audit log entry
        audit_entry = ReviewAudit(
            transaction_id=transaction_id,
            previous_status=prev_status,
            new_status=new_status,
            action_type=action_type,
            reviewer=reviewer,
            notes=notes,
            created_at=now
        )
        db.add(audit_entry)
        db.commit()
        db.refresh(txn)
        return txn

review_service = ReviewService()
