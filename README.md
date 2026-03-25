# ⚡ Swagger Generator

Generate **OpenAPI/Swagger YAML files automatically from user stories** using GitHub Copilot CLI as the AI backbone — no direct API keys required.

---

## 🧠 How It Works

This tool uses **few-shot learning** — you provide example pairs of (user story + swagger YAML), and the AI learns your structure and generates a matching Swagger file for any new user story.

```
You upload examples (user story + swagger YAML)
            ↓
You upload a new user story
            ↓
FastAPI backend builds a few-shot prompt
            ↓
GitHub Copilot CLI processes it (Claude Sonnet / GPT-4.1 etc.)
            ↓
Generated Swagger YAML returned & ready to download
```

---

## 🗂️ Project Structure

```
swagger-gen/
│
├── backend/
│   └── main.py              # FastAPI app — all endpoints + Copilot SDK logic
│
├── frontend/
│   └── app.py               # Streamlit UI
│
├── learning/
│   ├── example_story_1.txt  # Sample user story (ready to use for testing)
│   └── example_swagger_1.yaml # Corresponding Swagger YAML
│
├── requirements.txt         # All dependencies
└── README.md
```

---

## ⚙️ Prerequisites

### 1. Node.js
Required to install GitHub Copilot CLI.
Download from: https://nodejs.org

### 2. GitHub Copilot CLI
```bash
npm install -g @github/copilot
```

### 3. Authenticate Copilot CLI
```bash
copilot auth login
```
Follow the browser prompt to authenticate with your GitHub account.
Make sure your account has an active **GitHub Copilot Pro** plan.

### 4. Python 3.11 or 3.12 ensure , .venv is present
Python 3.14 has known SSL compatibility issues — stick to 3.11 or 3.12.

---

## 🚀 Setup & Running

### Step 1 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 2 — Start the backend
```bash
cd backend
uvicorn main:app --reload --port 8000 --timeout-keep-alive 600
```
Backend runs at: `http://localhost:8000`
API docs at: `http://localhost:8000/docs`

### Step 3 — Start the frontend
```bash
cd frontend
streamlit run app.py
```
Frontend opens at: `http://localhost:8501`

---

## 🖥️ How to Use

1. **Check Copilot Status** — click the status button to confirm Copilot CLI is authenticated
2. **Select a model** — Claude Sonnet 4.5 recommended for large files
3. **Upload learning examples** — 1 to 3 pairs of (user story + swagger YAML)
4. **Upload your new user story** — the one you want to convert
5. **Click Generate** — wait for the AI to process (large files may take 2-5 minutes)
6. **Download** the generated Swagger YAML

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/models` | List available Copilot models |
| POST | `/validate-pat` | Check Copilot CLI auth status |
| POST | `/generate` | Generate Swagger YAML |

---

## 🤖 Supported Models

| Model ID | Description |
|----------|-------------|
| `claude-sonnet-4.5` | ✅ Recommended — best for large files |
| `gpt-4o` | Fast and capable |
