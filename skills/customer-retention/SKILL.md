---
name: customer-retention
description: Investigate a Northstar customer’s engagement and illustrative retention risk without pretending the rule is a trained churn model.
---

# Customer retention skill

Use this skill for customer IDs, engagement, support tickets, missed payments, balances, products, or retention questions. The evidence is in `data/sources/northstar_customer_retention_sample.xlsx` and the inspectable CSV copy is `data/sources/customers.csv`.

Procedure:

1. Confirm the customer ID with the customer lookup tool.
2. Use the retention-risk tool when the user asks for a risk assessment.
3. Report the observable signals behind the result.
4. Call the result an illustrative teaching score, not a prediction or credit decision.
5. Avoid recommending denial of service, pricing changes, or other consequential action from this tiny sample.
6. Say when the customer ID is not present.
