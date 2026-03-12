import streamlit as st
import requests
import io

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Swagger Generator",
    page_icon="📄",
    layout="wide",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Inter:wght@300;400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .main { background-color: #0f1117; }

    .stApp {
        background: linear-gradient(135deg, #0f1117 0%, #1a1d2e 100%);
    }

    h1, h2, h3 {
        font-family: 'JetBrains Mono', monospace !important;
        color: #e2e8f0 !important;
    }

    .hero-title {
        font-family: 'JetBrains Mono', monospace;
        font-size: 2.2rem;
        font-weight: 600;
        background: linear-gradient(90deg, #38bdf8, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.25rem;
    }

    .hero-subtitle {
        color: #64748b;
        font-size: 0.95rem;
        margin-bottom: 2rem;
    }

    .section-card {
        background: #1e2130;
        border: 1px solid #2d3348;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }

    .section-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        color: #38bdf8;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 0.75rem;
    }

    .pat-info {
        background: #1a2744;
        border: 1px solid #1d4ed8;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        font-size: 0.82rem;
        color: #93c5fd;
        margin-top: 0.5rem;
    }

    .yaml-output {
        background: #0d1117;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 1rem;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        color: #adbac7;
        white-space: pre-wrap;
        overflow-x: auto;
        max-height: 500px;
        overflow-y: auto;
    }

    .stButton > button {
        background: linear-gradient(135deg, #38bdf8, #818cf8) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: 600 !important;
        padding: 0.6rem 2rem !important;
        font-size: 0.9rem !important;
        transition: opacity 0.2s !important;
    }

    .stButton > button:hover {
        opacity: 0.85 !important;
    }

    .success-badge {
        display: inline-block;
        background: #14532d;
        color: #86efac;
        border: 1px solid #16a34a;
        border-radius: 20px;
        padding: 0.2rem 0.8rem;
        font-size: 0.78rem;
        font-family: 'JetBrains Mono', monospace;
    }

    .error-badge {
        display: inline-block;
        background: #450a0a;
        color: #fca5a5;
        border: 1px solid #dc2626;
        border-radius: 20px;
        padding: 0.2rem 0.8rem;
        font-size: 0.78rem;
        font-family: 'JetBrains Mono', monospace;
    }

    div[data-testid="stFileUploader"] {
        background: #161b27;
        border: 1px dashed #2d3348;
        border-radius: 8px;
        padding: 0.5rem;
    }

    .stSelectbox > div > div {
        background: #1e2130 !important;
        border-color: #2d3348 !important;
        color: #e2e8f0 !important;
    }

    .stTextInput > div > div > input {
        background: #161b27 !important;
        border-color: #2d3348 !important;
        color: #e2e8f0 !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.85rem !important;
    }

    .step-number {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 24px;
        height: 24px;
        background: linear-gradient(135deg, #38bdf8, #818cf8);
        color: white;
        border-radius: 50%;
        font-size: 0.75rem;
        font-weight: 700;
        margin-right: 0.5rem;
        font-family: 'JetBrains Mono', monospace;
    }
</style>
""", unsafe_allow_html=True)

BACKEND_URL = "http://localhost:8000"

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="hero-title">⚡ Swagger Generator</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-subtitle">Generate OpenAPI/Swagger YAML from user stories using GitHub Models AI</div>', unsafe_allow_html=True)

# ── Layout: two columns ────────────────────────────────────────────────────────
left_col, right_col = st.columns([1, 1], gap="large")

with left_col:
    # ── Step 1: Copilot Status ────────────────────────────────────────────────
    st.markdown('<div class="section-label">① Copilot CLI Status</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="pat-info">
        🤖 Authentication is handled by <b>GitHub Copilot CLI</b><br>
        Make sure you have run <code>copilot auth login</code> before starting the backend
    </div>
    """, unsafe_allow_html=True)

    if st.button("Check Copilot Status", key="validate"):
        with st.spinner("Checking..."):
            try:
                resp = requests.post(f"{BACKEND_URL}/validate-pat", timeout=15)
                result = resp.json()
                if result["valid"]:
                    st.markdown('<span class="success-badge">✓ Copilot CLI Ready</span>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<span class="error-badge">✗ {result["message"]}</span>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Could not reach backend: {e}")

    st.markdown("---")

    # ── Step 2: Model Selection ───────────────────────────────────────────────
    st.markdown('<div class="section-label">② Select Model</div>', unsafe_allow_html=True)

    try:
        models_resp = requests.get(f"{BACKEND_URL}/models", timeout=5)
        model_options = {m["name"]: m["id"] for m in models_resp.json()["models"]}
    except Exception:
        model_options = {
            "GPT-4.1 (Recommended)": "openai/gpt-4.1",
            "GPT-4o": "openai/gpt-4o",
            "Claude 3.5 Sonnet": "anthropic/claude-3-5-sonnet-latest",
        }

    selected_model_name = st.selectbox("Model", list(model_options.keys()))
    selected_model_id = model_options[selected_model_name]
    st.caption(f"Model ID: `{selected_model_id}`")

    st.markdown("---")

    # ── Step 3: Learning Examples ─────────────────────────────────────────────
    st.markdown('<div class="section-label">③ Learning Examples (Few-Shot)</div>', unsafe_allow_html=True)
    st.caption("Upload 1–3 example pairs so the AI learns your YAML structure")

    num_examples = st.radio("Number of examples", [1, 2, 3], horizontal=True)

    example_files = {}
    for i in range(1, int(num_examples) + 1):
        with st.expander(f"Example {i}", expanded=(i == 1)):
            example_files[f"story_{i}"] = st.file_uploader(
                f"User Story {i} (.txt)",
                type=["txt"],
                key=f"ex_story_{i}"
            )
            example_files[f"swagger_{i}"] = st.file_uploader(
                f"Swagger YAML {i} (.yaml / .yml)",
                type=["yaml", "yml"],
                key=f"ex_swagger_{i}"
            )

    st.markdown("---")

    # ── Step 4: Input Story ───────────────────────────────────────────────────
    st.markdown('<div class="section-label">④ New User Story (Input)</div>', unsafe_allow_html=True)
    st.caption("Upload the user story you want to generate a Swagger file for")

    input_story_file = st.file_uploader(
        "New User Story (.txt)",
        type=["txt"],
        key="input_story"
    )

    if input_story_file:
        with st.expander("Preview"):
            st.text(input_story_file.read().decode("utf-8"))
            input_story_file.seek(0)

    st.markdown("---")

    # ── Generate Button ───────────────────────────────────────────────────────
    generate_clicked = st.button("🚀 Generate Swagger YAML", use_container_width=True)

# ── Right Column: Output ───────────────────────────────────────────────────────
with right_col:
    st.markdown('<div class="section-label">⑤ Generated Output</div>', unsafe_allow_html=True)

    if generate_clicked:
        # Validation
        errors = []
        if not input_story_file:
            errors.append("Input user story is required")

        # Check at least one valid example pair
        has_example = False
        for i in range(1, int(num_examples) + 1):
            if example_files.get(f"story_{i}") and example_files.get(f"swagger_{i}"):
                has_example = True
                break
        if not has_example:
            errors.append("At least one complete example pair (story + swagger) is required")

        if errors:
            for err in errors:
                st.error(f"⚠️ {err}")
        else:
            with st.spinner("🤖 AI is generating your Swagger YAML..."):
                try:
                    files = {
                        "input_story": (
                            input_story_file.name,
                            input_story_file.read(),
                            "text/plain"
                        )
                    }
                    input_story_file.seek(0)

                    # Attach example files
                    for i in range(1, int(num_examples) + 1):
                        sf = example_files.get(f"story_{i}")
                        sw = example_files.get(f"swagger_{i}")
                        if sf and sw:
                            files[f"example_story_{i}"] = (sf.name, sf.read(), "text/plain")
                            files[f"example_swagger_{i}"] = (sw.name, sw.read(), "application/x-yaml")
                            sf.seek(0)
                            sw.seek(0)

                    data = {"model": selected_model_id}

                    response = requests.post(
                        f"{BACKEND_URL}/generate",
                        files=files,
                        data=data,
                        timeout=620,
                    )

                    if response.status_code == 200:
                        yaml_output = response.text
                        st.session_state["yaml_output"] = yaml_output
                        st.markdown('<span class="success-badge">✓ Generation Complete</span>', unsafe_allow_html=True)
                    else:
                        detail = response.json().get("detail", response.text)
                        st.error(f"Generation failed: {detail}")

                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to backend. Make sure FastAPI is running on port 8000.")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

    # Display output if available
    if "yaml_output" in st.session_state:
        yaml_output = st.session_state["yaml_output"]

        st.markdown(f'<div class="yaml-output">{yaml_output}</div>', unsafe_allow_html=True)

        st.markdown("####")

        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="⬇️ Download YAML",
                data=yaml_output,
                file_name="generated_swagger.yaml",
                mime="application/x-yaml",
                use_container_width=True,
            )
        with col2:
            if st.button("🗑️ Clear Output", use_container_width=True):
                del st.session_state["yaml_output"]
                st.rerun()

        # Stats
        lines = yaml_output.count("\n")
        chars = len(yaml_output)
        st.caption(f"📊 {lines} lines · {chars} characters · Model: `{selected_model_id}`")

    else:
        st.markdown("""
        <div style="
            border: 1px dashed #2d3348;
            border-radius: 12px;
            padding: 3rem 2rem;
            text-align: center;
            color: #475569;
            margin-top: 1rem;
        ">
            <div style="font-size: 2.5rem; margin-bottom: 1rem;">📋</div>
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.85rem;">
                Your generated Swagger YAML will appear here
            </div>
            <div style="font-size: 0.78rem; margin-top: 0.5rem; color: #334155;">
                Fill in the form on the left and click Generate
            </div>
        </div>
        """, unsafe_allow_html=True)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center; color: #334155; font-size: 0.78rem; font-family: 'JetBrains Mono', monospace;">
    Powered by GitHub Models API · Your PAT is never stored
</div>
""", unsafe_allow_html=True)