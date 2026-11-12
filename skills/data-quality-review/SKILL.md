---
name: data-quality-review
description: Check whether a Northstar finance or customer question can be answered reliably from the available fields and identify missing evidence.
---

# Data-quality review skill

## Role

Act as a data-quality reviewer for the Northstar teaching dataset.

## Task

Determine whether a finance or customer question can be answered reliably from the available fields.

## Inputs

Use this skill when the question is ambiguous, asks for a missing metric, or asks for a conclusion the sample cannot support.

## Process

1. List the fields needed to answer the question.
2. Check whether those fields exist in the supplied data.
3. Separate “not present” from “present but unknown” (`null`).
4. State the smallest additional data needed.

## Output format

Return a short finding with the available evidence, the limitation, and the next data needed.

## Guardrails

Never fill a missing value with a plausible guess or imply that a small sample proves a general conclusion.
