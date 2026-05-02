from redis.asyncio import Redis

from app.core.config import get_settings

settings = get_settings()
redis_client = Redis.from_url(settings.redis_url, decode_responses=True)


async def get_redis() -> Redis:
    return redis_client


def key_otp(mobile_number: str) -> str:
    return f"otp:{mobile_number}"


def key_otp_attempts(mobile_number: str) -> str:
    return f"otp_attempts:{mobile_number}"


def key_otp_requests(mobile_number: str) -> str:
    return f"otp_requests:{mobile_number}"


def key_user_permissions(user_id: str) -> str:
    return f"user_permissions:{user_id}"


def key_user_roles(user_id: str) -> str:
    return f"user_roles:{user_id}"


def key_property_trust_score(property_id: str) -> str:
    return f"property_trust_score:{property_id}"


def key_user_trust_score(user_id: str) -> str:
    return f"user_trust_score:{user_id}"
