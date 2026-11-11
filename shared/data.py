from __future__ import annotations

import json
from pathlib import Path

DATA_FILE = Path(__file__).parents[1] / "data" / "finance_facts.json"


def load_facts() -> dict:
    """Load the small, fictional bank dataset."""
    return json.loads(DATA_FILE.read_text())


def facts_as_text() -> str:
    """Create readable context for lessons that have not introduced tools yet."""
    data = load_facts()
    lines = [f"Company: {data['company']}", "\nQuarterly financials:"]
    for row in data["financials"]:
        lines.append(
            f"{row['period']}: revenue ${row['revenue_million_usd']}m; net income ${row['net_income_million_usd']}m; "
            f"deposits ${row['deposits_million_usd']}m; loans ${row['loans_million_usd']}m; NIM {row['net_interest_margin_pct']}%; "
            f"charge-off rate {row['charge_off_rate_pct']}%; source: {row['source']}"
        )
    lines.append("\nCustomer sample:")
    for row in data["customers"]:
        lines.append(
            f"{row['customer_id']}: {row['segment']}; products={', '.join(row['products'])}; login {row['days_since_login']} days ago; "
            f"tickets last 90d={row['support_tickets_90d']}; missed payments={row['missed_payments_12m']}; balance=${row['balance_usd']}; source: {row['source']}"
        )
    lines.append("\nProduct policies:")
    for row in data["policies"]:
        lines.append(f"{row['product']}: annual fee=${row['annual_fee_usd']}; monthly fee=${row['monthly_fee_usd']}; APR={row['apr_pct']}; source: {row['source']}")
    return "\n".join(lines)


def _financial(period: str) -> dict | None:
    return next((row for row in load_facts()["financials"] if row["period"].lower() == period.lower()), None)


def lookup_financial_metric(metric: str, period: str) -> str:
    row = _financial(period)
    if row is None:
        return f"No financial row exists for {period}."
    aliases = {"revenue": "revenue_million_usd", "net income": "net_income_million_usd", "deposits": "deposits_million_usd", "loans": "loans_million_usd", "nim": "net_interest_margin_pct", "charge offs": "charge_off_rate_pct"}
    key = aliases.get(metric.lower(), metric)
    if key not in row:
        return f"The dataset does not contain a financial metric called {metric}."
    return f"{metric} for {period}: {row[key]}. Source: {row['source']}"


def compare_financial_metric(metric: str, from_period: str, to_period: str) -> str:
    left = _financial(from_period)
    right = _financial(to_period)
    if left is None or right is None:
        return "Both periods must be present in the financial dataset."
    aliases = {"revenue": "revenue_million_usd", "net income": "net_income_million_usd", "deposits": "deposits_million_usd", "loans": "loans_million_usd"}
    key = aliases.get(metric.lower(), metric)
    if key not in left or key not in right:
        return f"The dataset does not contain a comparable metric called {metric}."
    change = right[key] - left[key]
    percent = change / left[key] * 100
    return f"{metric} changed from {left[key]} in {from_period} to {right[key]} in {to_period}: {change:+.1f} ({percent:+.1f}%)."


def operating_margin(period: str) -> str:
    row = _financial(period)
    if row is None:
        return f"No financial row exists for {period}."
    margin = row["net_income_million_usd"] / row["revenue_million_usd"] * 100
    return f"Net-income margin for {period}: {margin:.1f}% (net income ${row['net_income_million_usd']}m / revenue ${row['revenue_million_usd']}m)."


def lookup_product_policy(product: str) -> str:
    row = next((item for item in load_facts()["policies"] if item["product"].lower() == product.lower()), None)
    if row is None:
        return f"No product policy exists for {product}."
    return json.dumps(row)


def lookup_customer(customer_id: str) -> str:
    row = next((item for item in load_facts()["customers"] if item["customer_id"].lower() == customer_id.lower()), None)
    if row is None:
        return f"No customer record exists for {customer_id}."
    return json.dumps(row)


def retention_risk(customer_id: str) -> str:
    row = next((item for item in load_facts()["customers"] if item["customer_id"].lower() == customer_id.lower()), None)
    if row is None:
        return f"No customer record exists for {customer_id}."
    score = 0
    reasons = []
    if row["days_since_login"] > 30:
        score += 2
        reasons.append("no recent login")
    elif row["days_since_login"] > 14:
        score += 1
        reasons.append("declining engagement")
    if row["support_tickets_90d"] >= 3:
        score += 2
        reasons.append("several recent support tickets")
    if row["missed_payments_12m"] > 0:
        score += 2
        reasons.append("missed payment history")
    label = "high" if score >= 4 else "medium" if score >= 2 else "low"
    return f"Illustrative retention risk for {customer_id}: {label} ({score}/6). Reasons: {', '.join(reasons) or 'no strong risk signal in this sample'}. This is a teaching rule, not a trained prediction model."
