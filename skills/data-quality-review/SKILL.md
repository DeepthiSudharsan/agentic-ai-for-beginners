---
name: data-quality-review
description: Check whether a Northstar finance or customer question can be answered reliably from the available fields and identify missing evidence.
---

# Data-quality review skill

Use this skill when the question is ambiguous, asks for a missing metric, or asks for a conclusion that the sample cannot support.

Procedure:

1. List the fields needed to answer the question.
2. Check whether those fields exist in the supplied data.
3. Separate “not present” from “present but unknown” (`null`).
4. State the smallest additional data needed.
5. Never fill a missing value with a plausible guess.
