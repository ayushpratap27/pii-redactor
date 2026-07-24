import streamlit as st
import tempfile
import os
import sys
import json
import pandas as pd
import docx
import altair as alt

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from redactor import PIIRedactor
from docx_processor import DocxProcessor

CACHE_FILE = os.path.join(tempfile.gettempdir(), "pii_last_session_cache.json")

# 1. Page Configuration (Light Mode, No Sidebar)
st.set_page_config(
    page_title="PII Redaction Tool",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Premium Light Mode CSS Injection
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Completely hide Streamlit sidebar, top header, Deploy button, and decoration bar */
    [data-testid="stSidebar"] {
        display: none !important;
        visibility: hidden !important;
        width: 0px !important;
    }
    header[data-testid="stHeader"] {
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
    }
    div[data-testid="stDecoration"] {
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Light Mode Main background */
    .stApp {
        background-color: #F8FAFC !important;
        color: #0F172A !important;
        padding-top: 0px !important;
    }

    /* Container padding */
    .block-container {
        padding-top: 2rem !important;
        max-width: 1200px;
    }

    .main-title {
        font-size: 2.4rem;
        font-weight: 800;
        color: #0F172A;
        margin-bottom: 6px;
        letter-spacing: -0.02em;
    }

    .main-subtitle {
        color: #475569;
        font-size: 0.95rem;
        margin-bottom: 24px;
    }

    /* 5-Step Workflow Bar (Light Mode) */
    .workflow-container {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 18px 22px;
        margin-bottom: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.03);
    }
    .workflow-title {
        font-size: 0.82rem;
        font-weight: 700;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 14px;
    }
    .workflow-steps {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 12px;
    }
    .step-item {
        display: flex;
        align-items: flex-start;
        gap: 10px;
    }
    .step-num {
        width: 28px;
        height: 28px;
        border-radius: 50%;
        background: #EEF2FF;
        color: #4F46E5;
        font-weight: 700;
        font-size: 0.82rem;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        border: 1px solid #C7D2FE;
    }
    .step-text-title {
        font-size: 0.82rem;
        font-weight: 700;
        color: #1E293B;
    }
    .step-text-sub {
        font-size: 0.72rem;
        color: #64748B;
    }

    /* Dynamic Stat Cards */
    .stat-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 20px;
        position: relative;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.03);
    }
    .stat-title {
        font-size: 0.78rem;
        font-weight: 600;
        color: #64748B;
        margin-bottom: 4px;
    }
    .stat-val {
        font-size: 2.1rem;
        font-weight: 800;
        color: #0F172A;
        font-family: 'JetBrains Mono', monospace;
        line-height: 1.2;
    }
    .stat-sub {
        font-size: 0.75rem;
        color: #4F46E5;
        margin-top: 4px;
        font-weight: 600;
    }

    /* Custom Section Card Wrapper */
    .section-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.03);
    }

    /* Custom File Dropzone */
    [data-testid="stFileUploader"] {
        background: #FFFFFF !important;
        border: 2px dashed #818CF8 !important;
        border-radius: 14px !important;
        padding: 20px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.03) !important;
    }
    [data-testid="stFileUploader"] section {
        background: #F8FAFC !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 10px !important;
    }
    [data-testid="stFileUploader"] label, 
    [data-testid="stFileUploader"] p, 
    [data-testid="stFileUploader"] span, 
    [data-testid="stFileUploader"] small {
        color: #1E293B !important;
        font-weight: 600 !important;
    }
    [data-testid="stFileUploader"] button {
        background: #4F46E5 !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: 600 !important;
    }

    /* Streamlit Dataframe Light Mode Container */
    div[data-testid="stDataFrame"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 12px !important;
        padding: 8px !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02) !important;
    }

    /* Centered Process Button */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #4F46E5 0%, #4338CA 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 14px 28px !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        box-shadow: 0 4px 14px rgba(79, 70, 229, 0.3) !important;
        width: 100%;
    }

    /* Centered Download Button */
    div.stDownloadButton > button {
        background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 16px 36px !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        box-shadow: 0 4px 14px rgba(5, 150, 105, 0.3) !important;
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Default Runtime Variables
seed = 42

# Restore session state from persistent disk cache if available
if 'redaction_stats' not in st.session_state and os.path.exists(CACHE_FILE):
    try:
        with open(CACHE_FILE, "r") as f_cache:
            cache_data = json.load(f_cache)
            if os.path.exists(cache_data.get('output_path', '')):
                st.session_state['redaction_stats'] = cache_data['redaction_stats']
                st.session_state['output_path'] = cache_data['output_path']
                st.session_state['filename'] = cache_data['filename']
                st.session_state['input_path'] = cache_data.get('input_path', '')
                
                # Restore redactor instance & mapping registry
                redactor_inst = PIIRedactor(seed=cache_data.get('seed', 42))
                redactor_inst.entity_map = cache_data.get('entity_map', {})
                st.session_state['redactor_instance'] = redactor_inst
    except Exception:
        pass

# 3. Header Title & Subtitle
st.markdown('<div class="main-title">PII Redaction Tool</div>', unsafe_allow_html=True)
st.markdown('<div class="main-subtitle">Layout-preserving DOCX AST parser with deterministic synthetic anonymization.</div>', unsafe_allow_html=True)

# 4. 5-Step Workflow Bar Component
st.markdown("""
<div class="workflow-container">
    <div class="workflow-title">Redaction Workflow Pipeline</div>
    <div class="workflow-steps">
        <div class="step-item">
            <div class="step-num">1</div>
            <div>
                <div class="step-text-title">Upload Document</div>
                <div class="step-text-sub">DOCX up to 200MB</div>
            </div>
        </div>
        <div class="step-item">
            <div class="step-num">2</div>
            <div>
                <div class="step-text-title">Parse & Detect</div>
                <div class="step-text-sub">AST parsing & PII detection</div>
            </div>
        </div>
        <div class="step-item">
            <div class="step-num">3</div>
            <div>
                <div class="step-text-title">Validate & Map</div>
                <div class="step-text-sub">Entity mapping registry</div>
            </div>
        </div>
        <div class="step-item">
            <div class="step-num">4</div>
            <div>
                <div class="step-text-title">Redact & Replace</div>
                <div class="step-text-sub">Deterministic anonymization</div>
            </div>
        </div>
        <div class="step-item">
            <div class="step-num">5</div>
            <div>
                <div class="step-text-title">Generate Output</div>
                <div class="step-text-sub">Download redacted file</div>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# 5. Clean File Upload Section
uploaded_file = st.file_uploader("Select Microsoft Word Document (.docx) to Redact", type=["docx"])

if uploaded_file is not None:
    # Save input file to persistent location
    persistent_in_dir = os.path.join(tempfile.gettempdir(), "pii_uploads")
    os.makedirs(persistent_in_dir, exist_ok=True)
    input_path = os.path.join(persistent_in_dir, uploaded_file.name)
    with open(input_path, "wb") as f_in:
        f_in.write(uploaded_file.getvalue())

    output_path = os.path.join(persistent_in_dir, f"redacted_{uploaded_file.name}")

    st.markdown("<br>", unsafe_allow_html=True)
    c_left, c_btn, c_right = st.columns([1, 1.5, 1])
    with c_btn:
        if st.button("🚀 Process & Redact Document", use_container_width=True):
            with st.spinner("Parsing document AST, detecting PII spans, and applying anonymization..."):
                redactor = PIIRedactor(seed=seed)
                processor = DocxProcessor(redactor=redactor)
                stats = processor.process_document(input_path, output_path)

            st.session_state['redaction_stats'] = stats
            st.session_state['redactor_instance'] = redactor
            st.session_state['output_path'] = output_path
            st.session_state['filename'] = uploaded_file.name
            st.session_state['input_path'] = input_path

            # Save to persistent disk cache for browser refresh survival
            try:
                cache_data = {
                    'redaction_stats': stats,
                    'output_path': output_path,
                    'filename': uploaded_file.name,
                    'input_path': input_path,
                    'seed': seed,
                    'entity_map': redactor.entity_map
                }
                with open(CACHE_FILE, "w") as f_cache:
                    json.dump(cache_data, f_cache)
            except Exception:
                pass

# 6. Streamlined Results Dashboard
if 'redaction_stats' in st.session_state:
    stats = st.session_state['redaction_stats']
    redactor = st.session_state['redactor_instance']
    output_path = st.session_state['output_path']
    filename = st.session_state['filename']

    st.markdown("<br>", unsafe_allow_html=True)

    # 4 Dynamic Stat Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-title">Total Spans Redacted</div>
            <div class="stat-val">{stats['total_redacted']:,}</div>
            <div class="stat-sub">Across Document AST</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-title">Unique Mapped Entities</div>
            <div class="stat-val">{stats['mapping_count']:,}</div>
            <div class="stat-sub">100% Deterministic</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-title">Paragraphs Processed</div>
            <div class="stat-val">{stats['total_paragraphs']:,}</div>
            <div class="stat-sub">Body & XML Runs</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-title">Tables Processed</div>
            <div class="stat-val">{stats['total_tables']:,}</div>
            <div class="stat-sub">100% Layout Intact</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Section 1: PII Entity Breakdown Chart
    df_cats = pd.DataFrame(list(stats["category_counts"].items()), columns=["Category", "Count"]).sort_values("Count", ascending=False)

    st.markdown("""
    <div class="section-card">
        <h4 style="margin-top:0; color:#0F172A; font-weight:800;">📊 PII Entity Breakdown</h4>
    """, unsafe_allow_html=True)

    chart = alt.Chart(df_cats).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
        x=alt.X('Category:N', sort='-y', axis=alt.Axis(labelAngle=0, labelColor='#334155', titleColor='#0F172A', labelFontSize=11)),
        y=alt.Y('Count:Q', axis=alt.Axis(gridColor='#E2E8F0', labelColor='#334155', titleColor='#0F172A')),
        color=alt.Color('Category:N', scale=alt.Scale(scheme='purples'), legend=None),
        tooltip=['Category', 'Count']
    ).properties(height=320, background='#FFFFFF').configure_view(strokeWidth=0)
    st.altair_chart(chart, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Section 2: Deterministic Synthetic Mapping Registry
    st.markdown("""
    <div class="section-card">
        <h4 style="margin-top:0; color:#0F172A; font-weight:800;">🔁 Deterministic Synthetic Mapping Registry</h4>
        <p style="color:#64748B; font-size:0.85rem; margin-bottom:14px;">Every repeated instance of an entity maps to the exact same synthetic replacement throughout the document.</p>
    """, unsafe_allow_html=True)
    mapping_items = list(redactor.entity_map.items())
    df_map = pd.DataFrame(mapping_items, columns=["Original Entity String", "Synthetic Replacement"]).reset_index(drop=True)
    st.dataframe(df_map, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Centered Download Button
    if os.path.exists(output_path):
        with open(output_path, "rb") as f_out:
            file_bytes = f_out.read()

        dl_left, dl_center, dl_right = st.columns([1, 2, 1])
        with dl_center:
            st.download_button(
                label="📥 Download Redacted Document",
                data=file_bytes,
                file_name=f"redacted_{filename}",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )

# 7. Footer Component
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align: center; color: #64748B; font-size: 0.8rem; border-top: 1px solid #E2E8F0; padding-top: 20px;">
    © 2025 PII Redaction & Anonymization Engine • Enterprise Edition • Secure & Compliant 🔒
</div>
""", unsafe_allow_html=True)
