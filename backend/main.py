from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from typing import Optional
import asyncio
from copilot import CopilotClient , PermissionHandler

app = FastAPI(title="Swagger Generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def build_prompt(examples: list[dict], new_story: str) -> str:
    prompt = "You are an expert API designer. Your job is to generate a Swagger/OpenAPI YAML file for a given user story.\n\n"
    prompt += "Here are some examples of user stories and their corresponding Swagger YAML files:\n\n"

    for i, example in enumerate(examples, 1):
        prompt += f"--- EXAMPLE {i} ---\n"
        prompt += f"USER STORY:\n{example['story']}\n\n"
        prompt += f"SWAGGER YAML:\n{example['swagger']}\n\n"

    prompt += "--- YOUR TASK ---\n"
    prompt += "Now generate a complete, valid Swagger/OpenAPI 3.0 YAML file for this user story:\n\n"
    prompt += f"{new_story}\n\n"
    prompt += (
        "IMPORTANT RULES:\n"
        "1. Return ONLY the raw YAML content. No explanations, no markdown code blocks, no backticks.\n"
        "2. Start directly with 'openapi: 3.0.0'\n"
        "3. Include all necessary components: info, paths, components/schemas\n"
        "4. Follow the exact same structure as the examples above\n"
    )
    return prompt


async def call_copilot_sdk(prompt: str, model: str) -> str:
    client = CopilotClient()
    await client.start()

    try:
        session = await client.create_session({
            "model": model,
            "streaming": False,
            "on_permission_request": PermissionHandler.approve_all
        })

        # Use event-based approach instead of send_and_wait
        result_content = []
        done = asyncio.Event()

        def on_event(event):
            if event.type.value == "assistant.message":
                result_content.append(event.data.content)
            elif event.type.value == "session.idle":
                done.set()

        session.on(on_event)

        # Send the prompt
        await session.send({"prompt": prompt})

        # Wait with a longer timeout (3 minutes for large prompts)
        await asyncio.wait_for(done.wait(), timeout=620.0)

        if not result_content:
            raise HTTPException(status_code=500, detail="No response received from Copilot")

        content = result_content[0].strip()

        # Clean up markdown fences if any
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

        return content

    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Copilot took too long to respond. Try a shorter prompt or fewer examples.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Copilot SDK error: {str(e)}")
    finally:
        await session.disconnect()
        await client.stop()


@app.get("/")
async def root():
    return {"message": "Swagger Generator API is running"}


@app.get("/models")
async def list_models():
    return {
        "models": [
            {"id": "claude-sonnet-4.5", "name": "Claude Sonnet 4.5 (Recommended)", "description": "Premium — high token limit, strong reasoning"},
            {"id": "gpt-4.1", "name": "GPT-4.1", "description": "Premium — great for code/YAML"},
            {"id": "gpt-4o", "name": "GPT-4o", "description": "Fast and capable"},
            {"id": "claude-opus-4", "name": "Claude Opus 4", "description": "Most powerful"},
        ]
    }


@app.post("/generate", response_class=PlainTextResponse)
async def generate_swagger(
    model: str = Form(default="claude-sonnet-4.5"),
    input_story: UploadFile = File(...),
    example_story_1: Optional[UploadFile] = File(default=None),
    example_swagger_1: Optional[UploadFile] = File(default=None),
    example_story_2: Optional[UploadFile] = File(default=None),
    example_swagger_2: Optional[UploadFile] = File(default=None),
    example_story_3: Optional[UploadFile] = File(default=None),
    example_swagger_3: Optional[UploadFile] = File(default=None),
):
    new_story_content = (await input_story.read()).decode("utf-8")

    examples = []
    pairs = [
        (example_story_1, example_swagger_1),
        (example_story_2, example_swagger_2),
        (example_story_3, example_swagger_3),
    ]

    for story_file, swagger_file in pairs:
        if story_file and swagger_file:
            story_content = (await story_file.read()).decode("utf-8")
            swagger_content = (await swagger_file.read()).decode("utf-8")
            if story_content.strip() and swagger_content.strip():
                examples.append({"story": story_content, "swagger": swagger_content})

    if not examples:
        raise HTTPException(
            status_code=400,
            detail="Please provide at least one example pair (user story + swagger YAML)."
        )

    prompt = build_prompt(examples, new_story_content)
    result = await call_copilot_sdk(prompt, model)
    return result


@app.post("/validate-pat")
async def validate_pat():
    """
    With Copilot SDK, auth is handled by the CLI itself.
    This endpoint just checks if the CLI is reachable.
    """
    try:
        client = CopilotClient()
        await client.start()
        await client.stop()
        return {"valid": True, "message": "Copilot CLI is authenticated and ready"}
    except Exception as e:
        return {"valid": False, "message": f"Copilot CLI error: {str(e)}"}