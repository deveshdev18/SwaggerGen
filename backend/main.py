from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from typing import Optional
import asyncio
import shutil
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
BASE_DIR = Path(__file__).resolve().parent.parent
LEARNING_DIR = BASE_DIR / "learning"
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"

LEARNING_DIR.mkdir(exist_ok=True)
INPUT_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


def build_agent_prompt() -> str:
    return f"""You are an expert API designer.

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


async def run_copilot_agent(prompt: str, model: str) -> str:
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
            event_type = event.type.value if hasattr(event.type, 'value') else str(event.type)

            #if event_type == "permission.requested":
                # Auto-approve all mid-session permission requests
              #  permission = event.data.permission_request
              #  if permission and permission.tool_call_id:
               #     asyncio.create_task(
                   #     session.approve_permission(permission.tool_call_id)
               #     )

            if event_type == "assistant.message":
                content = event.data.content if hasattr(event.data, 'content') else str(event.data)
                if content and not event.data.tool_requests:
                    result_content.append(content)

            elif event_type == "session.idle":
                done.set()

        session.on(on_event)
        await session.send({"prompt": prompt})

        # Wait up to 10 minutes for the agent to finish
        await asyncio.wait_for(done.wait(), timeout=600.0)

        # Primary: read the generated file from output folder
        output_file = OUTPUT_DIR / "generated_swagger.yaml"
        if output_file.exists():
            generated_yaml = output_file.read_text(encoding="utf-8").strip()
            if generated_yaml:
                return generated_yaml

        # Fallback: agent may have returned YAML directly in its message
        if result_content:
            content = result_content[0].strip()
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            if content.startswith("openapi"):
                return content

        raise HTTPException(
            status_code=500,
            detail="Agent did not generate the output file. Please check your learning and input folders."
        )

    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail="Agent timed out. Try using a faster model or fewer examples."
        )
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


@app.get("/")
async def root():
    return {"message": "Swagger Generator API is running"}


@app.get("/models")
async def list_models():
    return {
        "models": [
            {"id": "claude-sonnet-4.5", "name": "Claude Sonnet 4.5 (Recommended)", "description": "Best for large files"},
            {"id": "gpt-4.1", "name": "GPT-4.1", "description": "Great for code/YAML generation"},
            {"id": "gpt-4o", "name": "GPT-4o", "description": "Fast and capable"},
            {"id": "claude-opus-4", "name": "Claude Opus 4", "description": "Most powerful, slower"},
        ]
    }


@app.post("/generate", response_class=PlainTextResponse)
async def generate_swagger(
    model: str = Form(default="claude-sonnet-4.5"),
    input_story: UploadFile = File(..., description="New user story to generate Swagger for"),
    example_story_1: Optional[UploadFile] = File(default=None),
    example_swagger_1: Optional[UploadFile] = File(default=None),
    example_story_2: Optional[UploadFile] = File(default=None),
    example_swagger_2: Optional[UploadFile] = File(default=None),
    example_story_3: Optional[UploadFile] = File(default=None),
    example_swagger_3: Optional[UploadFile] = File(default=None),
):
    # ── Collect uploaded example pairs ────────────────────────────────────────
    pairs = [
        (example_story_1, example_swagger_1, "example_1"),
        (example_story_2, example_swagger_2, "example_2"),
        (example_story_3, example_swagger_3, "example_3"),
    ]

    new_examples = []
    for story_file, swagger_file, name in pairs:
        if story_file and swagger_file:
            story_content = (await story_file.read()).decode("utf-8")
            swagger_content = (await swagger_file.read()).decode("utf-8")
            if story_content.strip() and swagger_content.strip():
                new_examples.append((story_content, swagger_content, name))

    # ── If new examples uploaded, refresh learning folder ─────────────────────
    # If no examples uploaded, keep existing files in learning/ folder
    if new_examples:
        shutil.rmtree(LEARNING_DIR)
        LEARNING_DIR.mkdir(exist_ok=True)
        for story_content, swagger_content, name in new_examples:
            (LEARNING_DIR / f"{name}_story.txt").write_text(story_content, encoding="utf-8")
            (LEARNING_DIR / f"{name}_swagger.yaml").write_text(swagger_content, encoding="utf-8")

    # ── Validate that learning folder has at least one example ────────────────
    existing_examples = list(LEARNING_DIR.glob("*.yaml"))
    if not existing_examples:
        raise HTTPException(
            status_code=400,
            detail="No examples found. Please upload at least one example pair (user story + swagger YAML)."
        )

    # ── Save input story, clear old input/output ───────────────────────────────
    shutil.rmtree(INPUT_DIR)
    shutil.rmtree(OUTPUT_DIR)
    INPUT_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

    input_content = (await input_story.read()).decode("utf-8")
    if not input_content.strip():
        raise HTTPException(status_code=400, detail="Input user story is empty.")
    (INPUT_DIR / "user_story.txt").write_text(input_content, encoding="utf-8")

    # ── Run the Copilot agent ──────────────────────────────────────────────────
    prompt = build_agent_prompt()
    result = await run_copilot_agent(prompt, model)
    return result


@app.post("/validate-pat")
async def validate_pat():
    """Check if Copilot CLI is authenticated and ready."""
    try:
        client = CopilotClient()
        await client.start()
        await client.stop()
        return {"valid": True, "message": "Copilot CLI is authenticated and ready"}
    except Exception as e:
        return {"valid": False, "message": f"Copilot CLI error: {str(e)}"}