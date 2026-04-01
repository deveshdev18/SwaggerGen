import streamlit as st
import requests
import difflib
from pathlib import Path
from datetime import datetime

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

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main { background-color: #0f1117; }
    .stApp { background: linear-gradient(135deg, #0f1117 0%, #1a1d2e 100%); }

    h1, h2, h3 {
        font-family: 'JetBrains Mono', monospace !important;
        color: #e2e8f0 !important;
    }

    .hero-title {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.6rem;
        font-weight: 600;
        background: linear-gradient(90deg, #38bdf8, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.25rem;
    }
    .hero-subtitle {
        color: #64748b;
        font-size: 0.82rem;
        margin-bottom: 0.5rem;
    }

    .model-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        color: #64748b;
        margin-bottom: 8px;
    }

    .section-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        color: #38bdf8;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 0.75rem;
    }
    .section-label-modify {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        color: #a78bfa;
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

    .mode-badge-generate {
        display: inline-block;
        background: #0c2340;
        color: #38bdf8;
        border: 1px solid #38bdf8;
        border-radius: 20px;
        padding: 0.2rem 0.9rem;
        font-size: 0.78rem;
        font-family: 'JetBrains Mono', monospace;
        margin-bottom: 1rem;
    }
    .mode-badge-modify {
        display: inline-block;
        background: #1e1040;
        color: #a78bfa;
        border: 1px solid #a78bfa;
        border-radius: 20px;
        padding: 0.2rem 0.9rem;
        font-size: 0.78rem;
        font-family: 'JetBrains Mono', monospace;
        margin-bottom: 1rem;
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
    .stButton > button:hover { opacity: 0.85 !important; }

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

    .stTextInput > div > div > input, .stTextArea textarea {
        background: #161b27 !important;
        border-color: #2d3348 !important;
        color: #e2e8f0 !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.85rem !important;
    }

    /* ── Diff viewer ── */
    .diff-container {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1rem;
        margin-bottom: 1rem;
    }
    .diff-pane {
        background: #0d1117;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 0.75rem;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.76rem;
        overflow: auto;
        max-height: 500px;
    }
    .diff-pane-title {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.5rem;
        padding-bottom: 0.4rem;
        border-bottom: 1px solid #2d3348;
    }
    .diff-line { line-height: 1.7; white-space: pre-wrap; word-break: break-all; }
    .diff-add  { background: #0d2b0d; color: #86efac; }
    .diff-del  { background: #2b0d0d; color: #fca5a5; text-decoration: line-through; }
    .diff-ctx  { color: #6b7280; }

    /* ── Additional instructions box ── */
    .instructions-box {
        background: #0f1e14;
        border: 1px solid #166534;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        font-size: 0.82rem;
        color: #86efac;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

BACKEND_URL = "http://localhost:8000"

# ── Backup directory (sibling of this file) ────────────────────────────────────
_APP_DIR   = Path(__file__).resolve().parent
BACKUP_DIR = _APP_DIR / "story_backups"
BACKUP_DIR.mkdir(exist_ok=True)


# ── Backup helper ──────────────────────────────────────────────────────────────
def _save_story_backup(original_text: str, filename_hint: str = "revised_story") -> Path:
    """
    Write *original_text* to BACKUP_DIR once and return the path.
    The file is named  <filename_hint>_backup_<YYYYMMDD_HHMMSS>.txt
    so multiple edits in the same session never overwrite each other.
    """
    ts   = datetime.now().strftime("%Y%m%d_%H%M%SS")
    stem = Path(filename_hint).stem          # strip extension if present
    path = BACKUP_DIR / f"{stem}_backup_{ts}.txt"
    path.write_text(original_text, encoding="utf-8")
    return path


# ── Diff helpers ───────────────────────────────────────────────────────────────
def _build_diff(old_text: str, new_text: str):
    return list(difflib.ndiff(old_text.splitlines(), new_text.splitlines()))


def _diff_pane_html(diff, side: str) -> str:
    """Return HTML lines for one side of a diff. side = 'del' or 'add'."""
    out = []
    for line in diff:
        content = line[2:].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if side == "del" and line.startswith("- "):
            out.append(f'<div class="diff-line diff-del">{content}</div>')
        elif side == "add" and line.startswith("+ "):
            out.append(f'<div class="diff-line diff-add">{content}</div>')
        elif line.startswith("  "):
            out.append(f'<div class="diff-line diff-ctx">{content}</div>')
    return "\n".join(out)


# ── st.dialog — Preview & Edit (Modify mode) ──────────────────────────────────
@st.dialog("Preview & Edit User Stories", width="large")
def preview_dialog(existing_text: str, revised_text: str):
    """
    Full-screen modal:
    - Left  : existing story, color-coded diff (read-only)
    - Right : revised story, color-coded diff + editable text area in one pane
    On "Save & Close":
      • A backup of the *original* revised story is written to disk (once).
      • The edited version is saved to session_state for use by the AI.
    """
    diff = _build_diff(existing_text, revised_text)

    left_col, right_col = st.columns(2, gap="large")

    # ── Left: existing story with removed lines highlighted ───────────────────
    with left_col:
        st.markdown(
            '<div class="diff-pane-title" style="color:#f87171;">'
            'Existing Story — removed lines highlighted</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="diff-pane">{_diff_pane_html(diff, "del")}</div>',
            unsafe_allow_html=True,
        )

    # ── Right: revised story — diff + edit in one tabbed section ─────────────
    with right_col:
        st.markdown(
            '<div class="diff-pane-title" style="color:#86efac;">'
            'Revised Story</div>',
            unsafe_allow_html=True,
        )
        diff_tab, edit_tab = st.tabs(["📊 Diff View", "✏️ Edit"])

        with diff_tab:
            st.markdown(
                f'<div class="diff-pane" style="max-height:440px;">'
                f'{_diff_pane_html(diff, "add")}</div>',
                unsafe_allow_html=True,
            )

        with edit_tab:
            edited = st.text_area(
                "Edit revised story",
                value=st.session_state.get("mod_editable_story", revised_text),
                height=440,
                label_visibility="collapsed",
                key="dialog_story_editor",
            )

    # Footer row
    st.divider()
    save_col, _ = st.columns([1, 3])
    with save_col:
        if st.button("Save & Close", use_container_width=True):
            user_made_changes = edited != revised_text   # compare against the *original* upload

            if user_made_changes:
                # ── Write backup ONLY if the user actually changed something ──
                # Guard: skip if we already backed up this exact original text
                already_backed_up = (
                    st.session_state.get("mod_backup_source") == revised_text
                )
                if not already_backed_up:
                    hint        = st.session_state.get("mod_last_uploaded", "revised_story")
                    backup_path = _save_story_backup(revised_text, hint)
                    # Remember which original we backed up so we don't duplicate
                    st.session_state["mod_backup_source"] = revised_text
                    st.session_state["mod_backup_path"]   = str(backup_path)

                st.session_state["mod_story_was_edited"] = True

            # Always persist whatever the user typed (even if unchanged)
            st.session_state["mod_editable_story"] = edited
            st.rerun()


# ── st.dialog — Swagger Diff viewer ──────────────────────────────────────────
@st.dialog("Swagger Diff — Existing vs Modified", width="large")
def swagger_diff_dialog(baseline: str, modified: str):
    diff = _build_diff(baseline, modified)
    left_col, right_col = st.columns(2, gap="large")

    with left_col:
        st.markdown(
            '<div class="diff-pane-title" style="color:#f87171;">'
            'Existing Swagger — removed lines highlighted</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="diff-pane" style="max-height:520px;">'
            f'{_diff_pane_html(diff, "del")}</div>',
            unsafe_allow_html=True,
        )

    with right_col:
        st.markdown(
            '<div class="diff-pane-title" style="color:#86efac;">'
            'Modified Swagger — added lines highlighted</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="diff-pane" style="max-height:520px;">'
            f'{_diff_pane_html(diff, "add")}</div>',
            unsafe_allow_html=True,
        )

    st.divider()
    _, close_col = st.columns([4, 1])
    with close_col:
        if st.button("Close", use_container_width=True):
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# HEADER — compact toolbar (both modes)
# ══════════════════════════════════════════════════════════════════════════════
_current_mode  = st.session_state.get("_mode_radio", "🚀 Generate")
_is_modify_hdr = _current_mode == "✏️ Modify"

hdr_left, hdr_right = st.columns([3, 2])

with hdr_left:
    st.markdown(
        '<div class="hero-title">⚡ Swagger Generator</div>'
        '<div class="hero-subtitle">'
        'Generate or Modify Swagger files from user stories using GitHub Copilot AI</div>',
        unsafe_allow_html=True,
    )

with hdr_right:
    mdl_col, info_col, status_col = st.columns([5, 1, 2])

    with mdl_col:
        st.markdown('<div class="model-label">MODEL</div>', unsafe_allow_html=True)
        try:
            _mr = requests.get(f"{BACKEND_URL}/models", timeout=5)
            _model_options = {m["name"]: m["id"] for m in _mr.json()["models"]}
        except Exception:
            _model_options = {
                "Claude Sonnet 4.5 (Recommended)": "claude-sonnet-4.5",
                "GPT-4.1": "gpt-4.1",
                "GPT-4o": "gpt-4o",
                "Claude Opus 4": "claude-opus-4",
            }
        _toolbar_key = "modify_model" if _is_modify_hdr else "generate_model_toolbar"
        _sel_name = st.selectbox(
            "model_select",
            list(_model_options.keys()),
            label_visibility="collapsed",
            key=_toolbar_key,
        )
        selected_model_id        = _model_options[_sel_name]
        selected_model_id_modify = _model_options[_sel_name]

    with info_col:
        st.markdown("<br>", unsafe_allow_html=True)
        show_info = st.button("ℹ️", key="info_btn", help="About Copilot CLI authentication")

    with status_col:
        st.markdown("<br>", unsafe_allow_html=True)
        check_status = st.button("Status", key="status_btn", help="Check Copilot CLI status")

if show_info:
    st.markdown("""
    <div class="pat-info">
        🤖 Authentication is handled by <b>GitHub Copilot CLI</b><br>
        Make sure you have run <code>copilot auth login</code> before starting the backend.
    </div>
    """, unsafe_allow_html=True)

if check_status:
    with st.spinner("Checking Copilot CLI status…"):
        try:
            resp = requests.post(f"{BACKEND_URL}/validate-pat", timeout=15)
            result = resp.json()
            if result["valid"]:
                st.markdown('<span class="success-badge">✓ Copilot CLI Ready</span>', unsafe_allow_html=True)
            else:
                st.markdown(f'<span class="error-badge">✗ {result["message"]}</span>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Could not reach backend: {e}")

st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# MODE TOGGLE
# ══════════════════════════════════════════════════════════════════════════════
mode = st.radio(
    "Mode",
    ["🚀 Generate", "✏️ Modify"],
    horizontal=True,
    label_visibility="collapsed",
    key="_mode_radio",
)
is_modify = mode == "✏️ Modify"

if is_modify:
    st.markdown(
        '<div class="mode-badge-modify">✏️ MODIFY MODE — modifies an existing Swagger File based on a revised user story</div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<div class="mode-badge-generate">🚀 GENERATE MODE — generates a new Swagger File from a user story</div>',
        unsafe_allow_html=True,
    )

label_color = "section-label-modify" if is_modify else "section-label"

left_col, right_col = st.columns([1, 1], gap="large")


# ─────────────────────────────────────────────────────────────────────────────
# LEFT COLUMN
# ─────────────────────────────────────────────────────────────────────────────
with left_col:

    # ══════════════════════════════════════════════════════════════════════════
    # GENERATE MODE
    # ══════════════════════════════════════════════════════════════════════════
    if not is_modify:

        st.markdown(f'<div class="{label_color}">① Learning Examples</div>', unsafe_allow_html=True)
        st.caption("Upload 1–3 example pairs so the AI learns your Swagger structure")

        num_examples = st.radio("Number of examples", [1, 2, 3], horizontal=True)

        example_files = {}
        for i in range(1, int(num_examples) + 1):
            with st.expander(f"Example {i}", expanded=(i == 1)):
                example_files[f"story_{i}"] = st.file_uploader(
                    f"User Story {i} (.txt)",
                    type=["txt"],
                    key=f"gen_ex_story_{i}",
                )
                example_files[f"swagger_{i}"] = st.file_uploader(
                    f"Swagger YAML {i} (.yaml / .yml)",
                    type=["yaml", "yml"],
                    key=f"gen_ex_swagger_{i}",
                )

        st.markdown("---")

        st.markdown(f'<div class="{label_color}">② New User Story (Input)</div>', unsafe_allow_html=True)
        st.caption("Upload the user story you want to generate a Swagger file for")

        input_story_file = st.file_uploader(
            "New User Story (.txt)",
            type=["txt"],
            key="gen_input_story",
        )

        if input_story_file:
            with st.expander("Preview"):
                st.text(input_story_file.read().decode("utf-8"))
                input_story_file.seek(0)

        st.markdown("---")

        # ── ③ Additional / Special Instructions ──────────────────────────────
        st.markdown(
            f'<div class="{label_color}">③ Additional Instructions (Optional)</div>',
            unsafe_allow_html=True,
        )
        st.caption(
            "Add any special instructions, module names, constraints, or hints for the AI — "
            "these will be passed directly into the generation prompt."
        )

        additional_instructions = st.text_area(
            "Additional Instructions",
            placeholder=(
                "e.g.\n"
                "• Include modules: Payments, Refunds, Settlements\n"
                "• Use snake_case for all field names\n"
                "• Add pagination to all list endpoints\n"
                "• All date fields should use ISO 8601 format (YYYY-MM-DD)"
            ),
            height=150,
            label_visibility="collapsed",
            key="gen_additional_instructions",
        )

        # Show a subtle confirmation badge when instructions have been entered
        if additional_instructions and additional_instructions.strip():
            line_count = len([l for l in additional_instructions.strip().splitlines() if l.strip()])
            st.markdown(
                f'<div class="instructions-box">'
                f'✅ {line_count} instruction{"s" if line_count != 1 else ""} will be included in the prompt'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.markdown("---")
        action_clicked = st.button("🚀 Generate Swagger YAML", use_container_width=True)

    # ══════════════════════════════════════════════════════════════════════════
    # MODIFY MODE
    # ══════════════════════════════════════════════════════════════════════════
    else:

        # ① Existing Artifacts
        st.markdown(
            f'<div class="{label_color}">① Existing Artifacts (User Story & Swagger File)</div>',
            unsafe_allow_html=True,
        )

        existing_story_file = st.file_uploader(
            "Existing User Story (.txt)",
            type=["txt"],
            key="mod_ex_story",
        )
        existing_swagger_file = st.file_uploader(
            "Existing Swagger File (.yaml/.yml)",
            type=["yaml", "yml"],
            key="mod_ex_swagger",
        )

        st.markdown("---")

        # ② Revised User Story
        st.markdown(
            f'<div class="{label_color}">② Revised User Story (Input)</div>',
            unsafe_allow_html=True,
        )
        st.caption("Only the changes will be applied to the Swagger file")

        revised_story_file = st.file_uploader(
            "Revised User Story (.txt)",
            type=["txt"],
            key="mod_input_story",
        )

        if revised_story_file:
            revised_story_text = revised_story_file.read().decode("utf-8")
            revised_story_file.seek(0)

            # Seed editable story once per new upload
            if (
                "mod_editable_story" not in st.session_state
                or st.session_state.get("mod_last_uploaded") != revised_story_file.name
            ):
                st.session_state["mod_editable_story"]   = revised_story_text
                st.session_state["mod_last_uploaded"]    = revised_story_file.name
                st.session_state["mod_last_raw"]         = revised_story_text
                st.session_state["mod_story_was_edited"] = False
                # Clear any backup state from a previous upload
                st.session_state.pop("mod_backup_source", None)
                st.session_state.pop("mod_backup_path",   None)

            # Preview button — requires existing story
            if existing_story_file:
                # Show edited indicator + backup path if story was changed in the dialog
                if st.session_state.get("mod_story_was_edited"):
                    st.caption("⚠️ Revised story has been edited — the edited version will be used")
                    backup_path = st.session_state.get("mod_backup_path")
                    if backup_path:
                        st.caption(f"💾 Original backed up → `{backup_path}`")

                if st.button("Preview & Edit Stories", key="mod_preview_btn"):
                    existing_story_text_for_dialog = existing_story_file.read().decode("utf-8")
                    existing_story_file.seek(0)
                    st.session_state["mod_cached_existing"] = existing_story_text_for_dialog
                    preview_dialog(
                        existing_story_text_for_dialog,
                        st.session_state["mod_editable_story"],
                    )
            else:
                st.caption("ℹ️ Upload the existing user story above to enable Preview & diff")

        st.markdown("---")

        # ③ Guidelines scope checkbox
        apply_to_full_file = st.checkbox(
            "Apply Swagger guidelines to the entire file (not just the changed sections)",
            value=True,
            key="mod_apply_guidelines_full",
            help=(
                "Checked guidelines are enforced across the whole output file, "
                "including sections carried over from the original. "
                "Unchecked guidelines are applied only to sections that changed "
                "based on the diff between the original and revised user story."
            ),
        )

        st.markdown("---")
        action_clicked = st.button("Modify Swagger YAML", use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# RIGHT COLUMN — Output
# ─────────────────────────────────────────────────────────────────────────────
with right_col:
    output_label = "Generated" if not is_modify else "Modified"
    # Use ④ for Generate mode (since ③ is now Additional Instructions), ③ for Modify
    output_step  = "④" if not is_modify else "③"
    st.markdown(
        f'<div class="{label_color}">{output_step} {output_label} Output</div>',
        unsafe_allow_html=True,
    )

    if action_clicked:

        # ── GENERATE ──────────────────────────────────────────────────────────
        if not is_modify:
            errors = []
            if not input_story_file:
                errors.append("Input user story is required")
            has_example = any(
                example_files.get(f"story_{i}") and example_files.get(f"swagger_{i}")
                for i in range(1, int(num_examples) + 1)
            )
            if not has_example:
                errors.append("At least one complete example pair (story + swagger) is required")

            if errors:
                for e in errors:
                    st.error(f"⚠️ {e}")
            else:
                with st.spinner("🤖 AI is generating your Swagger YAML..."):
                    try:
                        files = {
                            "input_story": (
                                input_story_file.name,
                                input_story_file.read(),
                                "text/plain",
                            )
                        }
                        input_story_file.seek(0)
                        for i in range(1, int(num_examples) + 1):
                            sf = example_files.get(f"story_{i}")
                            sw = example_files.get(f"swagger_{i}")
                            if sf and sw:
                                files[f"example_story_{i}"] = (sf.name, sf.read(), "text/plain")
                                files[f"example_swagger_{i}"] = (sw.name, sw.read(), "application/x-yaml")
                                sf.seek(0); sw.seek(0)

                        response = requests.post(
                            f"{BACKEND_URL}/generate",
                            files=files,
                            data={
                                "model": selected_model_id,
                                "additional_instructions": st.session_state.get(
                                    "gen_additional_instructions", ""
                                ),
                            },
                            timeout=620,
                        )
                        if response.status_code == 200:
                            st.session_state["yaml_output"] = response.text
                            st.session_state["yaml_mode"]   = "generate"
                            st.markdown('<span class="success-badge">✓ Complete</span>', unsafe_allow_html=True)
                        else:
                            st.error(f"Failed: {response.json().get('detail', response.text)}")
                    except requests.exceptions.ConnectionError:
                        st.error("❌ Cannot connect to backend. Make sure FastAPI is running on port 8000.")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

        # ── MODIFY ────────────────────────────────────────────────────────────
        else:
            errors = []
            effective_story = st.session_state.get("mod_editable_story", "")
            if not effective_story.strip():
                errors.append("Revised user story is required")
            if not existing_story_file or not existing_swagger_file:
                errors.append("Both an existing user story and an existing Swagger file are required")

            if errors:
                for e in errors:
                    st.error(f"⚠️ {e}")
            else:
                with st.spinner("🤖 AI is modifying your Swagger YAML…"):
                    try:
                        existing_story_file.seek(0)
                        existing_swagger_file.seek(0)
                        files = {
                            "revised_story": (
                                "revised_story.txt",
                                effective_story.encode("utf-8"),
                                "text/plain",
                            ),
                            "example_story_1": (
                                existing_story_file.name,
                                existing_story_file.read(),
                                "text/plain",
                            ),
                            "example_swagger_1": (
                                existing_swagger_file.name,
                                existing_swagger_file.read(),
                                "application/x-yaml",
                            ),
                        }
                        response = requests.post(
                            f"{BACKEND_URL}/modify",
                            files=files,
                            data={
                                "model": selected_model_id_modify,
                                "apply_guidelines_to_full_file": str(
                                    st.session_state.get("mod_apply_guidelines_full", True)
                                ).lower(),
                            },
                            timeout=620,
                        )
                        if response.status_code == 200:
                            st.session_state["yaml_output"] = response.text
                            st.session_state["yaml_mode"]   = "modify"
                            existing_swagger_file.seek(0)
                            st.session_state["mod_baseline_swagger"] = existing_swagger_file.read().decode("utf-8")
                            st.markdown('<span class="success-badge">✓ Complete</span>', unsafe_allow_html=True)
                        else:
                            st.error(f"Failed: {response.json().get('detail', response.text)}")
                    except requests.exceptions.ConnectionError:
                        st.error("❌ Cannot connect to backend. Make sure FastAPI is running on port 8000.")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

    # ── Display output ─────────────────────────────────────────────────────────
    if "yaml_output" in st.session_state:
        yaml_output     = st.session_state["yaml_output"]
        yaml_mode       = st.session_state.get("yaml_mode", "generate")
        output_filename = "modified_swagger.yaml" if yaml_mode == "modify" else "generated_swagger.yaml"

        if is_modify:
            baseline = st.session_state.get("mod_baseline_swagger", "")
            if baseline and yaml_output != baseline:
                if st.button("📊 View Diff", key="view_diff_btn"):
                    swagger_diff_dialog(baseline, yaml_output)
            st.markdown(f'<div class="yaml-output">{yaml_output}</div>', unsafe_allow_html=True)

        else:
            st.markdown(f'<div class="yaml-output">{yaml_output}</div>', unsafe_allow_html=True)

        st.markdown("####")
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="⬇️ Download YAML",
                data=yaml_output,
                file_name=output_filename,
                mime="application/x-yaml",
                use_container_width=True,
            )
        with col2:
            if st.button("🗑️ Clear Output", use_container_width=True):
                for k in ["yaml_output", "yaml_mode", "mod_baseline_swagger"]:
                    st.session_state.pop(k, None)
                st.rerun()

        _caption_model = selected_model_id_modify if is_modify else selected_model_id
        st.caption(
            f"📊 {yaml_output.count(chr(10))} lines · {len(yaml_output)} chars"
            f" · {output_filename} · Model: `{_caption_model}`"
        )

        if is_modify:
            st.markdown("---")
            st.markdown(
                f'<div class="{label_color}">🔄 Not satisfied? Revise the story and modify again</div>',
                unsafe_allow_html=True,
            )
            st.caption("Use Preview & Edit Stories on the left, then click Modify Swagger YAML again.")

    else:
        placeholder_text = (
            "Your modified Swagger YAML will appear here"
            if is_modify
            else "Your generated Swagger YAML will appear here"
        )
        st.markdown(f"""
        <div style="border:1px dashed #2d3348;border-radius:12px;padding:3rem 2rem;
                    text-align:center;color:#475569;margin-top:1rem;">
            <div style="font-size:2.5rem;margin-bottom:1rem;">{"✏️" if is_modify else "📋"}</div>
            <div style="font-family:'JetBrains Mono',monospace;font-size:0.85rem;">
                {placeholder_text}
            </div>
            <div style="font-size:0.78rem;margin-top:0.5rem;color:#334155;">
                Fill in the form on the left and click {"Modify" if is_modify else "Generate"}
            </div>
        </div>
        """, unsafe_allow_html=True)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center;color:#334155;font-size:0.78rem;font-family:'JetBrains Mono',monospace;">
    Powered by GitHub Copilot API
</div>
""", unsafe_allow_html=True)