from dataclasses import dataclass, field
from typing import Any, Dict, List

# High-risk / blacklisted jurisdictions
HIGH_RISK_COUNTRIES = {"IR", "KP", "MM", "SY", "RU", "YE", "AF", "CU", "SS"}

# Crypto & Privacy currencies from reference catalogue
CRYPTO_CURRENCIES = {
    "BTC",
    "ETH",
    "USDT",
    "USDC",
    "BNB",
    "XRP",
    "SOL",
    "ADA",
    "DOGE",
    "TRX",
    "AVAX",
    "DOT",
    "LINK",
    "LTC",
    "BCH",
    "XLM",
    "NEAR",
    "UNI",
    "DAI",
    "TON",
    "XMR",
    "ZEC",
}


@dataclass
class TriggeredRule:
    rule_id: str
    rule_name: str
    points: int
    reason: str


@dataclass
class RiskResult:
    score: int
    category: str
    reasons: List[str] = field(default_factory=list)
    triggered_rules: List[Dict[str, Any]] = field(default_factory=list)


def evaluate_transaction_risk(transaction: Dic[str, Any]) -> RiskResult:
    """
    Evaluates a transaction dictionary against AML rules and returns a RiskResult.
    """

    score = 0
    triggered: List[TriggeredRule] = []

    amount = transaction.get("amount", 0)
    country = (transaction.get("origin_country_id" or "")).upper()
    currency = (transaction.get("currency_id" or "")).upper()

    # Rule for structuring detection - just below the £10,000 threshold
    if 9000 <= amount <= 9999:
        triggered.append(
            TriggeredRule(
                rule_id="RULE_STRUCTURING",
                rule_name="Structuring Suspicion",
                points=30,
                reason="Amount is just below the £10,000 reporting threshold (potential smurfing).",
            )
        )

    # Rule for high value transfers
    # rule for £50,000
    if amount >= 50000:
        triggered.append(
            TriggeredRule(
                rule_id="RULE_CRITICAL_AMOUNT",
                rule_name="Critical Value Transfer",
                points=45,
                reason=f"Transfer of {amount:,} significantly exceeds typical baseline thresholds.",
            )
        )

    # rule for £10,000
    elif amount >= 10000:
        triggered.append(
            TriggeredRule(
                rule_id="RULE_LARGE_AMOUNT",
                rule_name="High Value Transfer",
                points=25,
                reason=f"Transfer of {amount:,} meets or exceeds standard threshold (£10,000).",
            )
        )

    # Rule for high-risk jurisdiction
    if country in HIGH_RISK_COUNTRIES:
        triggered.append(
            TriggeredRule(
                rule_id="RULE_HIGH_RISK_JURISDICTION",
                rule_name="High-Risk Jurisdiction",
                points=35,
                reason=f"Transaction originates from high-risk jurisdiction ({country}).",
            )
        )

    # Rule for crypto / privacy coin
    if currency in CRYPTO_CURRENCIES:
        triggered.append(
            TriggeredRule(
                rule_id="RULE_CRYPTO_EXPOSURE",
                rule_name="Crypto Exposure",
                points=25,
                reason=f"Involves virtual asset / cryptocurrency transfer ({currency}).",
            )
        )

    # Rule for round sum anomaly on large transfers
    if amount >= 5000 and amount % 1000 == 0 and not (9000 <= amount <= 9999):
        triggered.append(
            TriggeredRule(
                rule_id="RULE_ROUND_AMOUNT",
                rule_name="Round Sum Transfer",
                points=10,
                reason="Large exact round-sum payment pattern detected.",
            )
        )

    # Calculate total score (capped at 100)
    for rule in triggered:
        score += rule.points
    score = min(100, score)

    # determine risk category
    if score >= 60:
        category = "HIGH"
    elif score >= 30:
        category = "MEDIUM"
    else:
        category = "LOW"

    return RiskResult(
        score=score,
        category=category,
        reasons=[rule.reason for rule in triggered],
        triggered_rules=[
            {
                "rule_id": r.rule_id,
                "rule_name": r.rule_name,
                "points": r.points,
                "reason": r.reason,
            }
            for r in triggered
        ],
    )
