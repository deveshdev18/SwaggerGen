from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from typing import Optional
import asyncio
import shutil
import re
import csv
import io
from pathlib import Path
from copilot import CopilotClient, PermissionHandler

app = FastAPI(title="Swagger Generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Folder paths ───────────────────────────────────────────────────────────────
BASE_DIR       = Path(__file__).resolve().parent.parent
LEARNING_DIR   = BASE_DIR / "learning"
INPUT_DIR      = BASE_DIR / "input"
OUTPUT_DIR     = BASE_DIR / "output"
GUIDELINES_DIR = BASE_DIR / "guidelines"

for d in (LEARNING_DIR, INPUT_DIR, OUTPUT_DIR, GUIDELINES_DIR):
    d.mkdir(exist_ok=True)

# ── Swagger guidelines ─────────────────────────────────────────────────────────

def load_guidelines() -> str:
    parts = []
    for f in sorted(GUIDELINES_DIR.iterdir()):
        if f.suffix.lower() in (".md", ".txt"):
            content = f.read_text(encoding="utf-8").strip()
            if content:
                parts.append(f"### {f.name}\n{content}")
        elif f.suffix.lower() == ".csv":
            raw = f.read_text(encoding="utf-8-sig")
            reader = csv.reader(io.StringIO(raw))
            rows = list(reader)
            if not rows:
                continue
            lines = []
            for row in rows[1:]:
                while len(row) < 3:
                    row.append("")
                num       = row[0].strip()
                guideline = row[1].strip()
                remarks   = row[2].strip()
                if not guideline:
                    continue
                if num:
                    lines.append(f"\n{num}. {guideline}")
                else:
                    lines.append(f"   - {guideline}")
                if remarks:
                    lines.append("     Example/Remarks:")
                    for rline in remarks.splitlines():
                        lines.append(f"       {rline}")
            parts.append(f"### {f.name}\n" + "\n".join(lines))
    return "\n\n".join(parts)


# ── OpenAPI version helpers ────────────────────────────────────────────────────
_OPENAPI_RE = re.compile(r"^\s*openapi\s*:\s*['\"]?(\d+\.\d+(?:\.\d+)?)['\"]?", re.MULTILINE)

def _parse_openapi_version(yaml_text: str) -> tuple[int, ...]:
    m = _OPENAPI_RE.search(yaml_text)
    if not m:
        return (0,)
    return tuple(int(x) for x in m.group(1).split("."))

def _openapi_version_str(yaml_text: str) -> str:
    m = _OPENAPI_RE.search(yaml_text)
    return m.group(1) if m else "unknown"


# ── Prompt builders ────────────────────────────────────────────────────────────

def build_agent_prompt(additional_instructions: str = "") -> str:
    guidelines = load_guidelines()
    guidelines_block = (
        f"\n\n"
        f"════════════════════════════════════════════════════════\n"
        f"MANDATORY Swagger / OpenAPI Design Guidelines\n"
        f"You MUST read, understand, and strictly abide by ALL of\n"
        f"the following rules before generating any YAML output.\n"
        f"Non-compliance is not acceptable.\n"
        f"════════════════════════════════════════════════════════\n"
        f"{guidelines}\n"
        f"════════════════════════════════════════════════════════"
        if guidelines else ""
    )

    additional_instructions_block = (
        f"\n\n"
        f"════════════════════════════════════════════════════════\n"
        f"ADDITIONAL INSTRUCTIONS FROM USER\n"
        f"You MUST follow these additional instructions provided by the user.\n"
        f"They take effect alongside the guidelines above and must be fully\n"
        f"honoured in the generated output — non-compliance is not acceptable.\n"
        f"════════════════════════════════════════════════════════\n"
        f"{additional_instructions.strip()}\n"
        f"════════════════════════════════════════════════════════"
        if additional_instructions and additional_instructions.strip() else ""
    )

    return f"""You are an expert API designer.
{guidelines_block}{additional_instructions_block}

In the folder '{LEARNING_DIR}', there are example user stories (*.txt files)
and their corresponding Swagger YAML files (*.yaml files) with matching names.

Please do the following:
1. Read and understand all the example user stories and their corresponding Swagger YAML files in the learning folder.
2. Learn the structure, patterns, and conventions used in those Swagger files.
3. Read the new user story from the input folder: '{INPUT_DIR}'.
4. Generate a complete, valid OpenAPI 3.0 Swagger YAML file for that user story, following the exact same structure and conventions as the examples.
5. Save the generated YAML to: '{OUTPUT_DIR / "generated_swagger.yaml"}'

IMPORTANT:
- The output file must start with 'openapi: 3.0.0'
- Include all necessary components: info, paths, components/schemas
- Follow the exact same structure as the learning examples
- Save ONLY the raw YAML content, no explanations or markdown
"""


def build_modify_prompt(existing_openapi_version: str, apply_guidelines_to_full_file: bool = True) -> str:
    guidelines = load_guidelines()
    guidelines_block = (
        f"\n\n"
        f"════════════════════════════════════════════════════════\n"
        f"MANDATORY Swagger / OpenAPI Design Guidelines\n"
        f"You MUST read, understand, and strictly abide by ALL of\n"
        f"the following rules before modifying any YAML output.\n"
        f"Non-compliance is not acceptable.\n"
        f"════════════════════════════════════════════════════════\n"
        f"{guidelines}\n"
        f"════════════════════════════════════════════════════════"
        if guidelines else ""
    )

    target_version = "3.0.0"
    existing_ver = tuple(int(x) for x in existing_openapi_version.split(".")) if existing_openapi_version != "unknown" else (0,)
    target_ver   = (3, 0, 0)

    if existing_ver >= target_ver:
        version_instruction = (
            f"- The existing Swagger file uses OpenAPI {existing_openapi_version}. "
            f"Keep the same OpenAPI version — do NOT downgrade it."
        )
    else:
        version_instruction = (
            f"- The existing Swagger file uses OpenAPI {existing_openapi_version}, which is lower than {target_version}. "
            f"Upgrade the openapi field to {target_version} in the output."
        )

    # ── Guidelines scope — switches on the checkbox value ─────────────────────
    if apply_guidelines_to_full_file:
        guidelines_scope_block = """
CRITICAL — Guidelines Apply to the ENTIRE Output File (No Exceptions):
- The Swagger guidelines listed above are NOT scoped to only the new or changed sections.
- After merging in the revised story changes, you MUST perform a full compliance audit of every
  single line in the final YAML — including all sections carried over unchanged from the original.
- There are NO exemptions for "legacy" or "pre-existing" content. If any section from the
  original file violates a guideline, you MUST fix it before saving.
- The final saved file must be 100% compliant with every guideline, end-to-end, with zero
  violations anywhere in the document — old content and new content alike.
"""
    else:
        guidelines_scope_block = """
CRITICAL — Guidelines Apply to Changed Sections Only:
- The Swagger guidelines listed above must be applied ONLY to the sections that are new or
  modified as a result of the revised user story.
- Sections of the original Swagger file that are NOT affected by the revised story must be
  carried over exactly as-is, without any guideline-driven changes.
- Do NOT audit, reformat, or alter any part of the file that was not touched by the diff
  between the original and revised user story.
"""

    return f"""You are an expert API designer.
{guidelines_block}

In the folder '{LEARNING_DIR}', there are original user stories (*.txt files)
and their corresponding Swagger YAML files (*.yaml files) with matching names.

In the input folder '{INPUT_DIR}', there is a revised user story file called 'revised_story.txt'.

Please do the following:
1. Read and understand all the original user stories and their corresponding Swagger YAML files in the learning folder.
2. Read the revised user story from: '{INPUT_DIR / "revised_story.txt"}'.
3. Compare the revised user story against the original user stories to identify what has changed.
4. Take the existing Swagger YAML from the learning folder as the base, and merge in the changes introduced by the revised user story.
5. Save the modified YAML to: '{OUTPUT_DIR / "modified_swagger.yaml"}'

OpenAPI Version Rule:
{version_instruction}
{guidelines_scope_block}
IMPORTANT:
- Include all necessary components: info, paths, components/schemas
- Use the existing Swagger YAML as the base — do not regenerate from scratch.
- Save ONLY the raw YAML content, no explanations or markdown
"""


# ── Copilot agent runner ───────────────────────────────────────────────────────

async def run_copilot_agent(prompt: str, model: str, output_filename: str) -> str:
    client = CopilotClient()
    await client.start()

    result_content = []
    done = asyncio.Event()
    session = None

    try:
        session = await client.create_session({
            "model": model,
            "streaming": False,
            "on_permission_request": PermissionHandler.approve_all,
            "cwd": str(BASE_DIR),
        })

        def on_event(event):
            event_type = event.type.value if hasattr(event.type, "value") else str(event.type)
            if event_type == "assistant.message":
                content = event.data.content if hasattr(event.data, "content") else str(event.data)
                if content and not event.data.tool_requests:
                    result_content.append(content)
            elif event_type == "session.idle":
                done.set()

        session.on(on_event)
        await session.send({"prompt": prompt})
        await asyncio.wait_for(done.wait(), timeout=600.0)

        output_file = OUTPUT_DIR / output_filename
        if output_file.exists():
            generated_yaml = output_file.read_text(encoding="utf-8").strip()
            if generated_yaml:
                return generated_yaml

        if result_content:
            content = result_content[0].strip()
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            if content.startswith("openapi"):
                return content

        raise HTTPException(
            status_code=500,
            detail="Agent did not generate the output file. Please check your learning and input folders.",
        )

    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timed out. Try using a faster model or fewer examples.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Copilot agent error: {str(e)}")
    finally:
        if session:
            try:
                await session.disconnect()
            except Exception:
                pass
        await client.stop()


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"message": "Swagger Generator API is running"}


@app.get("/models")
async def list_models():
    return {
        "models": [
            {"id": "claude-sonnet-4.5", "name": "Claude Sonnet 4.5 (Recommended)", "description": "Best for large files"},
            {"id": "gpt-4.1",           "name": "GPT-4.1",                          "description": "Great for code/YAML generation"},
            {"id": "gpt-4o",            "name": "GPT-4o",                           "description": "Fast and capable"},
            {"id": "claude-opus-4",     "name": "Claude Opus 4",                    "description": "Most powerful, slower"},
        ]
    }


@app.post("/generate", response_class=PlainTextResponse)
async def generate_swagger(
    model: str = Form(default="claude-sonnet-4.5"),
    additional_instructions: str = Form(default=""),
    input_story: UploadFile = File(..., description="New user story to generate Swagger for"),
    example_story_1:   Optional[UploadFile] = File(default=None),
    example_swagger_1: Optional[UploadFile] = File(default=None),
    example_story_2:   Optional[UploadFile] = File(default=None),
    example_swagger_2: Optional[UploadFile] = File(default=None),
    example_story_3:   Optional[UploadFile] = File(default=None),
    example_swagger_3: Optional[UploadFile] = File(default=None),
):
    raw_pairs = [
        (example_story_1, example_swagger_1, "example_1"),
        (example_story_2, example_swagger_2, "example_2"),
        (example_story_3, example_swagger_3, "example_3"),
    ]

    new_examples = []
    for story_file, swagger_file, name in raw_pairs:
        if story_file and swagger_file:
            story_content   = (await story_file.read()).decode("utf-8")
            swagger_content = (await swagger_file.read()).decode("utf-8")
            if story_content.strip() and swagger_content.strip():
                new_examples.append((story_content, swagger_content, name))

    if new_examples:
        shutil.rmtree(LEARNING_DIR)
        LEARNING_DIR.mkdir(exist_ok=True)
        for story_content, swagger_content, name in new_examples:
            (LEARNING_DIR / f"{name}_story.txt").write_text(story_content, encoding="utf-8")
            (LEARNING_DIR / f"{name}_swagger.yaml").write_text(swagger_content, encoding="utf-8")

    if not list(LEARNING_DIR.glob("*.yaml")):
        raise HTTPException(
            status_code=400,
            detail="No examples found. Please upload at least one example pair (user story + swagger YAML).",
        )

    shutil.rmtree(INPUT_DIR)
    shutil.rmtree(OUTPUT_DIR)
    INPUT_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

    input_content = (await input_story.read()).decode("utf-8")
    if not input_content.strip():
        raise HTTPException(status_code=400, detail="Input user story is empty.")
    (INPUT_DIR / "user_story.txt").write_text(input_content, encoding="utf-8")

    prompt = build_agent_prompt(additional_instructions)
    return await run_copilot_agent(prompt, model, "generated_swagger.yaml")


@app.post("/modify", response_class=PlainTextResponse)
async def modify_swagger(
    model: str = Form(default="claude-sonnet-4.5"),
    apply_guidelines_to_full_file: str = Form(default="true"),
    revised_story: UploadFile = File(..., description="Revised user story to modify the Swagger for"),
    example_story_1:   Optional[UploadFile] = File(default=None),
    example_swagger_1: Optional[UploadFile] = File(default=None),
    example_story_2:   Optional[UploadFile] = File(default=None),
    example_swagger_2: Optional[UploadFile] = File(default=None),
    example_story_3:   Optional[UploadFile] = File(default=None),
    example_swagger_3: Optional[UploadFile] = File(default=None),
):
    full_file_flag = apply_guidelines_to_full_file.lower() == "true"

    raw_pairs = [
        (example_story_1, example_swagger_1, "example_1"),
        (example_story_2, example_swagger_2, "example_2"),
        (example_story_3, example_swagger_3, "example_3"),
    ]

    new_examples = []
    existing_openapi_version = "unknown"

    for story_file, swagger_file, name in raw_pairs:
        if story_file and swagger_file:
            story_content   = (await story_file.read()).decode("utf-8")
            swagger_content = (await swagger_file.read()).decode("utf-8")
            if story_content.strip() and swagger_content.strip():
                new_examples.append((story_content, swagger_content, name))
                if existing_openapi_version == "unknown":
                    existing_openapi_version = _openapi_version_str(swagger_content)

    if new_examples:
        shutil.rmtree(LEARNING_DIR)
        LEARNING_DIR.mkdir(exist_ok=True)
        for story_content, swagger_content, name in new_examples:
            (LEARNING_DIR / f"{name}_story.txt").write_text(story_content, encoding="utf-8")
            (LEARNING_DIR / f"{name}_swagger.yaml").write_text(swagger_content, encoding="utf-8")

    if existing_openapi_version == "unknown":
        for yaml_file in LEARNING_DIR.glob("*.yaml"):
            content = yaml_file.read_text(encoding="utf-8")
            v = _openapi_version_str(content)
            if v != "unknown":
                existing_openapi_version = v
                break

    if not list(LEARNING_DIR.glob("*.yaml")):
        raise HTTPException(
            status_code=400,
            detail="No examples found. Please upload at least one example pair (original story + swagger YAML).",
        )

    shutil.rmtree(INPUT_DIR)
    shutil.rmtree(OUTPUT_DIR)
    INPUT_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

    revised_content = (await revised_story.read()).decode("utf-8")
    if not revised_content.strip():
        raise HTTPException(status_code=400, detail="Revised user story is empty.")
    (INPUT_DIR / "revised_story.txt").write_text(revised_content, encoding="utf-8")

    prompt = build_modify_prompt(existing_openapi_version, full_file_flag)
    return await run_copilot_agent(prompt, model, "modified_swagger.yaml")


@app.post("/validate-pat")
async def validate_pat():
    try:
        client = CopilotClient()
        await client.start()
        await client.stop()
        return {"valid": True, "message": "Copilot CLI is authenticated and ready"}
    except Exception as e:
        return {"valid": False, "message": f"Copilot CLI error: {str(e)}"}