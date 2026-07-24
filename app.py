import streamlit as st
import tempfile
import os
import sys
import pandas as pd
import altair as alt

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from redactor import PIIRedactor
from docx_processor import DocxProcessor
from evaluator import BenchmarkEvaluator

# 1. Page Configuration
st.set_page_config(
    page_title="SentinelPII | Enterprise Redaction Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Inject Custom Premium CSS Styling (Glassmorphism + Modern Typography + Custom Palette)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Main background */
    .stApp {
        background: radial-gradient(circle at 10% 20%, #0d1322 0%, #060911 90%);
        color: #E2E8F0;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0b0f19 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
    }

    /* Custom Header Badge */
    .header-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 14px;
        border-radius: 9999px;
        background: rgba(6, 182, 212, 0.1);
        border: 1px solid rgba(6, 182, 212, 0.3);
        color: #22D3EE;
        font-size: 0.85rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-bottom: 12px;
    }

    /* Gradient Title */
    .gradient-title {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #FFFFFF 0%, #94A3B8 50%, #38BDF8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 6px;
        letter-spacing: -0.02em;
    }

    .subtitle {
        color: #94A3B8;
        font-size: 1.05rem;
        margin-bottom: 28px;
    }

    /* Stat Cards (Glassmorphism) */
    .stat-card {
        background: rgba(15, 23, 42, 0.65);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 20px 24px;
        backdrop-filter: blur(12px);
        transition: transform 0.2s ease, border-color 0.2s ease;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
    }
    .stat-card:hover {
        border-color: rgba(56, 189, 248, 0.4);
        transform: translateY(-2px);
    }
    .stat-label {
        color: #94A3B8;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 6px;
    }
    .stat-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: #F8FAFC;
        font-family: 'JetBrains Mono', monospace;
    }
    .stat-sub {
        font-size: 0.8rem;
        color: #38BDF8;
        margin-top: 4px;
        font-weight: 500;
    }

    /* Metric Pills for Category Table */
    .category-pill {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Custom Streamlit Button Styling */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 12px 28px !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.4) !important;
        transition: all 0.2s ease !important;
    }
    div.stButton > button:first-child:hover {
        background: linear-gradient(135deg, #1D4ED8 0%, #1E40AF 100%) !important;
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.6) !important;
        transform: translateY(-1px);
    }

    /* Download Button Gradient */
    div.stDownloadButton > button {
        background: linear-gradient(135deg, #059669 0%, #10B981 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 14px 32px !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        box-shadow: 0 4px 14px rgba(16, 185, 129, 0.4) !important;
        width: 100%;
    }
    div.stDownloadButton > button:hover {
        background: linear-gradient(135deg, #047857 0%, #059669 100%) !important;
        box-shadow: 0 6px 20px rgba(16, 185, 129, 0.6) !important;
    }

    /* Hide Streamlit default branding elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# 3. Sidebar Controls
with st.sidebar:
    st.image("https://img.icons8.com/isometric/100/security-shield.png", width=64)
    st.title("SentinelPII")
    st.caption("Enterprise Redaction & Evaluation")

    st.markdown("---")
    st.subheader("⚙️ Runtime Parameters")
    seed = st.number_input("Deterministic Seed", value=42, step=1, help="Seed for consistent synthetic Faker replacements")
    evaluate_benchmark = st.checkbox("Run Benchmark Evaluation", value=True, help="Evaluate detection performance against ground truth")

    st.markdown("---")
    st.markdown("""
    **Supported Entities:**
    - 👤 Full Names
    - ✉️ Email Addresses
    - 📞 Phone Numbers
    - 🏢 Company Names
    - 📍 Physical Addresses
    - 💳 Credit Card Numbers (Luhn)
    - 🆔 SSN & Indian PAN
    - 📅 Dates of Birth
    - 🌐 IP Addresses
    - ⚖️ CIN / DIN Identifiers
    """)

# 4. Hero Title Section
st.markdown('<div class="header-badge">🛡️ Enterprise Document Privacy Engine</div>', unsafe_allow_html=True)
st.markdown('<div class="gradient-title">SentinelPII Redaction Platform</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Layout-preserving DOCX AST parser with deterministic synthetic anonymization & evaluation benchmarking.</div>', unsafe_allow_html=True)

# 5. File Upload Section
uploaded_file = st.file_uploader("Upload Microsoft Word Document (.docx)", type=["docx"])

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_in:
        tmp_in.write(uploaded_file.getvalue())
        input_path = tmp_in.name

    output_path = os.path.join(tempfile.gettempdir(), f"redacted_{uploaded_file.name}")

    if st.button("🚀 Process & Redact Document"):
        with st.spinner("Analyzing document AST, executing hybrid PII pipeline, and preserving styles..."):
            redactor = PIIRedactor(seed=seed)
            processor = DocxProcessor(redactor=redactor)
            stats = processor.process_document(input_path, output_path)

        st.session_state['redaction_stats'] = stats
        st.session_state['redactor_instance'] = redactor
        st.session_state['output_path'] = output_path
        st.session_state['filename'] = uploaded_file.name

# 6. Dashboard Display Section
if 'redaction_stats' in st.session_state:
    stats = st.session_state['redaction_stats']
    redactor = st.session_state['redactor_instance']
    output_path = st.session_state['output_path']
    filename = st.session_state['filename']

    st.markdown("<br>", unsafe_allow_html=True)

    # 4 Stat Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Total Spans Redacted</div>
            <div class="stat-value">{stats['total_redacted']:,}</div>
            <div class="stat-sub">Across document AST</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Unique Entity Map</div>
            <div class="stat-value">{stats['mapping_count']:,}</div>
            <div class="stat-sub">Deterministic mapping</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Paragraphs Processed</div>
            <div class="stat-value">{stats['total_paragraphs']:,}</div>
            <div class="stat-sub">Body & XML Runs</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Tables Processed</div>
            <div class="stat-value">{stats['total_tables']:,}</div>
            <div class="stat-sub">100% Style Preserved</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Tabs Interface
    tab1, tab2, tab3 = st.tabs(["📊 Category Analytics", "📈 Benchmark Metrics", "🔁 Entity Replacement Map"])

    with tab1:
        col_chart, col_tbl = st.columns([1.2, 1])

        df_cats = pd.DataFrame(list(stats["category_counts"].items()), columns=["Category", "Count"]).sort_values("Count", ascending=False)

        with col_chart:
            st.markdown("#### PII Distribution by Category")
            chart = alt.Chart(df_cats).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
                x=alt.X('Category:N', sort='-y', axis=alt.Axis(labelAngle=-35, labelColor='#94A3B8')),
                y=alt.Y('Count:Q', axis=alt.Axis(gridColor='rgba(255,255,255,0.05)', labelColor='#94A3B8')),
                color=alt.Color('Category:N', scale=alt.Scale(scheme='tealblues'), legend=None),
                tooltip=['Category', 'Count']
            ).properties(height=320).configure_view(strokeWidth=0)
            st.altair_chart(chart, use_container_width=True)

        with col_tbl:
            st.markdown("#### Category Breakdown Table")
            st.dataframe(df_cats, width=500, height=320)

    with tab2:
        if evaluate_benchmark:
            ann_path = os.path.join("data", "annotations.json")
            if os.path.exists(ann_path):
                evaluator = BenchmarkEvaluator(redactor=redactor)
                metrics = evaluator.evaluate(ann_path)
                overall = metrics["overall"]

                st.markdown("#### Benchmark Evaluation Metrics (data/annotations.json)")
                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    st.markdown(f'<div class="stat-card"><div class="stat-label">Precision</div><div class="stat-value" style="color:#10B981;">{overall["precision"]:.2%}</div><div class="stat-sub">TP / (TP + FP)</div></div>', unsafe_allow_html=True)
                with m2:
                    st.markdown(f'<div class="stat-card"><div class="stat-label">Recall</div><div class="stat-value" style="color:#38BDF8;">{overall["recall"]:.2%}</div><div class="stat-sub">TP / (TP + FN)</div></div>', unsafe_allow_html=True)
                with m3:
                    st.markdown(f'<div class="stat-card"><div class="stat-label">F1-Score</div><div class="stat-value" style="color:#8B5CF6;">{overall["f1_score"]:.2%}</div><div class="stat-sub">Harmonic Mean</div></div>', unsafe_allow_html=True)
                with m4:
                    st.markdown(f'<div class="stat-card"><div class="stat-label">Accuracy</div><div class="stat-value" style="color:#F59E0B;">{overall["accuracy"]:.2%}</div><div class="stat-sub">Overall Span Match</div></div>', unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("#### Per-Category Evaluation Breakdown")
                df_eval = pd.DataFrame.from_dict(metrics["by_category"], orient="index")
                st.dataframe(df_eval, width=1000)

    with tab3:
        st.markdown("#### Global Deterministic Entity Mapping Registry")
        st.caption("Every repeated instance of an original entity maps to the exact same synthetic replacement throughout the document.")
        mapping_items = list(redactor.entity_map.items())
        df_map = pd.DataFrame(mapping_items, columns=["Original Entity String", "Synthetic Replacement"]).reset_index(drop=True)
        st.dataframe(df_map, width=1000)

    st.markdown("---")

    # Download Button Section
    with open(output_path, "rb") as f_out:
        st.download_button(
            label=f"📥 Download Redacted Document ({filename})",
            data=f_out.read(),
            file_name=f"redacted_{filename}",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
