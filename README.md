# Insurance Claim Processing Agent using LangGraph

![web_page](web_page.png)



## Project Overview

The **Insurance Claim Processing Agent** is an AI-powered insurance claim processing application built using **LangGraph, LangChain, Gemini, and Streamlit**.

The application processes insurance claims through multiple specialized agents. It performs document verification, eligibility checking, fraud-risk checking, decision routing, human approval when required, and AI-generated claim summarization.

The workflow uses **LangGraph** to coordinate the different processing steps and supports **parallel execution** of document verification, eligibility checking, and fraud detection.

The application also implements **Human-in-the-Loop (HITL)** processing for claims that require manual approval.

---

## Objective

The objective of this project is to build an automated insurance claim processing workflow that can:

- Verify whether the required claim documents have been submitted.
- Check whether the claim is eligible based on the claim date and policy expiry date.
- Identify claims requiring additional fraud review based on the configured high-value claim threshold.
- Automatically route claims to Approve, Reject, or Human Review.
- Pause the workflow when human approval is required.
- Allow a human reviewer to approve or reject the claim.
- Generate a concise AI-powered claim summary.
- Provide an interactive Streamlit interface for claim processing.

---

## Key Features

### 1. Document Verification

The Document Verification Agent checks whether all required documents have been submitted.

Required documents in the application include:

- Claim Form
- Policy Document
- ID Proof
- Medical Bill

The result can be:

- `COMPLETE`
- `INCOMPLETE`

If required documents are missing, the claim is routed for rejection.

> Note: The current implementation verifies document submission/presence. It does not perform OCR, authenticity verification, or detailed content validation of the uploaded PDFs.

---

### 2. Eligibility Check

The Eligibility Check Agent compares:

- Claim Date
- Policy Expiry Date

If the claim date is on or before the policy expiry date, the claim is considered eligible.

Possible results include:

- `ELIGIBLE`
- `INELIGIBLE`
- `UNKNOWN`

An expired policy results in claim rejection.

---

### 3. Fraud Detection

The Fraud Detection Agent performs a rule-based risk check using the claim amount.

The current application uses a high-value threshold of:

```text
₹500,000
