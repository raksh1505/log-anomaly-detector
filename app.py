import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.detector import analyze_log_text
from src.explainer import explain_anomalies
from src.log_generator import generate_sample_logs

# ─── Page Config ────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="LogSense AI",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Syne:wght@700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'JetBrains Mono', monospace;
        background-color: #0d0f14;
        color: #e2e8f0;
    }
    .main { background-color: #0d0f14; }
    .stButton>button {
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700;
    }
    .metric-card {
        background: #161b27;
        border: 1px solid #2d3748;
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
    }
    .anomaly-row { background: rgba(239,68,68,0.1) !important; }
    .severity-CRITICAL { color: #ef4444; font-weight: bold; }
    .severity-HIGH     { color: #f97316; font-weight: bold; }
    .severity-MEDIUM   { color: #eab308; }
    .severity-LOW      { color: #22c55e; }
</style>
""", unsafe_allow_html=True)


# ─── Header ─────────────────────────────────────────────────────────────────

st.markdown("""
<h1 style='font-family: Syne, sans-serif; font-size: 2.4rem; font-weight: 800;
           background: linear-gradient(135deg, #6366f1, #a78bfa);
           -webkit-background-clip: text; -webkit-text-fill-color: transparent;
           margin-bottom: 0;'>
    🔍 LogSense AI
</h1>
<p style='color: #64748b; margin-top: 4px; font-size: 0.9rem;'>
    ML-powered log anomaly detection with LLM root cause explanation
</p>
<hr style='border-color: #1e2533; margin: 1rem 0;'>
""", unsafe_allow_html=True)


# ─── Sidebar ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    contamination = st.slider("Anomaly sensitivity", 0.01, 0.3, 0.1, 0.01,
                               help="% of logs expected to be anomalous")
    use_llm = st.toggle("Enable LLM Explanation", value=True,
                         help="Requires OPENAI_API_KEY in .env")
    st.markdown("---")
    st.markdown("### 📂 Input Mode")
    input_mode = st.radio("", ["Upload log file", "Paste log text", "Generate demo logs"])


# ─── Input ───────────────────────────────────────────────────────────────────

log_text = ""

if input_mode == "Upload log file":
    uploaded = st.file_uploader("Upload your .log file", type=["log", "txt"])
    if uploaded:
        log_text = uploaded.read().decode("utf-8")

elif input_mode == "Paste log text":
    log_text = st.text_area("Paste log lines here", height=200,
                             placeholder="2024-01-15 10:23:45 ERROR Connection refused...")

else:
    col1, col2 = st.columns(2)
    n_normal = col1.number_input("Normal log lines", 50, 500, 150)
    n_anomalous = col2.number_input("Anomalous lines", 5, 50, 12)
    if st.button("🎲 Generate Demo Logs"):
        log_text = generate_sample_logs(int(n_normal), int(n_anomalous))
        st.text_area("Generated logs (preview)", log_text[:2000] + "...", height=150)


# ─── Analysis ────────────────────────────────────────────────────────────────

if log_text and st.button("🚀 Analyze Logs"):
    with st.spinner("Running anomaly detection..."):
        results = analyze_log_text(log_text, contamination=contamination)

    if not results:
        st.warning("No parseable log lines found. Check your log format.")
        st.stop()

    df = pd.DataFrame(results)
    anomalies = df[df["is_anomaly"] == True]
    total = len(df)
    n_anomalies = len(anomalies)

    # ── Metrics ──────────────────────────────────────────────────────────────
    st.markdown("### 📊 Summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Log Lines", total)
    c2.metric("Anomalies Detected", n_anomalies, delta=f"{n_anomalies/total*100:.1f}%")
    c3.metric("Normal Lines", total - n_anomalies)
    c4.metric("Most Severe Level",
              anomalies["level"].value_counts().idxmax() if n_anomalies else "—")

    # ── Timeline chart ────────────────────────────────────────────────────────
    st.markdown("### 📈 Anomaly Timeline")
    df["color"] = df["is_anomaly"].map({True: "#ef4444", False: "#6366f1"})
    fig = go.Figure()
    for is_anom, label, color in [(False, "Normal", "#6366f1"), (True, "Anomaly", "#ef4444")]:
        subset = df[df["is_anomaly"] == is_anom]
        fig.add_trace(go.Scatter(
            x=list(range(len(subset))),
            y=subset["anomaly_score"],
            mode="markers",
            name=label,
            marker=dict(color=color, size=6 if not is_anom else 10, opacity=0.8)
        ))
    fig.update_layout(
        paper_bgcolor="#0d0f14", plot_bgcolor="#161b27",
        font=dict(color="#e2e8f0", family="JetBrains Mono"),
        xaxis=dict(title="Log Index", gridcolor="#1e2533"),
        yaxis=dict(title="Anomaly Score (lower = more anomalous)", gridcolor="#1e2533"),
        height=350, margin=dict(l=20, r=20, t=20, b=40)
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── LLM Explanation ──────────────────────────────────────────────────────
    if use_llm and n_anomalies > 0:
        st.markdown("### 🤖 AI Root Cause Analysis")
        with st.spinner("Consulting AI for root cause explanation..."):
            explanation = explain_anomalies(anomalies.to_dict("records"))

        severity = explanation.get("severity", "MEDIUM")
        sev_colors = {"CRITICAL": "#ef4444", "HIGH": "#f97316", "MEDIUM": "#eab308", "LOW": "#22c55e"}
        color = sev_colors.get(severity, "#6366f1")

        st.markdown(f"""
        <div style='background:#161b27; border:1px solid {color}; border-radius:12px; padding:1.5rem;'>
            <div style='display:flex; justify-content:space-between; align-items:center;'>
                <h3 style='color:{color}; margin:0; font-family:Syne,sans-serif;'>
                    ⚡ {explanation.get('root_cause', 'Unknown')}
                </h3>
                <span style='background:{color}22; color:{color}; border-radius:6px;
                             padding:4px 12px; font-size:0.8rem; font-weight:700;'>
                    {severity}
                </span>
            </div>
            <p style='color:#94a3b8; margin:1rem 0 0.5rem;'>{explanation.get('explanation', '')}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("**🔧 Suggested Fixes:**")
        for i, fix in enumerate(explanation.get("suggested_fixes", []), 1):
            st.markdown(f"`{i}.` {fix}")

    # ── Anomaly Table ─────────────────────────────────────────────────────────
    st.markdown("### 🚨 Anomalous Log Entries")
    if n_anomalies > 0:
        display_df = anomalies[["timestamp", "level", "message", "anomaly_score"]].copy()
        display_df = display_df.sort_values("anomaly_score")
        st.dataframe(display_df, use_container_width=True, height=300)
    else:
        st.success("✅ No anomalies detected in these logs!")
