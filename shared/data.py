from __future__ import annotations

import json
import csv
from pathlib import Path

DATA_FILE = Path(__file__).parents[1] / "data" / "finance_facts.json"
SOURCES_DIR = DATA_FILE.parent / "sources"
FINANCIALS_FILE = SOURCES_DIR / "financials.csv"
CUSTOMERS_FILE = SOURCES_DIR / "customers.csv"
POLICIES_FILE = SOURCES_DIR / "product_policies.md"


def _financial_source(period: str) -> str:
    page = {"Q1 2024": 3, "Q2 2024": 4, "Q3 2024": 5, "Q4 2024": 6}.get(period, "?")
    return f"data/sources/northstar_investor_brief.pdf#page={page}"


def _customer_source(customer_id: str) -> str:
    return f"data/sources/northstar_customer_retention_sample.xlsx#Customers!customer_id={customer_id}"


def _policy_source() -> str:
    return "data/sources/northstar_product_guide.docx#Product Policies"


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
            f"charge-off rate {row['charge_off_rate_pct']}%; source: {_financial_source(row['period'])}"
        )
    lines.append("\nCustomer sample:")
    for row in data["customers"]:
        lines.append(
            f"{row['customer_id']}: {row['segment']}; products={', '.join(row['products'])}; login {row['days_since_login']} days ago; "
            f"tickets last 90d={row['support_tickets_90d']}; missed payments={row['missed_payments_12m']}; balance=${row['balance_usd']}; source: {_customer_source(row['customer_id'])}"
        )
    lines.append("\nProduct policies:")
    for row in data["policies"]:
        lines.append(f"{row['product']}: annual fee=${row['annual_fee_usd']}; monthly fee=${row['monthly_fee_usd']}; APR={row['apr_pct']}; source: {_policy_source()}")
    return "\n".join(lines)


def _financial(period: str) -> dict | None:
    with FINANCIALS_FILE.open(newline="") as file:
        for row in csv.DictReader(file):
            if row["period"].lower() == period.lower():
                for key in row:
                    if key != "period":
                        row[key] = float(row[key])
                return row
    return None


def lookup_financial_metric(metric: str, period: str) -> str:
    row = _financial(period)
    if row is None:
        return f"No financial row exists for {period}."
    aliases = {"revenue": "revenue_million_usd", "net income": "net_income_million_usd", "deposits": "deposits_million_usd", "loans": "loans_million_usd", "nim": "net_interest_margin_pct", "charge offs": "charge_off_rate_pct"}
    key = aliases.get(metric.lower(), metric)
    if key not in row:
        return f"The dataset does not contain a financial metric called {metric}."
    return f"{metric} for {period}: {row[key]}. Source: {_financial_source(period)}"


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
    return f"{metric} changed from {left[key]} in {from_period} to {right[key]} in {to_period}: {change:+.1f} ({percent:+.1f}%). Sources: {_financial_source(from_period)}, {_financial_source(to_period)}"


def operating_margin(period: str) -> str:
    row = _financial(period)
    if row is None:
        return f"No financial row exists for {period}."
    margin = row["net_income_million_usd"] / row["revenue_million_usd"] * 100
    return f"Net-income margin for {period}: {margin:.1f}% (net income ${row['net_income_million_usd']}m / revenue ${row['revenue_million_usd']}m). Source: {_financial_source(period)}"


def lookup_product_policy(product: str) -> str:
    for line in POLICIES_FILE.read_text().splitlines():
        if not line.startswith("|") or line.startswith("| ---"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if cells and cells[0].lower() == product.lower():
            row = {
                "product": cells[0],
                "annual_fee_usd": cells[1],
                "monthly_fee_usd": cells[2],
                "apr_pct": cells[3],
                "minimum_opening_deposit_usd": cells[4],
                "source": _policy_source(),
            }
            return json.dumps(row)
    if not product:
        return f"No product policy exists for {product}."
    return f"No product policy exists for {product}."


def lookup_customer(customer_id: str) -> str:
    row = _customer(customer_id)
    if row is None:
        return f"No customer record exists for {customer_id}."
    return json.dumps(row)


def retention_risk(customer_id: str) -> str:
    row = _customer(customer_id)
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
    return f"Illustrative retention risk for {customer_id}: {label} ({score}/6). Reasons: {', '.join(reasons) or 'no strong risk signal in this sample'}. Source: {_customer_source(customer_id)}. This is a teaching rule, not a trained prediction model."


def _customer(customer_id: str) -> dict | None:
    with CUSTOMERS_FILE.open(newline="") as file:
        for row in csv.DictReader(file):
            if row["customer_id"].lower() != customer_id.lower():
                continue
            return {
                "customer_id": row["customer_id"],
                "segment": row["segment"],
                "tenure_years": int(row["tenure_years"]),
                "products": row["products"].split("|"),
                "monthly_card_spend_usd": float(row["monthly_card_spend_usd"]),
                "support_tickets_90d": int(row["support_tickets_90d"]),
                "days_since_login": int(row["days_since_login"]),
                "missed_payments_12m": int(row["missed_payments_12m"]),
                "balance_usd": float(row["balance_usd"]),
                "source": _customer_source(customer_id),
            }
    return None
