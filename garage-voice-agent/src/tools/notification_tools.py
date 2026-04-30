import logging

logger = logging.getLogger(__name__)


def send_confirmation_sms(phone: str | None, message: str) -> dict:
    logger.info("mock_sms_logged", extra={"phone": phone, "message": message})
    return {
        "status": "logged",
        "provider": "mock",
        "phone": phone,
        "message": message,
        "replace_with": "Twilio or another SMS provider",
    }


def send_garage_summary_email(to_email: str | None, subject: str, body: str) -> dict:
    logger.info("mock_email_logged", extra={"to_email": to_email, "subject": subject})
    return {
        "status": "logged",
        "provider": "mock",
        "to_email": to_email,
        "subject": subject,
        "body": body,
        "replace_with": "SendGrid, Mailgun, Resend, or SMTP",
    }
