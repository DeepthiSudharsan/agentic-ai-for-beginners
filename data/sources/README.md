# Northstar source pack

These are the source artifacts for the course. `data/finance_facts.json` is a small normalized teaching index; it is deliberately not the evidence layer.

| Source | Format | Use it to teach |
| --- | --- | --- |
| `northstar_investor_brief.pdf` | PDF | page-aware financial QA and citation |
| `northstar_customer_retention_sample.xlsx` | Excel workbook | structured customer lookup and retention analysis |
| `northstar_product_guide.docx` | Word document | policy/document lookup and missing-field handling |
| `financials.csv` | CSV | simple tabular inspection and data loading |
| `customers.csv` | CSV | a transparent view of the customer sample |
| `product_policies.md` | Markdown | readable policy source for beginners |

The PDF, workbook, and Word document are intentionally small but formatted artifacts. Students should open them and compare their content with the tool outputs and the normalized JSON. The PDF has a summary page plus one KPI table per quarter. Customer citations use the stable `customer_id` rather than a fragile spreadsheet row number.
