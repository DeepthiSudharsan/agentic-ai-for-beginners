---
name: product-policy
description: Answer questions about Northstar account, card, and loan fees, APRs, deposits, and product-policy sources.
---

# Product policy skill

Use this skill for product comparisons, fees, APRs, opening deposits, or “which product” questions. The evidence is in `data/sources/northstar_product_guide.docx` and the readable teaching copy is `data/sources/product_policies.md`.

Procedure:

1. Find the exact product in the supplied policy data.
2. Quote only the fields present in the policy record.
3. Include the policy source.
4. Do not infer eligibility, approval, affordability, or suitability from the policy table.
5. If a field is `null`, say that the dataset does not provide that value.
