import httpx
from twilio.rest import Client

from app.core.config import get_settings


class SMSProviderError(Exception):
    pass


async def send_otp_sms_india(mobile_number: str, otp: str) -> None:
    settings = get_settings()
    if not settings.sms_enabled:
        return

    provider = settings.sms_provider.lower().strip()
    if provider == "twilio":
        await _send_otp_twilio(mobile_number, otp)
        return
    if provider == "msg91":
        await _send_otp_msg91(mobile_number, otp)
        return
    raise SMSProviderError(f"Unsupported SMS provider: {settings.sms_provider}")


async def _send_otp_msg91(mobile_number: str, otp: str) -> None:
    settings = get_settings()

    if not settings.msg91_auth_key or not settings.msg91_template_id or not settings.msg91_sender_id:
        raise SMSProviderError("MSG91 configuration is incomplete")

    payload = {
        "template_id": settings.msg91_template_id,
        "short_url": "0",
        "recipients": [{"mobiles": f"91{mobile_number}", "otp": otp}],
    }

    headers = {
        "authkey": settings.msg91_auth_key,
        "content-type": "application/json",
    }

    url = "https://control.msg91.com/api/v5/flow/"
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(url, json=payload, headers=headers)

    if response.status_code >= 400:
        raise SMSProviderError(f"MSG91 error: {response.status_code} {response.text}")


async def _send_otp_twilio(mobile_number: str, otp: str) -> None:
    settings = get_settings()
    if not settings.twilio_account_sid or not settings.twilio_auth_token or not settings.twilio_from_number:
        raise SMSProviderError("Twilio configuration is incomplete")

    to_number = f"+91{mobile_number}"
    body = f"Your OTP for Real Estate login is {otp}. It expires in {settings.otp_expire_minutes} minutes."
    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    try:
        client.messages.create(
            body=body,
            from_=settings.twilio_from_number,
            to=to_number,
        )
    except Exception as exc:  # pragma: no cover
        raise SMSProviderError(f"Twilio error: {exc}") from exc
