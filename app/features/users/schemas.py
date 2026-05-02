from datetime import datetime
import re

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


INDIA_MOBILE_REGEX = re.compile(r"^[6-9]\d{9}$")


class UserCreate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    mobile_number: str
    email: EmailStr | None = None

    @field_validator("mobile_number")
    @classmethod
    def validate_mobile_number(cls, value: str) -> str:
        normalized = value.strip()
        if normalized.startswith("+91"):
            normalized = normalized[3:]
        if not INDIA_MOBILE_REGEX.match(normalized):
            raise ValueError("Invalid Indian mobile number")
        return normalized


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    email: EmailStr | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str | None
    mobile_number: str
    email: str | None
    is_mobile_verified: bool
    is_email_verified: bool
    is_active: bool
    kyc_verified: bool
    kyc_type: str | None
    kyc_document_url: str | None
    kyc_verified_by: str | None
    kyc_verified_at: datetime | None
    is_agent_verified: bool
    is_company_verified: bool
    trust_score: int
    created_at: datetime
    updated_at: datetime


class UserDeleteOut(BaseModel):
    status: str = "deleted"
    user_id: str


class UserSelfUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    email: EmailStr | None = None


class UserWithAccessOut(UserOut):
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)


class OTPSendRequest(BaseModel):
    mobile_number: str

    @field_validator("mobile_number")
    @classmethod
    def validate_mobile_number(cls, value: str) -> str:
        normalized = value.strip()
        if normalized.startswith("+91"):
            normalized = normalized[3:]
        if not INDIA_MOBILE_REGEX.match(normalized):
            raise ValueError("Invalid Indian mobile number")
        return normalized


class OTPVerifyRequest(BaseModel):
    mobile_number: str
    otp: str = Field(min_length=6, max_length=6)
    full_name: str | None = Field(default=None, max_length=120)

    @field_validator("mobile_number")
    @classmethod
    def validate_mobile_number(cls, value: str) -> str:
        normalized = value.strip()
        if normalized.startswith("+91"):
            normalized = normalized[3:]
        if not INDIA_MOBILE_REGEX.match(normalized):
            raise ValueError("Invalid Indian mobile number")
        return normalized

    @field_validator("otp")
    @classmethod
    def validate_otp(cls, value: str) -> str:
        if not value.isdigit():
            raise ValueError("OTP must contain only digits")
        return value


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class EmailVerificationSendRequest(BaseModel):
    email: EmailStr


class EmailVerificationRequest(BaseModel):
    token: str
