import re
import tempfile
import time

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

if "uploaded_file_token" not in st.session_state:
    st.session_state["uploaded_file_token"] = ""

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

    .nav-left {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
    }

    .nav-icon {
        width: 22px;
        height: 22px;
        border-radius: 7px;
        background: rgba(255, 255, 255, 0.12);
        border: 1px solid rgba(255, 255, 255, 0.2);
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 0.72rem;
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

    .top-strip-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.8rem;
    }

    .top-actions {
        display: flex;
        align-items: center;
        gap: 0.45rem;
    }

    .top-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 34px;
        height: 34px;
        border-radius: 10px;
        border: 1px solid #dbe4fa;
        background: #f6f9ff;
        color: #3d58be;
        font-size: 0.92rem;
        font-weight: 700;
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

    .tile-head {
        display: flex;
        align-items: center;
        gap: 0.45rem;
        margin-bottom: 0.32rem;
    }

    .tile-icon {
        width: 28px;
        height: 28px;
        border-radius: 8px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 0.85rem;
        font-weight: 700;
    }

    .tile-icon-blue {
        background: #dfe9ff;
        color: #3b57c6;
    }

    .tile-icon-white {
        background: rgba(255, 255, 255, 0.2);
        color: #ffffff;
        border: 1px solid rgba(255, 255, 255, 0.28);
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
        border: 2px dashed #b9c9f4;
        border-radius: 12px;
        padding: 0.4rem;
        transition: all 0.24s ease;
    }

    .upload-card {
        transition: transform 0.22s ease, box-shadow 0.22s ease;
    }

    .upload-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 14px 26px rgba(30, 36, 63, 0.11);
    }

    .upload-card:hover [data-testid="stFileUploader"] {
        border-color: #6d8ef0;
        background: #f4f8ff;
    }

    .upload-head {
        display: flex;
        align-items: center;
        gap: 0.55rem;
        margin-bottom: 0.35rem;
    }

    .upload-icon {
        width: 34px;
        height: 34px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1rem;
        font-weight: 800;
        color: #ffffff;
        background: linear-gradient(140deg, #4f73ef 0%, #2f56e5 100%);
        box-shadow: 0 8px 14px rgba(47, 86, 229, 0.35);
        animation: icon-float 1.9s ease-in-out infinite;
    }

    .upload-hint {
        margin: 0;
        font-size: 0.8rem;
        color: #6d7590;
    }

    @keyframes icon-float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-3px); }
        100% { transform: translateY(0px); }
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

    .result-head {
        display: flex;
        align-items: center;
        gap: 0.45rem;
        margin-bottom: 0.22rem;
    }

    .result-icon {
        width: 26px;
        height: 26px;
        border-radius: 8px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        color: #2b3b86;
        background: #e9f0ff;
        border: 1px solid #d7e3ff;
        font-size: 0.8rem;
        font-weight: 700;
    }

    .status-ribbon {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        margin-top: 0.35rem;
        padding: 0.28rem 0.55rem;
        border-radius: 999px;
        background: #ecfdf3;
        border: 1px solid #bfeace;
        color: #0f766e;
        font-size: 0.75rem;
        font-weight: 700;
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
                        <li><span class="nav-left"><span class="nav-icon">&#8962;</span>Dashboard</span><span>&#8250;</span></li>
                        <li><span class="nav-left"><span class="nav-icon">&#8682;</span>Upload Resume</span><span>&#8250;</span></li>
                        <li><span class="nav-left"><span class="nav-icon">&#9993;</span>Email Insights</span><span>&#8250;</span></li>
                        <li><span class="nav-left"><span class="nav-icon">&#9742;</span>Phone Insights</span><span>&#8250;</span></li>
                        <li><span class="nav-left"><span class="nav-icon">&#128196;</span>Preview Text</span><span>&#8250;</span></li>
                        <li><span class="nav-left"><span class="nav-icon">&#128202;</span>Reports</span><span>&#8250;</span></li>
                        <li><span class="nav-left"><span class="nav-icon">&#9881;</span>Settings</span><span>&#8250;</span></li>
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
                    <div class="top-strip-row">
                        <div>
                            <p class="hello">Hello, Welcome back</p>
                            <h1 class="headline">Your Resume Dashboard</h1>
                        </div>
                        <div class="top-actions">
                            <span class="top-badge">&#128276;</span>
                            <span class="top-badge">&#128197;</span>
                            <span class="top-badge">&#128269;</span>
                        </div>
                    </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    top_card_1, top_card_2, top_card_3 = st.columns([1.3, 1, 1.05], gap="small")

    with top_card_1:
        st.markdown('<div class="dashboard-card upload-card">', unsafe_allow_html=True)
        st.markdown(
            """
            <div class="upload-head">
              <div class="upload-icon">&#8682;</div>
              <div>
                <h4 class="section-title">Upload Resume</h4>
                <p class="upload-hint">Drop your latest PDF and extract contacts instantly.</p>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        uploaded_file = st.file_uploader("Choose PDF", type=["pdf"], help="Only PDF files are supported", label_visibility="collapsed")
        st.caption("Tip: Use text-based PDFs for the best extraction quality.")

        if uploaded_file is not None:
            token = f"{uploaded_file.name}_{uploaded_file.size}"
            if st.session_state["uploaded_file_token"] != token:
                progress = st.progress(0, text="Uploading resume...")
                for pct in range(0, 101, 10):
                    time.sleep(0.03)
                    progress.progress(pct, text=f"Uploading resume... {pct}%")
                st.session_state["uploaded_file_token"] = token
            st.progress(100, text="Upload complete")

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
                            <div class="tile-head">
                                <span class="tile-icon tile-icon-blue">&#128193;</span>
                                <h5>Open Projects</h5>
                            </div>
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
                            <div class="tile-head">
                                <span class="tile-icon tile-icon-white">&#9737;</span>
                                <h5>Today's focus</h5>
                            </div>
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
            st.markdown('<span class="status-ribbon">&#10003; Resume parsed and insights updated</span>', unsafe_allow_html=True)

            metric_col_1, metric_col_2, metric_col_3 = st.columns(3)
            metric_col_1.metric("Emails Found", len(emails))
            metric_col_2.metric("Phone Numbers Found", len(phones))
            metric_col_3.metric("Text Preview", "Ready")

            result_col_1, result_col_2 = st.columns(2, gap="small")

            with result_col_1:
                st.markdown(
                    '<div class="dashboard-card"><div class="result-head"><span class="result-icon">&#9993;</span><h4 class="section-title">Email Addresses</h4></div>',
                    unsafe_allow_html=True,
                )
                if emails:
                    st.markdown("".join([f'<span class="chip">{email}</span>' for email in emails]), unsafe_allow_html=True)
                else:
                    st.markdown('<p class="empty-note">No email address found.</p>', unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with result_col_2:
                st.markdown(
                    '<div class="dashboard-card"><div class="result-head"><span class="result-icon">&#9742;</span><h4 class="section-title">Phone Numbers</h4></div>',
                    unsafe_allow_html=True,
                )
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
    
       

