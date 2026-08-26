# AML Transaction Risk Scoring Methodology

The Risk Engine calculates a  risk score (0–100) for every transaction based on observable indicators.

## Scoring Bands
- **0 – 29: LOW RISK** (Standard processing)
- **30 – 59: MEDIUM RISK** (Requires monitoring / review)
- **60 – 100: HIGH RISK** (Immediate analyst alert / potential SAR escalation)

## Indicators & Point Allocation
Format: Rule ID: Indicator Description | Condition | Points

`RULE_LARGE_AMOUNT`: High-Value Transfer | Amount >= £10,000 | +25
`RULE_CRITICAL_AMOUNT`: Critical-Value Transfer | Amount >= £50,000 | +20 (cumulative: +45)
`RULE_STRUCTURING`: Potential Structuring / Smurfing | Amount between £9,000 and £9,999 | +30 |
`RULE_HIGH_RISK_JURISDICTION`: High-Risk Origin Country | Origin country in FATF/Sanction list (e.g. IR, KP, SY, RU, YE, AF, MM) | +35
`RULE_CRYPTO_EXPOSURE`: Cryptocurrency / Privacy Coin Exposure | Currency is crypto or privacy coin (e.g., BTC, ETH, USDT, XMR, ZEC) | +25
`RULE_ROUND_AMOUNT`: Anomalous Round Large Sum | Amount >= £5,000 and multiple of 1,000 | +10












