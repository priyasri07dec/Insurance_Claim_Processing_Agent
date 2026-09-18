from typing import TypedDict
import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt
from langgraph.checkpoint.memory import MemorySaver

# LOAD ENVIRONMENT VARIABLES

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY not found. Please check your .env file."
    )

# CREATE GEMINI LLM

llm = ChatGoogleGenerativeAI(
    model="gemini-3.6-flash",
    temperature=0,
    google_api_key=api_key
)

# DEFINE THE CLAIM STATE

class ClaimState(TypedDict, total=False):

    # Claim information

    claim_id: str
    claimant_name: str
    policy_number: str
    claim_amount: float
    claim_date: str
    policy_expiry_date: str

    # Documents

    submitted_documents: list[str]
    required_documents: list[str]

    # Document Verification Agent results

    document_status: str
    missing_documents: list[str]

    # Eligibility Check Agent results

    eligibility_status: str
    eligibility_reason: str

    # Fraud Detection Agent results

    fraud_status: str
    fraud_indicators: list[str]

    # Final decision

    final_decision: str

    # Gemini Claim Summary Agent result

    claim_summary: str

# DOCUMENT VERIFICATION AGENT

def document_verification_agent(state: ClaimState):

    required_documents = state.get(
        "required_documents",
        []
    )

    submitted_documents = state.get(
        "submitted_documents",
        []
    )

    missing_documents = [
        document
        for document in required_documents
        if document not in submitted_documents
    ]

    if missing_documents:

        document_status = "INCOMPLETE"

    else:

        document_status = "COMPLETE"

    return {
        "document_status": document_status,
        "missing_documents": missing_documents
    }

# ELIGIBILITY CHECK AGENT

def eligibility_check_agent(state: ClaimState):

    claim_date = state.get(
        "claim_date",
        ""
    )

    policy_expiry_date = state.get(
        "policy_expiry_date",
        ""
    )

    if claim_date and policy_expiry_date:

        if claim_date <= policy_expiry_date:

            eligibility_status = "ELIGIBLE"

            eligibility_reason = (
                "Policy is active on the claim date."
            )

        else:

            eligibility_status = "INELIGIBLE"

            eligibility_reason = (
                "Policy had expired before the claim date."
            )

    else:

        eligibility_status = "UNKNOWN"

        eligibility_reason = (
            "Claim date or policy expiry date is missing."
        )

    return {
        "eligibility_status": eligibility_status,
        "eligibility_reason": eligibility_reason
    }

# FRAUD DETECTION AGENT

def fraud_detection_agent(state: ClaimState):

    claim_amount = state.get(
        "claim_amount",
        0
    )

    fraud_indicators = []

    # High-value claim threshold
    if claim_amount > 500000:

        fraud_indicators.append(
            "Claim amount exceeds the high-value threshold."
        )

    if fraud_indicators:

        fraud_status = "REVIEW_REQUIRED"

    else:

        fraud_status = "NO_MAJOR_INDICATOR"

    return {
        "fraud_status": fraud_status,
        "fraud_indicators": fraud_indicators
    }

# DECISION ROUTER

def decision_router(state: ClaimState):

    # Missing documents → Reject

    if state.get("document_status") == "INCOMPLETE":

        return "reject"

    # Policy not eligible → Reject

    if state.get("eligibility_status") == "INELIGIBLE":

        return "reject"

    # Unknown eligibility → Human Review

    if state.get("eligibility_status") == "UNKNOWN":

        return "human_review"

    # Fraud indicators → Human Review

    if state.get("fraud_status") == "REVIEW_REQUIRED":

        return "human_review"

    # Everything is valid → Auto Approve

    return "approve"

# REJECT CLAIM NODE

def reject_claim(state: ClaimState):

    return {
        "final_decision": "REJECT"
    }

# AUTO APPROVE CLAIM NODE

def approve_claim(state: ClaimState):

    return {
        "final_decision": "AUTO APPROVE"
    }

# HUMAN APPROVAL AGENT

def human_review_claim(state: ClaimState):

    # Pause the LangGraph workflow

    human_decision = interrupt({

        "message": (
            "This claim requires human review."
        ),

        "claim_id": state.get(
            "claim_id"
        ),

        "claimant_name": state.get(
            "claimant_name"
        ),

        "claim_amount": state.get(
            "claim_amount"
        ),

        "fraud_indicators": state.get(
            "fraud_indicators",
            []
        ),

        "eligibility_status": state.get(
            "eligibility_status"
        ),

        "document_status": state.get(
            "document_status"
        )
    })

    # Process human decision

    if human_decision == "APPROVE":

        final_decision = "HUMAN APPROVED"

    elif human_decision == "REJECT":

        final_decision = "HUMAN REJECTED"

    else:

        final_decision = "HUMAN DECISION INVALID"

    return {
        "final_decision": final_decision
    }

# CLAIM SUMMARY AGENT

def claim_summary_agent(state: ClaimState):

    prompt = f"""
You are an Insurance Claim Summary Agent.

Generate a concise and professional summary of the insurance
claim using ONLY the information provided below.

IMPORTANT RULES:

1. Do not invent any information.
2. Do not assume information that is not provided.
3. Do not add medical, financial, policy or fraud details
   that are not present in the input.
4. Mention the reason for the final decision when available.
5. Keep the summary factual and professional.
6. Write 3 to 5 sentences.

Claim Information
-----------------
Claim ID:
{state.get("claim_id", "Not provided")}

Claimant Name:
{state.get("claimant_name", "Not provided")}

Policy Number:
{state.get("policy_number", "Not provided")}

Claim Amount:
{state.get("claim_amount", "Not provided")}

Claim Date:
{state.get("claim_date", "Not provided")}

Policy Expiry Date:
{state.get("policy_expiry_date", "Not provided")}

Document Verification
---------------------
Document Status:
{state.get("document_status", "Not provided")}

Missing Documents:
{state.get("missing_documents", [])}

Eligibility Check
-----------------
Eligibility Status:
{state.get("eligibility_status", "Not provided")}

Eligibility Reason:
{state.get("eligibility_reason", "Not provided")}

Fraud Detection
---------------
Fraud Status:
{state.get("fraud_status", "Not provided")}

Fraud Indicators:
{state.get("fraud_indicators", [])}

Final Decision
--------------
{state.get("final_decision", "Not provided")}

Generate only the final claim summary.
"""

    try:

        response = llm.invoke(prompt)

        # Gemini may return either a string or
        # a structured list of content blocks.

        if isinstance(response.content, list):

            text_parts = []

            for item in response.content:

                if isinstance(item, dict) and item.get("type") == "text":

                    text_parts.append(
                        item.get("text", "")
                    )

            claim_summary = "\n".join(
                text_parts
            ).strip()

        else:

            claim_summary = str(
                response.content
            ).strip()


        # If Gemini returned empty content
        if not claim_summary:

            claim_summary = (
                "AI-generated claim summary is "
                "currently unavailable."
            )


        return {
            "claim_summary": claim_summary
        }


    except Exception as e:

        # Handle Gemini/API problems gracefully
        # without crashing the complete claim workflow.

        error_message = str(e)

        if (
            "429" in error_message
            or "RESOURCE_EXHAUSTED" in error_message
            or "quota" in error_message.lower()
        ):

            claim_summary = (
                "AI-generated claim summary is "
                "temporarily unavailable because "
                "the Gemini API quota has been exhausted. "
                "The claim processing decision was completed "
                "using the automated verification, eligibility "
                "and fraud checks."
            )

        else:

            claim_summary = (
                "AI-generated claim summary is "
                "temporarily unavailable due to an "
                "API connection or service issue."
            )


        return {
            "claim_summary": claim_summary
        }

# BUILD LANGGRAPH

builder = StateGraph(ClaimState)

# ADD CHECKING AGENTS

builder.add_node(
    "document_verification",
    document_verification_agent
)

builder.add_node(
    "eligibility_check",
    eligibility_check_agent
)

builder.add_node(
    "fraud_detection",
    fraud_detection_agent
)

# ADD DECISION ROUTER

builder.add_node(
    "decision_router",
    lambda state: {}
)

# ADD DECISION NODES

builder.add_node(
    "reject",
    reject_claim
)

builder.add_node(
    "approve",
    approve_claim
)

builder.add_node(
    "human_review",
    human_review_claim
)

# ADD CLAIM SUMMARY AGENT

builder.add_node(
    "claim_summary",
    claim_summary_agent
)

# PARALLEL EXECUTION

# START sends the claim to all three checking agents.

builder.add_edge(
    START,
    "document_verification"
)

builder.add_edge(
    START,
    "eligibility_check"
)

builder.add_edge(
    START,
    "fraud_detection"
)

# PARALLEL JOIN / FAN-IN

# The decision router waits for all three checking agents 
# to complete before making a routing decision.

builder.add_edge(
    [
        "document_verification",
        "eligibility_check",
        "fraud_detection"
    ],
    "decision_router"
)

# CONDITIONAL ROUTING

builder.add_conditional_edges(
    "decision_router",
    decision_router,
    {
        "reject": "reject",
        "approve": "approve",
        "human_review": "human_review"
    }
)

# CONNECT DECISION NODES TO CLAIM SUMMARY

builder.add_edge(
    "reject",
    "claim_summary"
)

builder.add_edge(
    "approve",
    "claim_summary"
)

builder.add_edge(
    "human_review",
    "claim_summary"
)

# CLAIM SUMMARY → END

builder.add_edge(
    "claim_summary",
    END
)

# CHECKPOINT MEMORY

memory = MemorySaver()

# COMPILE GRAPH

claim_graph = builder.compile(
    checkpointer=memory
)