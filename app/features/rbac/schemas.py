from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PermissionCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    description: str | None = Field(default=None, max_length=500)


class PermissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    created_at: datetime


class RoleCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    description: str | None = Field(default=None, max_length=500)


class RoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    permissions: list[PermissionOut] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class AssignPermissionRequest(BaseModel):
    permission_id: str


class AssignRoleRequest(BaseModel):
    role_id: str
