from __future__ import annotations

import csv
import json
import re
from pathlib import Path

DATA_FILE = Path(__file__).parents[1] / "data" / "finance_facts.json"
SOURCES_DIR = DATA_FILE.parent / "sources"
FINANCIALS_CSV = SOURCES_DIR / "financials.csv"
FINANCIALS_PDF = SOURCES_DIR / "northstar_investor_brief.pdf"
CUSTOMERS_CSV = SOURCES_DIR / "customers.csv"
CUSTOMERS_XLSX = SOURCES_DIR / "northstar_customer_retention_sample.xlsx"
POLICIES_DOCX = SOURCES_DIR / "northstar_product_guide.docx"
POLICIES_MD = SOURCES_DIR / "product_policies.md"


def load_facts() -> dict:
    """Load the small normalized index: company name and known periods."""
    return json.loads(DATA_FILE.read_text())


def _financial_source(period: str) -> str:
    page = {"Q1 2024": 3, "Q2 2024": 4, "Q3 2024": 5, "Q4 2024": 6}.get(period, "?")
    return f"data/sources/northstar_investor_brief.pdf#page={page}"


def _customer_source(customer_id: str) -> str:
    return f"data/sources/northstar_customer_retention_sample.xlsx#Customers!customer_id={customer_id}"


def _policy_source() -> str:
    return "data/sources/northstar_product_guide.docx#Product Policies"


def _policy_mirror_source() -> str:
    return "data/sources/product_policies.md#Product Policies"


def _financial_from_csv(period: str) -> dict | None:
    """Read structured financial comparisons from the CSV source."""
    with FINANCIALS_CSV.open(newline="") as file:
        for row in csv.DictReader(file):
            if row["period"].lower() == period.lower():
                return {key: (value if key == "period" else float(value)) for key, value in row.items()}
    return None


def _financial_from_pdf(period: str) -> dict | None:
    """Read one quarterly page from the PDF source document."""
    from pypdf import PdfReader

    page_number = {"Q1 2024": 3, "Q2 2024": 4, "Q3 2024": 5, "Q4 2024": 6}.get(period)
    if page_number is None:
        return None
    text = PdfReader(str(FINANCIALS_PDF)).pages[page_number - 1].extract_text() or ""

    def number(label: str, suffix: str) -> float:
        match = re.search(rf"{re.escape(label)}\s*\$?\s*([0-9]+(?:\.[0-9]+)?)\s*{re.escape(suffix)}", text, re.IGNORECASE)
        if not match:
            raise ValueError(f"Could not find {label} on the PDF page for {period}.")
        return float(match.group(1))

    return {
        "period": period,
        "revenue_million_usd": number("Revenue", "m"),
        "net_income_million_usd": number("Net income", "m"),
        "deposits_million_usd": number("Deposits", "m"),
        "loans_million_usd": number("Loans", "m"),
        "net_interest_margin_pct": number("Net interest margin", "%"),
        "charge_off_rate_pct": number("Charge-off rate", "%"),
    }


def _customers_from_csv() -> list[dict]:
    """Read the raw customer sample from CSV."""
    with CUSTOMERS_CSV.open(newline="") as file:
        rows = []
        for row in csv.DictReader(file):
            rows.append({
                "customer_id": row["customer_id"],
                "segment": row["segment"],
                "tenure_years": int(row["tenure_years"]),
                "products": row["products"].split("|"),
                "monthly_card_spend_usd": float(row["monthly_card_spend_usd"]),
                "support_tickets_90d": int(row["support_tickets_90d"]),
                "days_since_login": int(row["days_since_login"]),
                "missed_payments_12m": int(row["missed_payments_12m"]),
                "balance_usd": float(row["balance_usd"]),
            })
        return rows


def _customers_from_xlsx() -> list[dict]:
    """Read the customer workbook, locating its formatted header row."""
    from openpyxl import load_workbook

    workbook = load_workbook(CUSTOMERS_XLSX, read_only=True, data_only=True)
    sheet = workbook["Customers"]
    rows = list(sheet.iter_rows(values_only=True))
    header_index = next(index for index, row in enumerate(rows) if row and row[0] == "Customer ID")
    headers = [str(value) for value in rows[header_index]]
    result = []
    for values in rows[header_index + 1:]:
        if not values or values[0] is None:
            continue
        row = dict(zip(headers, values))
        result.append({
            "customer_id": str(row["Customer ID"]),
            "segment": str(row["Segment"]),
            "tenure_years": int(row["Tenure (years)"]),
            "products": str(row["Products"]).split(" | "),
            "monthly_card_spend_usd": float(row["Monthly card spend (USD)"]),
            "support_tickets_90d": int(row["Support tickets (90d)"]),
            "days_since_login": int(row["Days since login"]),
            "missed_payments_12m": int(row["Missed payments (12m)"]),
            "balance_usd": float(row["Balance (USD)"]),
        })
    workbook.close()
    return result


def _policies_from_docx() -> list[dict]:
    """Read product policy sentences from the Word source document."""
    from docx import Document

    policies = []
    for paragraph in Document(POLICIES_DOCX).paragraphs:
        text = paragraph.text.strip()
        if "— annual fee" not in text:
            continue
        product, details = text.split("—", 1)
        annual = re.search(r"annual fee \$([0-9]+)", details)
        monthly = re.search(r"monthly fee \$([0-9]+)", details)
        apr = re.search(r"APR: ([0-9.]+)%", details)
        deposit = re.search(r"opening deposit: \$([0-9]+)", details)
        policies.append({
            "product": product.strip(),
            "annual_fee_usd": annual.group(1) if annual else "0",
            "monthly_fee_usd": monthly.group(1) if monthly else "0",
            "apr_pct": apr.group(1) if apr else "Not applicable",
            "minimum_opening_deposit_usd": deposit.group(1) if deposit else "Not applicable",
        })
    return policies


def _policies_from_markdown() -> list[dict]:
    """Read the beginner-friendly Markdown mirror of the Word policy source."""
    policies = []
    for line in POLICIES_MD.read_text().splitlines():
        if not line.startswith("|") or line.startswith("| Product") or line.startswith("|---"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != 5:
            continue
        product, annual, monthly, apr, deposit = cells
        policies.append({
            "product": product,
            "annual_fee_usd": annual.replace("$", ""),
            "monthly_fee_usd": monthly.replace("$", ""),
            "apr_pct": apr.replace("%", "") if apr != "Not applicable" else apr,
            "minimum_opening_deposit_usd": deposit.replace("$", "") if deposit != "Not applicable" else deposit,
        })
    return policies


def facts_as_text() -> str:
    """Build prompt context from the actual PDF, CSV, XLSX, and DOCX sources."""
    data = load_facts()
    lines = [f"Company: {data['company']}", "\nQuarterly financials from the PDF:"]
    for period in [row["period"] for row in data["financials"]]:
        row = _financial_from_pdf(period)
        lines.append(f"{period}: revenue ${row['revenue_million_usd']}m; net income ${row['net_income_million_usd']}m; deposits ${row['deposits_million_usd']}m; loans ${row['loans_million_usd']}m; NIM {row['net_interest_margin_pct']}%; charge-off rate {row['charge_off_rate_pct']}%; source: {_financial_source(period)}")
    lines.append("\nCustomer sample from CSV:")
    for row in _customers_from_csv():
        lines.append(f"{row['customer_id']}: {row['segment']}; products={', '.join(row['products'])}; login {row['days_since_login']} days ago; tickets last 90d={row['support_tickets_90d']}; missed payments={row['missed_payments_12m']}; balance=${row['balance_usd']}; source: {_customer_source(row['customer_id'])}")
    lines.append("\nProduct policies from DOCX, cross-checked against Markdown:")
    for row in _policies_from_docx():
        lines.append(f"{row['product']}: annual fee=${row['annual_fee_usd']}; monthly fee=${row['monthly_fee_usd']}; APR={row['apr_pct']}; sources: {_policy_source()}, {_policy_mirror_source()}")
    return "\n".join(lines)


def lookup_financial_metric(metric: str, period: str) -> str:
    row = _financial_from_pdf(period)
    if row is None:
        return f"No financial row exists for {period}."
    aliases = {"revenue": "revenue_million_usd", "net income": "net_income_million_usd", "deposits": "deposits_million_usd", "loans": "loans_million_usd", "nim": "net_interest_margin_pct", "charge offs": "charge_off_rate_pct"}
    key = aliases.get(metric.lower(), metric)
    if key not in row:
        return f"The PDF does not contain a financial metric called {metric}."
    return f"{metric} for {period}: {row[key]}. Source: {_financial_source(period)}"


def compare_financial_metric(metric: str, from_period: str, to_period: str) -> str:
    left = _financial_from_csv(from_period)
    right = _financial_from_csv(to_period)
    if left is None or right is None:
        return "Both periods must be present in the financial CSV."
    aliases = {"revenue": "revenue_million_usd", "net income": "net_income_million_usd", "deposits": "deposits_million_usd", "loans": "loans_million_usd"}
    key = aliases.get(metric.lower(), metric)
    if key not in left or key not in right:
        return f"The financial CSV does not contain a comparable metric called {metric}."
    change = right[key] - left[key]
    percent = change / left[key] * 100
    return f"{metric} changed from {left[key]} in {from_period} to {right[key]} in {to_period}: {change:+.1f} ({percent:+.1f}%). Sources: {_financial_source(from_period)}, {_financial_source(to_period)}"


def operating_margin(period: str) -> str:
    row = _financial_from_csv(period)
    if row is None:
        return f"No financial row exists for {period}."
    margin = row["net_income_million_usd"] / row["revenue_million_usd"] * 100
    return f"Net-income margin for {period}: {margin:.1f}% (net income ${row['net_income_million_usd']}m / revenue ${row['revenue_million_usd']}m). Source: {_financial_source(period)}"


def lookup_product_policy(product: str) -> str:
    docx_row = next((row for row in _policies_from_docx() if row["product"].lower() == product.lower()), None)
    markdown_row = next((row for row in _policies_from_markdown() if row["product"].lower() == product.lower()), None)
    if docx_row and markdown_row:
        if docx_row != markdown_row:
            return f"The Word and Markdown policy sources disagree for {product}; review both before answering."
        docx_row["sources"] = [_policy_source(), _policy_mirror_source()]
        return json.dumps(docx_row)
    return f"No product policy exists for {product}."


def lookup_customer(customer_id: str) -> str:
    for row in _customers_from_xlsx():
        if row["customer_id"].lower() == customer_id.lower():
            row["source"] = _customer_source(customer_id)
            return json.dumps(row)
    return f"No customer record exists for {customer_id}."


def retention_risk(customer_id: str) -> str:
    row = next((item for item in _customers_from_csv() if item["customer_id"].lower() == customer_id.lower()), None)
    if row is None:
        return f"No customer record exists for {customer_id}."
    score, reasons = _retention_score(row)
    label = "high" if score >= 4 else "medium" if score >= 2 else "low"
    return f"Illustrative retention risk for {customer_id}: {label} ({score}/6). Reasons: {', '.join(reasons) or 'no strong risk signal in this sample'}. Source: {_customer_source(customer_id)}. This is a teaching rule, not a trained prediction model."


def _retention_score(row: dict) -> tuple[int, list[str]]:
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
    return score, reasons


def high_retention_risk_customers(_unused_customer_id: str = "") -> str:
    """List every sample customer whose transparent teaching score is high."""
    high = []
    for row in _customers_from_csv():
        score, reasons = _retention_score(row)
        if score >= 4:
            high.append(f"{row['customer_id']} ({score}/6: {', '.join(reasons)})")
    return "High illustrative retention-risk customers: " + "; ".join(high) + ". Source: data/sources/customers.csv. This is a teaching rule, not a trained prediction model."
