import re
import tempfile
import time
import html
from collections import Counter

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


def latest_resume_updates(text, emails, phones, jd_text=""):
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

    jd_keywords = extract_jd_keywords(jd_text)
    if jd_keywords:
        missing_terms = [word for word in jd_keywords if word not in text_lower]
        if missing_terms:
            updates.append(
                "Align your resume with JD terms: " + ", ".join(missing_terms[:4]) + "."
            )

    if not updates:
        updates.append("Your resume looks complete. Focus on tailoring it to each role.")

    return updates[:5]


def clamp(value, low, high):
    return max(low, min(high, value))


def extract_jd_keywords(jd_text):
    if not jd_text.strip():
        return []

    words = re.findall(r"[a-zA-Z][a-zA-Z+.#-]{3,}", jd_text.lower())
    stopwords = {
        "with",
        "from",
        "that",
        "have",
        "will",
        "this",
        "your",
        "their",
        "ability",
        "years",
        "experience",
        "skills",
        "role",
        "team",
        "work",
        "using",
        "knowledge",
    }
    filtered = [word for word in words if word not in stopwords]
    return [word for word, _ in Counter(filtered).most_common(8)]


def extract_skill_insights(text, jd_text=""):
    resume_text = text.lower()
    jd_lower = jd_text.lower()
    skill_targets = [
        "python",
        "sql",
        "machine learning",
        "communication",
        "power bi",
        "excel",
        "leadership",
        "project management",
    ]

    if jd_lower.strip():
        required = [skill for skill in skill_targets if skill in jd_lower]
        skill_targets = required if required else skill_targets

    matching = [skill for skill in skill_targets if skill in resume_text]
    missing = [skill for skill in skill_targets if skill not in resume_text]
    return matching[:4], missing[:4]


def calculate_resume_scores(text, emails, phones, jd_text=""):
    text_lower = text.lower()
    jd_lower = jd_text.lower()

    # ATS score: core contact completeness + resume content depth.
    ats = 35
    if emails:
        ats += 25
    if phones:
        ats += 20
    ats += clamp(len(text) // 300, 0, 20)

    if jd_lower.strip():
        jd_keywords = extract_jd_keywords(jd_text)
        if jd_keywords:
            overlap = sum(1 for word in jd_keywords if word in text_lower)
            compatibility = clamp(int((overlap / len(jd_keywords)) * 100), 12, 98)
        else:
            compatibility = 35
    else:
        keywords = [
            "skills",
            "experience",
            "project",
            "education",
            "certification",
            "linkedin",
            "github",
        ]
        keyword_hits = sum(1 for word in keywords if word in text_lower)
        compatibility = clamp(int((keyword_hits / len(keywords)) * 100), 20, 96)

    sentences = [chunk.strip() for chunk in re.split(r"[.!?]+", text) if chunk.strip()]
    if sentences:
        avg_words = sum(len(sentence.split()) for sentence in sentences) / len(sentences)
    else:
        avg_words = 0
    readability = clamp(int(92 - abs(avg_words - 16) * 2.8), 35, 94)

    overall = round((ats + compatibility + readability) / 3)
    return ats, compatibility, readability, overall


def extract_uploaded_document_text(uploaded_doc):
    if uploaded_doc is None:
        return ""

    file_name = (uploaded_doc.name or "").lower()
    if file_name.endswith(".txt"):
        return uploaded_doc.getvalue().decode("utf-8", errors="ignore")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(uploaded_doc.getbuffer())
        temp_path = temp_file.name
    return extract_text(temp_path) or ""


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
        position: relative;
        overflow: hidden;
    }

    .dashboard-shell::before {
        content: "";
        position: absolute;
        inset: 16px 16px auto auto;
        width: 94%;
        height: 92%;
        border: 1px solid rgba(170, 182, 222, 0.35);
        border-radius: 22px;
        transform: translate(-20px, 20px);
        z-index: 0;
        pointer-events: none;
    }

    .browser-bar {
        background: #f8f9ff;
        border: 1px solid #d6dcf1;
        border-radius: 14px;
        padding: 0.35rem 0.6rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 0.75rem;
        position: relative;
        z-index: 1;
    }

    .browser-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 0.3rem;
        background: #d2d8f0;
    }

    .talk-btn {
        background: #0f1325;
        color: #ffffff;
        border-radius: 8px;
        border: 1px solid #20294f;
        padding: 0.24rem 0.55rem;
        font-size: 0.72rem;
        font-weight: 600;
    }

    .side-panel {
        background: linear-gradient(180deg, #363995 0%, #2e3284 100%);
        border-radius: 16px;
        color: #ffffff;
        padding: 1.15rem 1rem;
        min-height: 780px;
        box-shadow: 0 16px 28px rgba(45, 50, 132, 0.32);
        position: relative;
        z-index: 1;
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
        background: linear-gradient(135deg, #eef4ff 0%, #e3edff 100%);
        border: 1px solid #cfdcff;
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
        color: #24315c;
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
        background: linear-gradient(160deg, #0c2d66 0%, #08224f 100%);
        border: 2px dashed #4f75c6;
        border-radius: 12px;
        padding: 0.55rem;
        min-height: 210px;
        display: flex;
        align-items: center;
        transition: all 0.24s ease;
    }

    [data-testid="stFileUploaderDropzone"] {
        min-height: 175px;
        border-radius: 12px;
        background: linear-gradient(180deg, #123a7e 0%, #0e2f68 100%);
        border: 1px dashed #86a7ea;
        box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.05);
    }

    [data-testid="stFileUploaderDropzone"] * {
        color: #e9f1ff !important;
    }

    /* Give Browse files a contrasting accent color */
    [data-testid="stFileUploaderDropzone"] button {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%) !important;
        color: #fff8ef !important;
        border: 1px solid #f6b35a !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        box-shadow: 0 8px 16px rgba(217, 119, 6, 0.35) !important;
        transition: all 0.2s ease !important;
    }

    [data-testid="stFileUploaderDropzone"] button:hover {
        background: linear-gradient(135deg, #fbbf24 0%, #ea8f12 100%) !important;
        transform: translateY(-1px);
    }

    [data-testid="stFileUploaderDropzoneInstructions"] {
        padding-top: 0.45rem;
    }

    .upload-card {
        transition: transform 0.22s ease, box-shadow 0.22s ease;
    }

    .upload-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 14px 26px rgba(30, 36, 63, 0.11);
    }

    .upload-card:hover [data-testid="stFileUploader"] {
        border-color: #8db2ff;
        background: linear-gradient(160deg, #143874 0%, #0c2b5e 100%);
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

    .analysis-card {
        background: #ffffff;
        border: 1px solid #dfe5f3;
        border-radius: 14px;
        padding: 0.95rem;
        box-shadow: 0 10px 16px rgba(20, 28, 58, 0.06);
        margin-bottom: 0.9rem;
    }

    .panel-subtle {
        font-size: 0.75rem;
        color: #7e87a3;
        margin: 0.2rem 0 0.5rem 0;
    }

    .analysis-title {
        margin: 0;
        font-size: 1rem;
        font-weight: 700;
        color: #1f2a4a;
    }

    .candidate-box {
        margin-top: 0.65rem;
        padding: 0.7rem;
        border-radius: 10px;
        border: 1px solid #e4e9f6;
        background: #f8fafe;
    }

    .candidate-name {
        margin: 0;
        font-size: 0.96rem;
        font-weight: 700;
    }

    .candidate-meta {
        margin: 0.2rem 0 0 0;
        font-size: 0.8rem;
        color: #6f7897;
    }

    .preview-snippet {
        margin-top: 0.7rem;
        border: 1px solid #e6ebf8;
        border-radius: 10px;
        background: #fbfcff;
        padding: 0.7rem;
        color: #5b6484;
        font-size: 0.82rem;
        line-height: 1.45;
        min-height: 128px;
    }

    .score-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(80px, 1fr));
        gap: 0.55rem;
        margin-top: 0.65rem;
    }

    .score-chip {
        border: 1px solid #e3e8f6;
        border-radius: 11px;
        background: #f9fbff;
        padding: 0.6rem 0.45rem;
        text-align: center;
    }

    .ring {
        --pct: 0;
        --ring-color: #4f77ff;
        width: 58px;
        height: 58px;
        margin: 0 auto 0.4rem auto;
        border-radius: 50%;
        background: conic-gradient(var(--ring-color) calc(var(--pct) * 1%), #e3e9f8 0);
        display: grid;
        place-items: center;
    }

    .ring::before {
        content: "";
        width: 42px;
        height: 42px;
        border-radius: 50%;
        background: #ffffff;
        border: 1px solid #e8edfb;
    }

    .ring-value {
        margin-top: -2.1rem;
        font-size: 0.72rem;
        font-weight: 800;
        color: #253562;
    }

    .ring-label {
        margin: 0.18rem 0 0 0;
        font-size: 0.73rem;
        color: #6a7394;
        font-weight: 600;
    }

    .skill-wrap {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.55rem;
        margin-top: 0.75rem;
    }

    .skill-box {
        border: 1px solid #e4e9f7;
        border-radius: 10px;
        background: #fbfcff;
        padding: 0.58rem;
    }

    .skill-box h6 {
        margin: 0 0 0.3rem 0;
        font-size: 0.76rem;
        color: #34426f;
    }

    .skill-pill {
        display: inline-block;
        margin: 0.18rem 0.2rem 0.1rem 0;
        padding: 0.17rem 0.5rem;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 600;
        border: 1px solid #dbe4fb;
        color: #3b4a7a;
        background: #eef3ff;
    }

    .overall-note {
        margin-top: 0.7rem;
        padding: 0.58rem;
        border-radius: 10px;
        border: 1px solid #e3e8f5;
        background: #f7f9fe;
        font-size: 0.81rem;
        color: #5b6484;
    }

    .action-row {
        margin-top: 0.55rem;
        display: flex;
        gap: 0.45rem;
    }

    .action-btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border-radius: 8px;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.3rem 0.58rem;
        border: 1px solid #d4dbef;
        background: #f8faff;
        color: #3a466f;
    }

    .action-btn.primary {
        background: #2e3f79;
        border-color: #2e3f79;
        color: #ffffff;
    }

    @media (max-width: 960px) {
        .side-panel {
            min-height: auto;
            margin-bottom: 0.9rem;
        }

        .headline {
            font-size: 1.45rem;
        }

        .score-grid {
            grid-template-columns: repeat(2, minmax(80px, 1fr));
        }

        .skill-wrap {
            grid-template-columns: 1fr;
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
                        <li><span class="nav-left"><span class="nav-icon">&#128101;</span>Interview Process</span><span>&#8250;</span></li>
                        <li><span class="nav-left"><span class="nav-icon">&#128221;</span>Resume Analysis</span><span>&#8250;</span></li>
                        <li><span class="nav-left"><span class="nav-icon">&#128202;</span>Reports</span><span>&#8250;</span></li>
                        <li><span class="nav-left"><span class="nav-icon">&#128276;</span>Notifications</span><span>&#8250;</span></li>
                        <li><span class="nav-left"><span class="nav-icon">&#9881;</span>Settings</span><span>&#8250;</span></li>
                        <li><span class="nav-left"><span class="nav-icon">&#10067;</span>Support</span><span>&#8250;</span></li>
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
        <div class="browser-bar">
          <div>
            <span class="browser-dot"></span>
            <span class="browser-dot"></span>
            <span class="browser-dot"></span>
          </div>
          <button class="talk-btn">&#9679; Talk to Professionals</button>
        </div>
        <div class="top-strip">
          <p class="hello">Hello, Welcome back</p>
          <h1 class="headline">Resume Analysis Workspace</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Upload Resume",
        type=["pdf"],
        help="Only PDF files are supported",
        label_visibility="collapsed",
    )

    jd_text_input = st.text_area(
        "Paste Job Description (optional)",
        placeholder="Paste JD text here for role-specific matching...",
        height=120,
    )

    jd_file = None
    show_jd_uploader = st.checkbox("Upload JD file instead")
    if show_jd_uploader:
        jd_file = st.file_uploader(
            "Upload Job Description",
            type=["pdf", "txt"],
            help="Upload a JD in PDF or TXT format.",
            key="job_description_uploader",
        )

    if uploaded_file is not None:
        token = f"{uploaded_file.name}_{uploaded_file.size}"
        if st.session_state["uploaded_file_token"] != token:
            progress = st.progress(0, text="Uploading resume...")
            for pct in range(0, 101, 10):
                time.sleep(0.03)
                progress.progress(pct, text=f"Uploading resume... {pct}%")
            st.session_state["uploaded_file_token"] = token
        st.progress(100, text="Upload complete")

    analysis_ready = False
    text = ""
    emails = []
    phones = []
    ats_score, compatibility_score, readability_score, overall_score = (0, 0, 0, 0)
    matching_skills = ["python", "sql"]
    missing_skills = ["project management", "power bi"]
    overall_note = "Upload your resume to generate personalized recommendations and scores."
    preview_text = "Your extracted resume content will appear here once a PDF is uploaded and analyzed."
    candidate_label = "Candidate Profile"
    jd_text = ""
    jd_status = "No JD uploaded"

    if jd_text_input.strip():
        jd_status = "JD text added"
    elif jd_file is not None:
        jd_status = f"Selected: {jd_file.name}"

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

            jd_text = jd_text_input.strip()
            if not jd_text and jd_file is not None:
                jd_text = extract_uploaded_document_text(jd_file)
            jd_status = "JD uploaded" if jd_text.strip() else "No JD uploaded"

            updates = latest_resume_updates(text, emails, phones, jd_text)
            if updates != st.session_state["resume_updates"]:
                st.session_state["resume_updates"] = updates
                st.rerun()

            ats_score, compatibility_score, readability_score, overall_score = calculate_resume_scores(text, emails, phones, jd_text)
            matching_skills, missing_skills = extract_skill_insights(text, jd_text)
            overall_note = updates[0] if updates else "Your resume looks strong. Tailor it per role for better conversion."
            preview_text = (text[:540] + "...") if len(text) > 540 else text
            candidate_label = uploaded_file.name
            analysis_ready = True

            st.success("Resume uploaded and processed successfully.")
            st.markdown('<span class="status-ribbon">&#10003; Resume parsed and insights updated</span>', unsafe_allow_html=True)

            metric_col_1, metric_col_2, metric_col_3 = st.columns(3)
            metric_col_1.metric("Emails Found", len(emails))
            metric_col_2.metric("Phone Numbers Found", len(phones))
            metric_col_3.metric("JD Match", jd_status)
        except Exception as error:
            st.error(f"Could not process this file: {error}")

    score_cards_html = f"""
    <div class=\"score-grid\">
      <div class=\"score-chip\">
        <div class=\"ring\" style=\"--pct:{ats_score}; --ring-color:#5ea4d2;\"></div>
        <div class=\"ring-value\">{ats_score}%</div>
        <p class=\"ring-label\">ATS Score</p>
      </div>
      <div class=\"score-chip\">
        <div class=\"ring\" style=\"--pct:{compatibility_score}; --ring-color:#d79615;\"></div>
        <div class=\"ring-value\">{compatibility_score}%</div>
        <p class=\"ring-label\">Compatibility</p>
      </div>
      <div class=\"score-chip\">
        <div class=\"ring\" style=\"--pct:{readability_score}; --ring-color:#2e7e88;\"></div>
        <div class=\"ring-value\">{readability_score}%</div>
        <p class=\"ring-label\">Readability</p>
      </div>
      <div class=\"score-chip\">
        <div class=\"ring\" style=\"--pct:{overall_score}; --ring-color:#3f63df;\"></div>
        <div class=\"ring-value\">{overall_score}%</div>
        <p class=\"ring-label\">Overall</p>
      </div>
    </div>
    """

    matching_html = "".join([f'<span class="skill-pill">{skill.title()}</span>' for skill in matching_skills])
    missing_html = "".join([f'<span class="skill-pill">{skill.title()}</span>' for skill in missing_skills])

    if not matching_html:
        matching_html = '<span class="skill-pill">No strong skill matches yet</span>'
    if not missing_html:
        missing_html = '<span class="skill-pill">No major missing skills found</span>'

    analysis_left, analysis_right = st.columns([1.05, 1], gap="small")

    with analysis_left:
        st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
        st.markdown('<h4 class="analysis-title">Resume Recommendation</h4>', unsafe_allow_html=True)
        safe_candidate = html.escape(candidate_label)
        safe_email = html.escape(emails[0] if emails else "No email extracted yet")
        safe_jd_status = html.escape(jd_status)
        safe_preview = html.escape(preview_text if preview_text.strip() else "No readable text extracted from this file.")
        st.markdown(
            f"""
            <div class="candidate-box">
              <p class="candidate-name">{safe_candidate}</p>
              <p class="candidate-meta">{safe_email}</p>
              <p class="candidate-meta">Job Description: {safe_jd_status}</p>
            </div>
            <div class="preview-snippet">{safe_preview}</div>
            <div class="action-row">
              <span class="action-btn">&#8682; Upload Resume</span>
              <span class="action-btn primary">&#9889; Analyze Resume</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
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

    with analysis_right:
        st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
        st.markdown('<h4 class="analysis-title">Resume Score</h4>', unsafe_allow_html=True)
        st.markdown(score_cards_html, unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="skill-wrap">
              <div class="skill-box">
                <h6>Matching Skills</h6>
                {matching_html}
              </div>
              <div class="skill-box">
                <h6>Missing Skills</h6>
                {missing_html}
              </div>
            </div>
                        <div class="overall-note">{html.escape(overall_note)}</div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    if analysis_ready:
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

st.markdown('</div>', unsafe_allow_html=True)
    
       

