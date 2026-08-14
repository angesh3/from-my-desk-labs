"""Request and response models for the educational policy gate."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

Decision = Literal["allow", "confirm", "step_up", "deny"]
RequiredAction = Optional[Literal["customer_confirmation", "mfa_verification"]]
CheckResult = Literal["pass", "fail"]


def as_decimal(value: object) -> Decimal:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("Amount must be a decimal number.") from exc
    if not amount.is_finite():
        raise ValueError("Amount must be a finite decimal number.")
    return amount


class ProposedOrder(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=16)
    side: Literal["buy", "sell"]
    quantity: int = Field(..., gt=0, le=1_000_000)
    limit_price: Decimal
    account_id: str = Field(..., min_length=1, max_length=64)

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("account_id")
    @classmethod
    def normalize_account(cls, value: str) -> str:
        return value.strip()

    @field_validator("limit_price", mode="before")
    @classmethod
    def parse_price(cls, value: object) -> Decimal:
        amount = as_decimal(value)
        if amount <= 0:
            raise ValueError("limit_price must be greater than zero.")
        return amount


class AuthorizationContext(BaseModel):
    customer_confirmed: bool = False
    mfa_verified: bool = False


class EvaluateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    principal_id: str = Field(..., min_length=1, max_length=64)
    agent_id: str = Field(..., min_length=1, max_length=64)
    action: str = Field(..., min_length=1, max_length=64)
    order: ProposedOrder
    authorization_context: AuthorizationContext = Field(
        default_factory=AuthorizationContext
    )

    @field_validator("action")
    @classmethod
    def normalize_action(cls, value: str) -> str:
        return value.strip()


class PolicyCheck(BaseModel):
    name: str
    result: CheckResult
    explanation: str


class EvaluateResponse(BaseModel):
    decision: Decision
    reason_code: str
    reason: str
    required_action: RequiredAction = None
    policy_id: str
    audit_id: str
    notional: Optional[str] = None
    checks: List[PolicyCheck] = Field(default_factory=list)
    execution: Literal["not_performed"] = "not_performed"
