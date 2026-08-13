from typing import List, Literal, Optional

from pydantic import BaseModel, Field, PositiveInt


class ProposedOrder(BaseModel):
    ticker: str = Field(..., min_length=1)
    side: Literal["buy", "sell"]
    quantity: PositiveInt
    limit_price: float = Field(..., gt=0)
    account_id: str = Field(..., min_length=1)


class EvaluateRequest(BaseModel):
    agent_id: str = Field(..., min_length=1)
    action: Literal["propose_paper_order"]
    order: ProposedOrder


class EvaluateResponse(BaseModel):
    decision: Literal["allow", "deny"]
    reason_code: str
    message: str
    notional: Optional[float] = None
    policy_bundle: Optional[str] = None
    checks: List[str] = Field(default_factory=list)
