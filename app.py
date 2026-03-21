import re
import tempfile

import streamlit as st
from pdfminer.high_level import extract_text


def unique_keep_order(items):
    seen = set()
    ordered = []
    for item in items:
        value = item.strip()
        if value and value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


st.set_page_config(page_title="AI Resume Analyzer", layout="wide")

st.markdown(
    """
    <style>
    :root {
        --bg-soft: #f3f7f5;
        --card: #ffffff;
        --text: #1d2b2a;
        --muted: #5f6f6e;
        --accent: #0f766e;
        --accent-2: #f59e0b;
        --border: #dbe7e4;
    }

    .stApp {
        background: radial-gradient(circle at top right, #ffe9c7 0%, #f3f7f5 45%);
    }

    .hero {
        background: linear-gradient(135deg, #0f766e 0%, #115e59 100%);
        color: #ffffff;
        border-radius: 18px;
        padding: 1.2rem 1.4rem;
        margin-bottom: 1rem;
        box-shadow: 0 8px 24px rgba(17, 94, 89, 0.25);
    }

    .hero p {
        margin: 0.35rem 0 0 0;
        color: #d8f5f2;
    }

    .soft-card {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 1rem;
        box-shadow: 0 8px 18px rgba(29, 43, 42, 0.05);
        margin-bottom: 0.9rem;
    }

    .chip {
        display: inline-block;
        background: #ecfdf5;
        color: #065f46;
        border: 1px solid #a7f3d0;
        border-radius: 999px;
        padding: 0.2rem 0.65rem;
        margin: 0.2rem 0.25rem 0.1rem 0;
        font-size: 0.85rem;
        font-weight: 600;
    }

    .empty-note {
        color: var(--muted);
        font-style: italic;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <h2 style="margin:0;">AI Resume Analyzer</h2>
      <p>Upload your resume PDF and get quick extracted contact details.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

left_col, right_col = st.columns([1.1, 1])

with left_col:
    st.markdown('<div class="soft-card">', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload resume", type=["pdf"], help="Only PDF files are supported")
    st.caption("Tip: Upload a clean text-based resume PDF for better extraction.")
    st.markdown("</div>", unsafe_allow_html=True)

with right_col:
    st.markdown(
        """
        <div class="soft-card">
          <h4 style="margin-top:0; margin-bottom:0.4rem; color:#1d2b2a;">What this app extracts</h4>
          <p style="margin:0; color:#5f6f6e;">Email addresses and phone numbers from your uploaded PDF.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

if uploaded_file is None:
    st.info("Please upload a resume PDF to start analysis.")
else:
    try:
        with st.spinner("Analyzing resume..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_file.write(uploaded_file.getbuffer())
                temp_path = temp_file.name

            text = extract_text(temp_path) or ""

        emails = unique_keep_order(
            re.findall(r"\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b", text)
        )
        phones = unique_keep_order(
            re.findall(r"(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{3,5}\)?[\s-]?)?\d{5}[\s-]?\d{5}", text)
        )

        st.success("Resume uploaded and processed successfully.")

        metric_col_1, metric_col_2 = st.columns(2)
        metric_col_1.metric("Emails Found", len(emails))
        metric_col_2.metric("Phone Numbers Found", len(phones))

        result_col_1, result_col_2 = st.columns(2)

        with result_col_1:
            st.markdown('<div class="soft-card"><h4 style="margin-top:0;">Email Addresses</h4>', unsafe_allow_html=True)
            if emails:
                st.markdown("".join([f'<span class="chip">{email}</span>' for email in emails]), unsafe_allow_html=True)
            else:
                st.markdown('<p class="empty-note">No email address found.</p>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with result_col_2:
            st.markdown('<div class="soft-card"><h4 style="margin-top:0;">Phone Numbers</h4>', unsafe_allow_html=True)
            if phones:
                st.markdown("".join([f'<span class="chip">{phone}</span>' for phone in phones]), unsafe_allow_html=True)
            else:
                st.markdown('<p class="empty-note">No phone number found.</p>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with st.expander("Preview extracted text"):
            st.text(text[:2500] if text else "No text could be extracted from this PDF.")
    except Exception as error:
        st.error(f"Could not process this file: {error}")



