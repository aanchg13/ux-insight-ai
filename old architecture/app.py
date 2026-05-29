import streamlit as st
import anthropic
from dotenv import load_dotenv
import PyPDF2
import pandas as pd
import io
import json
import plotly.express as px

load_dotenv()

client = anthropic.Anthropic()

st.set_page_config(page_title="Ripple", page_icon="〰️", layout="wide")

st.markdown("""
<style>
    .ripple-hero {
        padding: 2.5rem 0 1.5rem 0;
        text-align: center;
    }
    .ripple-logo svg {
        display: block;
        margin: 0 auto 0.5rem auto;
    }
    .ripple-name {
        font-size: 3rem;
        font-weight: 600;
        color: #334155;
        letter-spacing: -1px;
        margin: 0;
        line-height: 1;
    }
    .ripple-tagline {
        font-size: 0.85rem;
        color: #64748b;
        letter-spacing: 0.05em;
        margin: 0.3rem 0 0 0;
    }
    .ripple-subline {
        font-size: 1.1rem;
        color: #475569;
        margin-top: 1rem;
    }
    .section-header {
        font-size: 1.4rem;
        font-weight: 600;
        color: #334155;
        margin-bottom: 0.25rem;
    }
    .section-divider {
        border: none;
        border-top: 1px solid #e2e8f0;
        margin: 2rem 0;
    }
    .snapshot-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        text-align: center;
    }
    .snapshot-number {
        font-size: 2.2rem;
        font-weight: 600;
        color: #0d9488;
        line-height: 1;
    }
    .snapshot-label {
        font-size: 0.8rem;
        color: #64748b;
        margin-top: 0.3rem;
        letter-spacing: 0.03em;
    }
    .upload-section {
        background: #f8fafc;
        border: 1.5px dashed #cbd5e1;
        border-radius: 16px;
        padding: 2rem 2.5rem;
        margin: 1.5rem 0;
    }
    .upload-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #334155;
        margin-bottom: 0.25rem;
    }
    .upload-subtitle {
        font-size: 0.9rem;
        color: #64748b;
        margin-bottom: 1rem;
    }
    .finding-card {
        background: #f8fafc;
        border-left: 3px solid #0d9488;
        border-radius: 0 8px 8px 0;
        padding: 0.6rem 1rem;
        margin-bottom: 0.5rem;
        font-size: 0.92rem;
        color: #334155;
    }
    .quote-block {
        border-left: 3px solid #cbd5e1;
        padding: 0.4rem 1rem;
        color: #64748b;
        font-style: italic;
        font-size: 0.9rem;
        margin: 0.4rem 0;
    }
    [data-testid="stMetric"] {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1rem;
    }
</style>
""", unsafe_allow_html=True)

WAVE_SVG = """
<svg width="80" height="40" viewBox="0 0 80 40" xmlns="http://www.w3.org/2000/svg">
  <path d="M5,20 Q17,4 29,20 Q41,36 53,20 Q65,4 75,20" fill="none" stroke="#0d9488" stroke-width="3.5" stroke-linecap="round"/>
  <path d="M5,28 Q17,12 29,28 Q41,44 53,28 Q65,12 75,28" fill="none" stroke="#0d9488" stroke-width="2.2" stroke-linecap="round" opacity="0.55"/>
  <path d="M5,35 Q17,19 29,35 Q41,51 53,35 Q65,19 75,35" fill="none" stroke="#0d9488" stroke-width="1.2" stroke-linecap="round" opacity="0.28"/>
</svg>
"""

st.markdown(f"""
<div class="ripple-hero">
    <div class="ripple-logo">{WAVE_SVG}</div>
    <p class="ripple-name">Ripple</p>
    <p class="ripple-tagline">Every user voice creates a ripple</p>
    <p class="ripple-subline">From raw interviews to research clarity — in seconds</p>
</div>
""", unsafe_allow_html=True)

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

def extract_text(file):
    if file.type == "text/plain":
        return file.read().decode("utf-8")
    elif file.type == "application/pdf":
        reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
        return "\n".join([page.extract_text() for page in reader.pages])
    elif file.type == "text/csv":
        df = pd.read_csv(file)
        return df.to_string()

def analyze_transcript(text):
    prompt = f"""You are an expert UX researcher. Analyze the following user interview transcript and extract structured insights.

Return ONLY a valid JSON object with this exact structure, no other text before or after:
{{
  "themes": [
    {{
      "name": "theme name",
      "description": "brief description",
      "quotes": ["exact quote from transcript"],
      "frequency": 1,
      "severity": "high/medium/low"
    }}
  ],
  "pain_points": ["pain point 1", "pain point 2"],
  "user_needs": ["need 1", "need 2"],
  "summary": "2-3 sentence executive summary"
}}

Transcript:
{text}"""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = message.content[0].text.strip()
    if response_text.startswith("```"):
        response_text = response_text.split("```")[1]
        if response_text.startswith("json"):
            response_text = response_text[4:]
    return json.loads(response_text.strip())

def load_sample_data():
    sample_files = ["banking_sarah.txt", "banking_marcus.txt", "banking_priya.txt"]
    texts = []
    for filename in sample_files:
        try:
            with open(filename, "r") as f:
                texts.append({"name": filename, "text": f.read()})
        except FileNotFoundError:
            st.error(f"Sample file {filename} not found")
    return texts

if "texts_to_analyze" not in st.session_state:
    st.session_state.texts_to_analyze = []

st.markdown('<div class="upload-section">', unsafe_allow_html=True)
st.markdown('<p class="upload-title">Let Your Research Speak</p>', unsafe_allow_html=True)
st.markdown('<p class="upload-subtitle">Upload interview transcripts or survey data — TXT, PDF, or CSV</p>', unsafe_allow_html=True)

uploaded_files = st.file_uploader(
    "Upload files",
    type=["txt", "pdf", "csv"],
    accept_multiple_files=True,
    label_visibility="collapsed"
)

col_space, col_btn = st.columns([4, 1])
with col_btn:
    if st.button("🧪 Try sample data", use_container_width=True):
        st.session_state.texts_to_analyze = load_sample_data()
        st.success("3 banking transcripts loaded!")

st.markdown('</div>', unsafe_allow_html=True)

if uploaded_files:
    st.session_state.texts_to_analyze = []
    for file in uploaded_files:
        text = extract_text(file)
        st.session_state.texts_to_analyze.append({"name": file.name, "text": text})

if st.session_state.texts_to_analyze:
    st.success(f"{len(st.session_state.texts_to_analyze)} file(s) ready for analysis")

    for item in st.session_state.texts_to_analyze:
        with st.expander(f"📄 {item['name']}"):
            st.text_area("Preview", item["text"][:500] + "...", height=130)

    st.markdown("<br>", unsafe_allow_html=True)
    analyze_btn = st.button("Analyze transcripts →", type="primary", use_container_width=False)

    if analyze_btn:
        with st.spinner("Ripple is reading your research..."):
            combined_text = "\n\n---NEW TRANSCRIPT---\n\n".join(
                [item["text"] for item in st.session_state.texts_to_analyze]
            )
            try:
                insights = analyze_transcript(combined_text)

                st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

                st.markdown('<p class="section-header">Research Snapshot</p>', unsafe_allow_html=True)
                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    st.markdown(f'<div class="snapshot-card"><div class="snapshot-number">{len(insights["themes"])}</div><div class="snapshot-label">Themes identified</div></div>', unsafe_allow_html=True)
                with m2:
                    st.markdown(f'<div class="snapshot-card"><div class="snapshot-number">{len(insights["pain_points"])}</div><div class="snapshot-label">Pain points</div></div>', unsafe_allow_html=True)
                with m3:
                    st.markdown(f'<div class="snapshot-card"><div class="snapshot-number">{len(insights["user_needs"])}</div><div class="snapshot-label">User needs</div></div>', unsafe_allow_html=True)
                with m4:
                    high = sum(1 for t in insights["themes"] if t["severity"].upper() == "HIGH")
                    st.markdown(f'<div class="snapshot-card"><div class="snapshot-number">{high}</div><div class="snapshot-label">High severity</div></div>', unsafe_allow_html=True)

                st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
                st.markdown('<p class="section-header">Executive Summary</p>', unsafe_allow_html=True)
                st.info(insights["summary"])

                st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
                st.markdown('<p class="section-header">Critical Findings</p>', unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Pain points**")
                    for point in insights["pain_points"]:
                        st.markdown(f'<div class="finding-card">{point}</div>', unsafe_allow_html=True)
                with col2:
                    st.markdown("**User needs**")
                    for need in insights["user_needs"]:
                        st.markdown(f'<div class="finding-card">{need}</div>', unsafe_allow_html=True)

                st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
                st.markdown('<p class="section-header">Evidence Map</p>', unsafe_allow_html=True)

                severity_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
                for theme in insights["themes"]:
                    level = theme["severity"].upper()
                    if level in severity_counts:
                        severity_counts[level] += 1

                severity_df = pd.DataFrame({
                    "Severity": list(severity_counts.keys()),
                    "Count": list(severity_counts.values())
                })

                col_chart1, col_chart2 = st.columns(2)
                with col_chart1:
                    fig1 = px.bar(
                        severity_df,
                        x="Severity", y="Count",
                        color="Severity",
                        color_discrete_map={"HIGH": "#ef4444", "MEDIUM": "#f97316", "LOW": "#22c55e"},
                        title="Themes by severity"
                    )
                    fig1.update_layout(showlegend=False, plot_bgcolor="white", paper_bgcolor="white")
                    st.plotly_chart(fig1, use_container_width=True)

                with col_chart2:
                    theme_names = [t["name"] for t in insights["themes"]]
                    theme_quotes = [len(t["quotes"]) for t in insights["themes"]]
                    fig2 = px.bar(
                        x=theme_quotes, y=theme_names,
                        orientation="h",
                        title="Theme strength by supporting quotes",
                        labels={"x": "Number of quotes", "y": "Theme"},
                        color=theme_quotes,
                        color_continuous_scale=["#22c55e", "#f97316", "#ef4444"]
                    )
                    fig2.update_layout(showlegend=False, plot_bgcolor="white", paper_bgcolor="white")
                    st.plotly_chart(fig2, use_container_width=True)

                st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
                st.markdown('<p class="section-header">Theme Deep Dive</p>', unsafe_allow_html=True)
                for theme in insights["themes"]:
                    with st.expander(f"{theme['name']} — {theme['severity'].upper()}"):
                        st.write(theme["description"])
                        if theme["quotes"]:
                            st.markdown("**Supporting quotes**")
                            for quote in theme["quotes"]:
                                st.markdown(f'<div class="quote-block">{quote}</div>', unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Something went wrong: {e}")