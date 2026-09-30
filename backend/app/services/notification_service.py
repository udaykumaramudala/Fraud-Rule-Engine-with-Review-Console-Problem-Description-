import os
import uuid
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from app.config import settings

logger = logging.getLogger(__name__)

class NotificationService:
    """
    AWS SES and SNS Notification Service.
    Dispatches alerts when transactions exceed the high-risk threshold.
    Supports real AWS SES/SNS via boto3, with automatic simulated fallback
    when AWS credentials are not configured in local environment.
    """
    def __init__(self):
        self.region = settings.AWS_REGION
        self.ses_sender = settings.SES_SENDER_EMAIL
        self.ses_recipient = settings.SES_ALERT_RECIPIENT
        self.sns_topic_arn = settings.SNS_TOPIC_ARN
        self.sns_phone = settings.SNS_PHONE_NUMBER
        self._init_aws_clients()

    def _init_aws_clients(self):
        self.ses_client = None
        self.sns_client = None
        self.has_credentials = bool(settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY)

        if not settings.FORCE_MOCK_NOTIFICATIONS and self.has_credentials:
            try:
                self.ses_client = boto3.client(
                    "ses",
                    region_name=self.region,
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    aws_session_token=settings.AWS_SESSION_TOKEN
                )
                self.sns_client = boto3.client(
                    "sns",
                    region_name=self.region,
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    aws_session_token=settings.AWS_SESSION_TOKEN
                )
                logger.info("Initialized real AWS SES and SNS boto3 clients.")
            except Exception as e:
                logger.warning(f"Failed to initialize AWS clients: {e}. Will use simulated mode.")
        else:
            logger.info("Running notification service in simulation mode (set AWS keys to enable live delivery).")

    def format_email_body(self, transaction: Dict[str, Any], evaluation: Any) -> Dict[str, str]:
        flagged_rules = [r for r in evaluation.rule_evaluations if r.is_flagged]
        rules_text = "\n".join([f"- [{r.rule_name}] ({r.severity}): {r.reason}" for r in flagged_rules])
        rules_html = "".join([
            f"<li style='margin-bottom: 8px;'><strong style='color: #ef4444;'>{r.rule_name}</strong> "
            f"(<span style='background:#fee2e2;color:#991b1b;padding:2px 6px;border-radius:4px;font-size:12px;'>{r.severity}</span>)<br/>"
            f"<span style='color: #4b5563;'>{r.reason}</span></li>"
            for r in flagged_rules
        ])

        subject = f"🚨 [HIGH RISK ALERT] Transaction {transaction.get('transaction_id')} - Score: {evaluation.risk_score}"

        text_body = (
            f"FRAUD RISK NOTIFICATION\n"
            f"=======================\n"
            f"Transaction ID : {transaction.get('transaction_id')}\n"
            f"User ID        : {transaction.get('user_id')}\n"
            f"Amount         : {transaction.get('currency', 'USD')} {transaction.get('amount', 0):,.2f}\n"
            f"Merchant       : {transaction.get('merchant')}\n"
            f"Location       : {transaction.get('location_name')}\n"
            f"Risk Score     : {evaluation.risk_score}/100 ({evaluation.risk_level})\n"
            f"Timestamp      : {transaction.get('timestamp')}\n\n"
            f"Triggered Rules ({len(flagged_rules)}):\n"
            f"{rules_text}\n\n"
            f"Action Required: Please review this transaction immediately in the Reviewer Console."
        )

        html_body = f"""
        <html>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f8fafc; padding: 24px; color: #1e293b;">
            <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
                <div style="background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%); padding: 20px 24px; color: #ffffff;">
                    <div style="font-size: 13px; text-transform: uppercase; letter-spacing: 1px; opacity: 0.9;">Automated Security Alert</div>
                    <h2 style="margin: 6px 0 0 0; font-size: 20px; font-weight: 700;">High-Risk Transaction Detected</h2>
                </div>
                <div style="padding: 24px;">
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                        <tr><td style="padding: 8px 0; color: #64748b; font-size: 14px;">Transaction ID</td><td style="font-weight: 600; text-align: right;">{transaction.get('transaction_id')}</td></tr>
                        <tr><td style="padding: 8px 0; color: #64748b; font-size: 14px;">User Account</td><td style="font-weight: 600; text-align: right;">{transaction.get('user_id')}</td></tr>
                        <tr><td style="padding: 8px 0; color: #64748b; font-size: 14px;">Amount</td><td style="font-weight: 700; font-size: 18px; color: #dc2626; text-align: right;">{transaction.get('currency', 'USD')} {transaction.get('amount', 0):,.2f}</td></tr>
                        <tr><td style="padding: 8px 0; color: #64748b; font-size: 14px;">Merchant / Category</td><td style="font-weight: 600; text-align: right;">{transaction.get('merchant')} ({transaction.get('category')})</td></tr>
                        <tr><td style="padding: 8px 0; color: #64748b; font-size: 14px;">Location</td><td style="font-weight: 600; text-align: right;">{transaction.get('location_name')}</td></tr>
                        <tr><td style="padding: 8px 0; color: #64748b; font-size: 14px;">Risk Assessment</td><td style="font-weight: 700; text-align: right;"><span style="color: #dc2626;">{evaluation.risk_score} / 100 ({evaluation.risk_level})</span></td></tr>
                    </table>

                    <div style="background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; padding: 16px; margin-bottom: 20px;">
                        <h4 style="margin: 0 0 10px 0; color: #991b1b; font-size: 14px; text-transform: uppercase;">Triggered Fraud Rules ({len(flagged_rules)})</h4>
                        <ul style="margin: 0; padding-left: 20px; font-size: 13px; line-height: 1.5;">
                            {rules_html}
                        </ul>
                    </div>

                    <p style="font-size: 13px; color: #64748b; margin-bottom: 0;">
                        This alert was automatically generated by the Fraud Rule Engine. Log in to the <strong>Reviewer Console</strong> to inspect telemetry, clear, or confirm fraud.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        return {"subject": subject, "text": text_body, "html": html_body}

    def send_ses_email(self, transaction: Dict[str, Any], evaluation: Any) -> Dict[str, Any]:
        """
        Sends an email alert via AWS SES (or mock if AWS credentials are not set).
        """
        payload = self.format_email_body(transaction, evaluation)
        recipient = self.ses_recipient
        sender = self.ses_sender

        if self.ses_client and not settings.FORCE_MOCK_NOTIFICATIONS:
            try:
                response = self.ses_client.send_email(
                    Source=sender,
                    Destination={"ToAddresses": [recipient]},
                    Message={
                        "Subject": {"Data": payload["subject"], "Charset": "UTF-8"},
                        "Body": {
                            "Text": {"Data": payload["text"], "Charset": "UTF-8"},
                            "Html": {"Data": payload["html"], "Charset": "UTF-8"}
                        }
                    }
                )
                msg_id = response.get("MessageId", f"ses-{uuid.uuid4().hex[:12]}")
                logger.info(f"Dispatched live AWS SES email. MessageId: {msg_id}")
                return {
                    "channel": "AWS_SES",
                    "status": "SENT",
                    "recipient": recipient,
                    "subject": payload["subject"],
                    "message": payload["text"],
                    "message_id": msg_id,
                    "error": None
                }
            except (ClientError, NoCredentialsError) as e:
                logger.error(f"Live AWS SES dispatch failed: {e}. Falling back to recorded simulation.")
                return {
                    "channel": "AWS_SES",
                    "status": "FAILED",
                    "recipient": recipient,
                    "subject": payload["subject"],
                    "message": payload["text"],
                    "message_id": None,
                    "error": str(e)
                }

        if settings.REQUIRE_LIVE_NOTIFICATIONS:
            return {
                "channel": "AWS_SES",
                "status": "FAILED",
                "recipient": recipient,
                "subject": payload["subject"],
                "message": payload["text"],
                "message_id": None,
                "error": "Live AWS SES delivery is required but the client is not configured."
            }

        # Simulated fallback (demonstrates full payload and functionality out-of-the-box)
        mock_id = f"ses-sim-{uuid.uuid4().hex[:12]}"
        logger.info(f"[SIMULATED AWS SES] Dispatched email alert to {recipient}. Simulated MsgID: {mock_id}")
        return {
            "channel": "AWS_SES",
            "status": "SIMULATED_SUCCESS",
            "recipient": recipient,
            "subject": payload["subject"],
            "message": payload["text"],
            "message_id": mock_id,
            "error": None
        }

    def send_sns_notification(self, transaction: Dict[str, Any], evaluation: Any) -> Dict[str, Any]:
        """
        Sends an alert via AWS SNS topic or SMS.
        """
        short_msg = (
            f"🚨 [FRAUD ALERT] Txn {transaction.get('transaction_id')} for "
            f"${transaction.get('amount', 0):,.2f} at {transaction.get('merchant')} "
            f"flagged HIGH RISK (Score: {evaluation.risk_score}). Review immediately!"
        )

        recipient = self.sns_topic_arn or self.sns_phone or "arn:aws:sns:us-east-1:123456789012:fraud-alerts"

        if self.sns_client and not settings.FORCE_MOCK_NOTIFICATIONS and (self.sns_topic_arn or self.sns_phone):
            try:
                params = {"Message": short_msg, "Subject": f"Fraud Alert {transaction.get('transaction_id')}"}
                if self.sns_topic_arn:
                    params["TopicArn"] = self.sns_topic_arn
                elif self.sns_phone:
                    params["PhoneNumber"] = self.sns_phone

                response = self.sns_client.publish(**params)
                msg_id = response.get("MessageId", f"sns-{uuid.uuid4().hex[:12]}")
                return {
                    "channel": "AWS_SNS",
                    "status": "SENT",
                    "recipient": recipient,
                    "subject": params["Subject"],
                    "message": short_msg,
                    "message_id": msg_id,
                    "error": None
                }
            except Exception as e:
                logger.error(f"Live AWS SNS publish failed: {e}")
                return {
                    "channel": "AWS_SNS",
                    "status": "FAILED",
                    "recipient": recipient,
                    "subject": "Fraud Alert",
                    "message": short_msg,
                    "message_id": None,
                    "error": str(e)
                }

        if settings.REQUIRE_LIVE_NOTIFICATIONS:
            return {
                "channel": "AWS_SNS",
                "status": "FAILED",
                "recipient": recipient,
                "subject": f"Fraud Alert {transaction.get('transaction_id')}",
                "message": short_msg,
                "message_id": None,
                "error": "Live AWS SNS delivery is required but the client or destination is not configured."
            }

        # Simulated fallback
        mock_id = f"sns-sim-{uuid.uuid4().hex[:12]}"
        return {
            "channel": "AWS_SNS",
            "status": "SIMULATED_SUCCESS",
            "recipient": recipient,
            "subject": f"Fraud Alert {transaction.get('transaction_id')}",
            "message": short_msg,
            "message_id": mock_id,
            "error": None
        }

notification_service = NotificationService()
