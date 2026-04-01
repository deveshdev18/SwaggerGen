# ⚡ Swagger Generator

Generate **OpenAPI/Swagger YAML files automatically from user stories** using GitHub Copilot CLI as the AI backbone — no direct API keys required.

---

## 🧠 How It Works

Provide example pairs of (user story + swagger YAML) as learning references. The Copilot agent reads them from disk, learns the structure, and generates a matching Swagger file for any new user story.

```
User uploads examples + new user story via Streamlit
            ↓
FastAPI saves files to learning/ and input/ folders
            ↓
Copilot agent reads files, generates YAML, saves to output/
            ↓
User downloads the generated Swagger YAML
```

---

## 🗂️ Project Structure

```
SwaggerGen/
├── backend/
│   └── main.py              # FastAPI app + Copilot SDK logic
├── frontend/
│   └── app.py               # Streamlit UI
├── learning/                # Example pairs (persisted across runs)
├── input/                   # New user story (cleared each run)
├── output/                  # Generated YAML (cleared each run)
├── requirements.txt
└── README.md
```

---

## ⚙️ Prerequisites

### 1. Node.js
Download from: https://nodejs.org

### 2. GitHub Copilot CLI
```bash
npm install -g @github/copilot
```

### 3. Authenticate
```bash
copilot auth login
```
Requires an active **GitHub Copilot Pro** plan.

### 4. Python 3.11 or 3.12
Ensure a `.venv` is present in your project root.

---

## 🚀 Setup & Running

### Step 1 — Clone and activate virtual environment
```bash
git clone <your-repo-url>
cd SwaggerGen

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

```

### Step 2 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 3 — Start the backend
```bash
cd backend
uvicorn main:app --reload --port 8000 --timeout-keep-alive 600
```

### Step 4 — Start the frontend
```bash
cd frontend
streamlit run app.py
```

---

## 🖥️ How to Use

1. **Check Copilot Status** — confirm CLI is authenticated
2. **Select a model** — Claude Sonnet 4.5 recommended
3. **Upload learning examples** — 1 to 3 pairs of (user story + swagger YAML)
4. **Upload your new user story**
5. **Click Generate** — may take 2–5 minutes for large files
6. **Download** the generated Swagger YAML

> If you've uploaded examples in a previous run, you can skip step 3 — they'll be reused automatically.

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/models` | List available models |
| POST | `/validate-pat` | Check Copilot CLI auth status |
| POST | `/generate` | Generate Swagger YAML |

---

## 🤖 Supported Models

| Model ID | Description |
|----------|-------------|
| `claude-sonnet-4.5` | ✅ Recommended |
| `gpt-4.1` | Great for code/YAML generation |
