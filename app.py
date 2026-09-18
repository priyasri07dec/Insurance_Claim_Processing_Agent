import os
import uuid

import streamlit as st
from langgraph.types import Command

# PAGE CONFIGURATION

st.set_page_config(
    page_title="Insurance Claim Processing Agent",
    page_icon="🏥",
    layout="wide"
)

# IMPORT LANGGRAPH AGENT

# claim_agent.py loads GEMINI_API_KEY from .env locally.
# Streamlit Cloud secrets will be configured during deployment.

from claim_agent import claim_graph

# CUSTOM CSS

st.markdown(
    """
    <style>

    .main-title {
        font-size: 38px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .subtitle {
        font-size: 17px;
        margin-bottom: 25px;
    }

    .section-title {
        font-size: 24px;
        font-weight: 600;
        margin-top: 20px;
    }

    .agent-card {
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #d9d9d9;
        margin-bottom: 10px;
    }

    .decision-box {
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        font-size: 25px;
        font-weight: 700;
        border: 1px solid #d9d9d9;
    }

    </style>
    """,
    unsafe_allow_html=True
)

# PAGE HEADER

st.markdown(
    '<div class="main-title">🏥 Insurance Claim Processing Agent</div>',
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="subtitle">
    AI-powered insurance claim processing using
    <b>LangGraph</b>, <b>Gemini</b> and <b>Streamlit</b>.
    </div>
    """,
    unsafe_allow_html=True
)

# SESSION STATE

if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

if "result" not in st.session_state:
    st.session_state.result = None

if "waiting_for_human" not in st.session_state:
    st.session_state.waiting_for_human = False

# CLAIM DETAILS

st.markdown(
    '<div class="section-title">📋 Claim Details</div>',
    unsafe_allow_html=True
)

st.caption(
    "Enter the insurance claim information below."
)

col1, col2 = st.columns(2)


with col1:

    claim_id = st.text_input(
        "Claim ID",
        placeholder="Example: CLM001"
    )

    claimant_name = st.text_input(
        "Claimant Name",
        placeholder="Enter claimant name"
    )

    policy_number = st.text_input(
        "Policy Number",
        placeholder="Example: POL1001"
    )

    claim_amount = st.number_input(
        "Claim Amount (₹)",
        min_value=0.0,
        value=0.0,
        step=10000.0
    )


with col2:

    claim_date = st.date_input(
        "Claim Date"
    )

    policy_expiry_date = st.date_input(
        "Policy Expiry Date"
    )

# SUPPORTING DOCUMENTS

st.markdown(
    '<div class="section-title">📄 Supporting Documents</div>',
    unsafe_allow_html=True
)

st.caption(
    "Upload the supporting documents submitted with the claim."
)

doc_col1, doc_col2 = st.columns(2)


with doc_col1:

    claim_form = st.file_uploader(
        "Claim Form",
        type=["pdf"],
        key="claim_form"
    )

    policy_document = st.file_uploader(
        "Policy Document",
        type=["pdf"],
        key="policy_document"
    )


with doc_col2:

    id_proof = st.file_uploader(
        "ID Proof",
        type=["pdf"],
        key="id_proof"
    )

    medical_bill = st.file_uploader(
        "Medical Bill",
        type=["pdf"],
        key="medical_bill"
    )

# SHOW UPLOADED DOCUMENT STATUS

uploaded_documents = {
    "Claim Form": claim_form,
    "Policy Document": policy_document,
    "ID Proof": id_proof,
    "Medical Bill": medical_bill
}


if any(
    document is not None
    for document in uploaded_documents.values()
):

    st.write("### Uploaded Documents")

    upload_col1, upload_col2 = st.columns(2)

    with upload_col1:

        for document_name in [
            "Claim Form",
            "Policy Document"
        ]:

            if uploaded_documents[document_name] is not None:

                st.success(
                    f"✓ {document_name}"
                )

            else:

                st.warning(
                    f"○ {document_name} not uploaded"
                )


    with upload_col2:

        for document_name in [
            "ID Proof",
            "Medical Bill"
        ]:

            if uploaded_documents[document_name] is not None:

                st.success(
                    f"✓ {document_name}"
                )

            else:

                st.warning(
                    f"○ {document_name} not uploaded"
                )

# PROCESS CLAIM BUTTON

st.divider()

process_claim = st.button(
    "🚀 Process Claim",
    type="primary",
    use_container_width=True
)

# PROCESS CLAIM

if process_claim:

    # Validate Claim ID

    if not claim_id.strip():

        st.error(
            "Please enter a Claim ID."
        )

        st.stop()

    # Validate Claimant Name

    if not claimant_name.strip():

        st.error(
            "Please enter the Claimant Name."
        )

        st.stop()

    # Validate Policy Number

    if not policy_number.strip():

        st.error(
            "Please enter the Policy Number."
        )

        st.stop()

    # Validate Claim Amount

    if claim_amount <= 0:

        st.error(
            "Please enter a claim amount greater than ₹0."
        )

        st.stop()

    # Determine Submitted Documents

    submitted_documents = []


    if claim_form is not None:

        submitted_documents.append(
            "Claim Form"
        )


    if policy_document is not None:

        submitted_documents.append(
            "Policy Document"
        )


    if id_proof is not None:

        submitted_documents.append(
            "ID Proof"
        )


    if medical_bill is not None:

        submitted_documents.append(
            "Medical Bill"
        )

    # Required Documents

    required_documents = [
        "Claim Form",
        "Policy Document",
        "ID Proof",
        "Medical Bill"
    ]

    # Create Claim State

    claim = {

        "claim_id": claim_id.strip(),

        "claimant_name": claimant_name.strip(),

        "policy_number": policy_number.strip(),

        "claim_amount": claim_amount,

        "claim_date": str(claim_date),

        "policy_expiry_date": str(policy_expiry_date),

        "required_documents": required_documents,

        "submitted_documents": submitted_documents
    }

    # Generate Unique Thread ID

    st.session_state.thread_id = (
        f"streamlit_{claim_id.strip()}_"
        f"{uuid.uuid4().hex[:8]}"
    )


    st.session_state.result = None

    st.session_state.waiting_for_human = False


    config = {

        "configurable": {

            "thread_id":
            st.session_state.thread_id

        }

    }

    # Execute LangGraph

    with st.spinner(
        "Processing claim through LangGraph agents..."
    ):

        try:

            result = claim_graph.invoke(
                claim,
                config=config
            )

        except Exception as e:

            st.error(
                "An error occurred while processing the claim."
            )

            st.exception(e)

            st.stop()

    # Check Human-in-the-Loop

    if "__interrupt__" in result:

        st.session_state.waiting_for_human = True

    else:

        st.session_state.waiting_for_human = False


    st.session_state.result = result

# DISPLAY RESULTS

if st.session_state.result is not None:

    result = st.session_state.result

    st.divider()

    st.markdown(
        '<div class="section-title">📊 Claim Processing Results</div>',
        unsafe_allow_html=True
    )

    # AGENT STATUS

    st.write("### Agent Results")


    metric1, metric2, metric3 = st.columns(3)


    with metric1:

        st.metric(
            "📄 Documents",
            result.get(
                "document_status",
                "N/A"
            )
        )


    with metric2:

        st.metric(
            "✅ Eligibility",
            result.get(
                "eligibility_status",
                "N/A"
            )
        )


    with metric3:

        st.metric(
            "🔍 Fraud Check",
            result.get(
                "fraud_status",
                "N/A"
            )
        )

    # DOCUMENT VERIFICATION

    st.write("### 📄 Document Verification")


    missing_documents = result.get(
        "missing_documents",
        []
    )


    if missing_documents:

        st.error(
            "Missing Documents: "
            + ", ".join(missing_documents)
        )

    else:

        st.success(
            "All required documents have been submitted."
        )

    # ELIGIBILITY

    st.write("### ✅ Eligibility Check")


    eligibility_status = result.get(
        "eligibility_status",
        "N/A"
    )


    eligibility_reason = result.get(
        "eligibility_reason",
        "No eligibility information available."
    )


    if eligibility_status == "ELIGIBLE":

        st.success(
            f"Policy Status: {eligibility_status}"
        )

    elif eligibility_status == "INELIGIBLE":

        st.error(
            f"Policy Status: {eligibility_status}"
        )

    else:

        st.warning(
            f"Policy Status: {eligibility_status}"
        )


    st.write(
        eligibility_reason
    )

    # FRAUD DETECTION

    st.write("### 🔍 Fraud Detection")


    fraud_status = result.get(
        "fraud_status",
        "N/A"
    )


    fraud_indicators = result.get(
        "fraud_indicators",
        []
    )


    if fraud_indicators:

        for indicator in fraud_indicators:

            st.warning(
                indicator
            )

    else:

        st.success(
            "No major fraud indicators detected."
        )

    # SHOW SUBMITTED DOCUMENTS

    st.write("### 📎 Submitted Documents")


    submitted_documents_display = []


    if claim_form is not None:

        submitted_documents_display.append(
            f"Claim Form — {claim_form.name}"
        )


    if policy_document is not None:

        submitted_documents_display.append(
            f"Policy Document — {policy_document.name}"
        )


    if id_proof is not None:

        submitted_documents_display.append(
            f"ID Proof — {id_proof.name}"
        )


    if medical_bill is not None:

        submitted_documents_display.append(
            f"Medical Bill — {medical_bill.name}"
        )


    if submitted_documents_display:

        for document in submitted_documents_display:

            st.write(
                f"✅ {document}"
            )

    else:

        st.write(
            "No documents uploaded."
        )

    # HUMAN REVIEW

    if st.session_state.waiting_for_human:

        st.divider()

        st.warning(
            "⚠️ HUMAN REVIEW REQUIRED"
        )


        st.write(
            """
            This claim has been routed to a human reviewer
            because it requires additional review before a
            final decision can be made.
            """
        )


        st.write("### 👤 Human Review")


        review_col1, review_col2 = st.columns(2)


        with review_col1:

            st.write(
                f"**Claim ID:** "
                f"{result.get('claim_id', claim_id)}"
            )

            st.write(
                f"**Claimant:** "
                f"{result.get('claimant_name', claimant_name)}"
            )

            st.write(
                f"**Claim Amount:** "
                f"₹{result.get('claim_amount', claim_amount):,.2f}"
            )


        with review_col2:

            st.write(
                f"**Document Status:** "
                f"{result.get('document_status', 'N/A')}"
            )

            st.write(
                f"**Eligibility:** "
                f"{result.get('eligibility_status', 'N/A')}"
            )

            st.write(
                f"**Fraud Status:** "
                f"{result.get('fraud_status', 'N/A')}"
            )


        st.write("### Select Human Decision")


        approve_col, reject_col = st.columns(2)


        with approve_col:

            approve = st.button(
                "✅ APPROVE CLAIM",
                use_container_width=True
            )


        with reject_col:

            reject = st.button(
                "❌ REJECT CLAIM",
                use_container_width=True
            )

        # Resume LangGraph

        if approve or reject:

            if approve:

                human_decision = "APPROVE"

            else:

                human_decision = "REJECT"


            config = {

                "configurable": {

                    "thread_id":
                    st.session_state.thread_id

                }

            }


            with st.spinner(
                "Finalizing claim decision and generating summary..."
            ):

                try:

                    final_result = claim_graph.invoke(
                        Command(
                            resume=human_decision
                        ),
                        config=config
                    )

                except Exception as e:

                    st.error(
                        "An error occurred while finalizing the claim."
                    )

                    st.exception(e)

                    st.stop()


            st.session_state.result = final_result

            st.session_state.waiting_for_human = False

            st.rerun()

    # FINAL DECISION

    if not st.session_state.waiting_for_human:

        st.divider()

        st.write("### 🎯 Final Decision")


        final_decision = result.get(
            "final_decision",
            "N/A"
        )


        if final_decision == "AUTO APPROVE":

            st.success(
                f"✅ {final_decision}"
            )


        elif final_decision == "REJECT":

            st.error(
                f"❌ {final_decision}"
            )


        elif final_decision == "HUMAN APPROVED":

            st.success(
                f"✅ {final_decision}"
            )


        elif final_decision == "HUMAN REJECTED":

            st.error(
                f"❌ {final_decision}"
            )


        else:

            st.warning(
                final_decision
            )

        # CLAIM SUMMARY

        st.write("### 📝 Claim Summary")


        claim_summary = result.get(
            "claim_summary",
            "No claim summary available."
        )


        st.info(
            claim_summary
        )

# SIDEBAR

with st.sidebar:

    st.header("🏥 About the Project")


    st.write(
        """
        This application demonstrates an
        AI-powered insurance claim processing
        workflow using LangGraph.
        """
    )


    st.divider()


    st.subheader("🤖 Processing Agents")


    st.write(
        """
        **1. Document Verification**

        Checks whether all required claim
        documents have been submitted.
        """
    )


    st.write(
        """
        **2. Eligibility Check**

        Checks whether the insurance policy
        was active on the claim date.
        """
    )


    st.write(
        """
        **3. Fraud Detection**

        Checks for configured high-value
        claim indicators.
        """
    )


    st.write(
        """
        **4. Decision Router**

        Routes the claim to automatic approval,
        rejection or human review.
        """
    )


    st.write(
        """
        **5. Human Approval**

        Allows a human reviewer to approve
        or reject claims requiring additional review.
        """
    )


    st.write(
        """
        **6. Claim Summary**

        Uses Gemini to generate a concise
        claim summary.
        """
    )


    st.divider()


    st.subheader("🛠 Technology")


    st.write(
        """
        • Python

        • LangGraph

        • LangChain

        • Gemini

        • Streamlit
        """
    )


    st.divider()


    st.caption(
        "Insurance Claim Processing Agent | "
        "GenAI & AgenticAI Project"
    )