from typing import List, Optional
from pydantic import BaseModel
from app.schemas.transaction import TransactionResponse


class TriggeredRuleResponse(BaseModel):
    rule_id: str
    rule_name: str
    points: int
    reason: str


class RiskAssessmentResponse(BaseModel):
    transaction_id: int
    risk_score: int
    risk_category: str
    reasons: List[str]
    triggered_rules: List[TriggeredRuleResponse]


class TransactionWithRiskResponse(TransactionResponse):
    risk_score: int
    risk_category: str
    reasons: Optional[List[str]] = []
