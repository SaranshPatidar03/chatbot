"""Pydantic schemas for organization APIs."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class OrganizationSummary(BaseModel):
    id: str
    name: str
    slug: str
    description: str | None
    created_at: datetime
    my_role: str | None = None

    model_config = {"from_attributes": True}


class OrganizationDetail(OrganizationSummary):
    member_count: int
    created_by_id: str | None = None


class OrganizationListResponse(BaseModel):
    items: list[OrganizationSummary]
    total: int


class OrganizationCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    slug: str | None = Field(default=None, min_length=2, max_length=128)


class OrganizationUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=2000)


class OrganizationMemberItem(BaseModel):
    user_id: str
    email: str
    full_name: str | None
    role: str
    joined_at: datetime


class OrganizationMemberListResponse(BaseModel):
    items: list[OrganizationMemberItem]
    total: int


class OrganizationMemberAddRequest(BaseModel):
    email: EmailStr
    role: str = Field(default="member", pattern="^(admin|member)$")


class OrganizationMemberUpdateRequest(BaseModel):
    role: str = Field(pattern="^(owner|admin|member)$")


class MessageResponse(BaseModel):
    message: str
