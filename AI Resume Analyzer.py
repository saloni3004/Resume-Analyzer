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


def latest_resume_updates(text, emails, phones):
    text_lower = text.lower()
    updates = []

    if not emails:
        updates.append("Add a professional email address in the header.")
    if not phones:
        updates.append("Include an active phone number with country code.")
    if "linkedin" not in text_lower:
        updates.append("Add your LinkedIn profile URL for recruiter verification.")
    if "github" not in text_lower and "portfolio" not in text_lower:
        updates.append("Add GitHub or portfolio links to showcase real work.")
    if "skills" not in text_lower:
        updates.append("Create a clear skills section with tools and technologies.")
    if "project" not in text_lower:
        updates.append("Add 2-3 projects with outcomes and measurable impact.")
    if "experience" not in text_lower and "work" not in text_lower:
        updates.append("Include work experience bullets using action verbs.")
    if "certification" not in text_lower and "certificate" not in text_lower:
        updates.append("Mention relevant certifications to strengthen credibility.")

    if not updates:
        updates.append("Your resume looks complete. Focus on tailoring it to each role.")

    return updates[:5]


st.set_page_config(page_title="AI Resume Analyzer", layout="wide")

default_resume_updates = [
    "Keep a one-line professional summary aligned with your target role.",
    "Use measurable achievements (numbers, percentage, impact) in experience bullets.",
    "Add recent projects, tools used, and direct links where possible.",
]

if "resume_updates" not in st.session_state:
    st.session_state["resume_updates"] = default_resume_updates

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');

    :root {
        --bg: #eeeced;
        --shell: #f7f8fb;
        --nav: #32368d;
        --card: #ffffff;
        --text: #1b2340;
        --muted: #7b819c;
        --accent: #3658e6;
        --soft-blue: #edf2ff;
        --border: #e4e9f4;
    }

    .stApp {
        font-family: 'Manrope', sans-serif;
        background: radial-gradient(circle at 20% -10%, #ffffff 0%, #eeeced 60%);
        color: var(--text);
    }

    h1, h2, h3, h4, h5, h6, p, span, label, div, li {
        font-family: 'Manrope', sans-serif !important;
    }

    .dashboard-shell {
        background: var(--shell);
        border: 1px solid #e7e4e5;
        border-radius: 20px;
        padding: 1rem;
        box-shadow: 0 18px 30px rgba(22, 26, 43, 0.08);
    }

    .side-panel {
        background: linear-gradient(180deg, #363995 0%, #2e3284 100%);
        border-radius: 16px;
        color: #ffffff;
        padding: 1.15rem 1rem;
        min-height: 690px;
        box-shadow: 0 16px 28px rgba(45, 50, 132, 0.32);
    }

    .logo {
        font-size: 1.08rem;
        font-weight: 800;
        margin-bottom: 1.2rem;
        text-align: center;
        letter-spacing: 0.3px;
        opacity: 0.95;
    }

    .profile {
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 12px;
        padding: 0.8rem;
        margin-bottom: 1rem;
    }

    .profile strong {
        display: block;
        font-size: 0.95rem;
    }

    .profile span {
        font-size: 0.72rem;
        color: #d7def8;
    }

    .nav-list {
        margin: 0;
        padding: 0;
        list-style: none;
    }

    .nav-list li {
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-size: 0.86rem;
        padding: 0.62rem 0.15rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        color: #eaf0ff;
    }

    .main-panel {
        padding: 0.1rem 0.25rem;
    }

    .top-strip {
        background: #ffffff;
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 1rem 1.1rem;
        margin-bottom: 0.9rem;
    }

    .hello {
        color: var(--muted);
        font-size: 0.9rem;
        margin: 0;
    }

    .headline {
        margin: 0.12rem 0 0 0;
        font-size: 1.95rem;
        font-weight: 800;
        letter-spacing: -0.3px;
        color: var(--text);
    }

    .dashboard-card {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 0.95rem;
        box-shadow: 0 10px 18px rgba(30, 36, 63, 0.06);
        margin-bottom: 0.9rem;
    }

    .section-title {
        margin: 0;
        font-size: 1rem;
        font-weight: 700;
        color: var(--text);
    }

    .section-note {
        margin: 0.28rem 0 0 0;
        color: var(--muted);
        font-size: 0.86rem;
    }

    .feature-tile {
        background: linear-gradient(145deg, #f4f7ff 0%, #edf3ff 100%);
        border: 1px solid #dee7ff;
        border-radius: 12px;
        padding: 0.85rem;
        min-height: 104px;
    }

    .feature-tile h5 {
        margin: 0 0 0.22rem 0;
        font-size: 0.95rem;
    }

    .feature-tile p {
        margin: 0;
        color: var(--muted);
        font-size: 0.82rem;
    }

    .weather-tile {
        background: linear-gradient(135deg, #0d2f64 0%, #123d81 60%, #1a4a97 100%);
        color: #ffffff;
        border-radius: 14px;
        padding: 0.95rem;
        min-height: 104px;
    }

    .weather-tile h5 {
        margin: 0;
        font-size: 0.95rem;
    }

    .weather-tile p {
        margin: 0.2rem 0 0 0;
        color: #d6e4ff;
        font-size: 0.82rem;
    }

    .chip {
        display: inline-block;
        background: var(--soft-blue);
        color: #2b3b86;
        border: 1px solid #d7e3ff;
        border-radius: 999px;
        padding: 0.26rem 0.7rem;
        margin: 0.24rem 0.26rem 0.1rem 0;
        font-size: 0.82rem;
        font-weight: 600;
    }

    [data-testid="stFileUploader"] {
        background: #fbfcff;
        border: 1px dashed #c7d4f8;
        border-radius: 12px;
        padding: 0.32rem;
    }

    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 0.6rem 0.75rem;
    }

    [data-testid="stMetricValue"] {
        color: #2b3b86;
    }

    [data-testid="stMetricLabel"] {
        color: #6d7590;
        font-weight: 600;
    }

    .empty-note {
        color: var(--muted);
        font-style: italic;
    }

    .footer-note {
        margin-top: 0.35rem;
        font-size: 0.82rem;
        color: #7a8196;
        text-align: left;
    }

    .update-list {
        margin: 0.45rem 0 0 0;
        padding-left: 1.15rem;
    }

    .update-list li {
        margin: 0.28rem 0;
        color: #4f5878;
        font-size: 0.86rem;
        line-height: 1.45;
    }

    .orange-update-box {
        margin-top: 0.5rem;
        border: 1px solid #c76600;
        border-radius: 12px;
        background: linear-gradient(145deg, #f6a13b 0%, #d97706 100%);
        overflow: hidden;
    }

    .orange-update-box summary {
        padding: 0.72rem 0.78rem;
        cursor: pointer;
        font-size: 0.9rem;
        font-weight: 700;
        color: #fff6e8;
        list-style: none;
    }

    .orange-update-box summary::-webkit-details-marker {
        display: none;
    }

    .orange-update-box summary::after {
        content: "Click to view";
        float: right;
        font-size: 0.75rem;
        font-weight: 600;
        color: #ffe6c7;
    }

    .orange-update-box[open] summary {
        border-bottom: 1px solid #e28a1c;
        background: rgba(168, 84, 0, 0.2);
    }

    .orange-update-box[open] summary::after {
        content: "Click to hide";
    }

    .orange-update-box ul {
        margin: 0;
        padding: 0.6rem 1rem 0.75rem 1.45rem;
    }

    .orange-update-box li {
        color: #fff6e8;
        font-size: 0.84rem;
        margin: 0.25rem 0;
        line-height: 1.4;
    }

    @media (max-width: 960px) {
        .side-panel {
            min-height: auto;
            margin-bottom: 0.9rem;
        }

        .headline {
            font-size: 1.45rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="dashboard-shell">', unsafe_allow_html=True)

side_col, main_col = st.columns([0.55, 1.75], gap="large")

with side_col:
    st.markdown(
        """
        <div class="side-panel">
          <div class="logo">databerry</div>
          <div class="profile">
            <strong>Resume Admin</strong>
            <span>Analyzer workspace</span>
          </div>
          <ul class="nav-list">
            <li><span>Dashboard</span><span>&#8250;</span></li>
            <li><span>Upload Resume</span><span>&#8250;</span></li>
            <li><span>Email Insights</span><span>&#8250;</span></li>
            <li><span>Phone Insights</span><span>&#8250;</span></li>
            <li><span>Preview Text</span><span>&#8250;</span></li>
            <li><span>Reports</span><span>&#8250;</span></li>
            <li><span>Settings</span><span>&#8250;</span></li>
          </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

with main_col:
    current_updates = st.session_state["resume_updates"]
    updates_html = "".join([f"<li>{item}</li>" for item in current_updates])

    st.markdown(
        """
        <div class="top-strip">
          <p class="hello">Hello, Welcome back</p>
          <h1 class="headline">Your Resume Dashboard</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

    top_card_1, top_card_2, top_card_3 = st.columns([1.3, 1, 1.05], gap="small")

    with top_card_1:
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        st.markdown('<h4 class="section-title">Upload Resume</h4>', unsafe_allow_html=True)
        st.markdown('<p class="section-note">Drop your latest PDF and extract contacts instantly.</p>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Choose PDF", type=["pdf"], help="Only PDF files are supported", label_visibility="collapsed")
        st.caption("Tip: Use text-based PDFs for the best extraction quality.")
        st.markdown(
            f"""
            <details class="orange-update-box">
              <summary>Latest updates required in your resume</summary>
              <ul>{updates_html}</ul>
            </details>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with top_card_2:
        st.markdown(
            """
            <div class="feature-tile">
              <h5>Open Projects</h5>
              <p>3 tasks remaining</p>
              <p style="margin-top:0.5rem; font-weight:700; color:#2b3b86;">Complete extraction queue</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with top_card_3:
        st.markdown(
            """
            <div class="weather-tile">
              <h5>Today's focus</h5>
              <p>Upload and screen resumes quickly</p>
              <p style="margin-top:0.5rem; font-size:1.25rem; color:#ffffff;">Contact Ready</p>
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
            updates = latest_resume_updates(text, emails, phones)
            if updates != st.session_state["resume_updates"]:
                st.session_state["resume_updates"] = updates
                st.rerun()

            st.success("Resume uploaded and processed successfully.")

            metric_col_1, metric_col_2, metric_col_3 = st.columns(3)
            metric_col_1.metric("Emails Found", len(emails))
            metric_col_2.metric("Phone Numbers Found", len(phones))
            metric_col_3.metric("Text Preview", "Ready")

            result_col_1, result_col_2 = st.columns(2, gap="small")

            with result_col_1:
                st.markdown('<div class="dashboard-card"><h4 class="section-title">Email Addresses</h4>', unsafe_allow_html=True)
                if emails:
                    st.markdown("".join([f'<span class="chip">{email}</span>' for email in emails]), unsafe_allow_html=True)
                else:
                    st.markdown('<p class="empty-note">No email address found.</p>', unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with result_col_2:
                st.markdown('<div class="dashboard-card"><h4 class="section-title">Phone Numbers</h4>', unsafe_allow_html=True)
                if phones:
                    st.markdown("".join([f'<span class="chip">{phone}</span>' for phone in phones]), unsafe_allow_html=True)
                else:
                    st.markdown('<p class="empty-note">No phone number found.</p>', unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with st.expander("Preview extracted text"):
                st.text(text[:2500] if text else "No text could be extracted from this PDF.")

            st.markdown('<p class="footer-note">Styled as a dashboard while preserving your extraction workflow.</p>', unsafe_allow_html=True)
        except Exception as error:
            st.error(f"Could not process this file: {error}")

st.markdown('</div>', unsafe_allow_html=True)
    
       

