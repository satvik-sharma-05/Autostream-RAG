# AutoStream Agent

AI-powered conversational lead generation agent for AutoStream — a video editing SaaS platform.

## Architecture

```
User (Chat UI / WhatsApp)
        ↓
   FastAPI (Render)
        ↓
  LangGraph Agent ──── Groq LLM (Llama 3.3 70B)
        ↓
  ChromaDB RAG (persistent disk)
        ↓
  Lead Capture Tool → in-memory store
```

**Stack:** Python 3.11 · FastAPI · LangGraph · Groq · ChromaDB · sentence-transformers · React + Vite

---

## Quick Start (Local)

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env        # add your GROQ_API_KEY
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

| URL | What |
|-----|------|
| http://localhost:5173 | Chat UI |
| http://localhost:5173/dashboard | Leads dashboard |
| http://localhost:8000/docs | Swagger API docs |
| http://localhost:8000/health | Health check |

### Docker (one command)

```bash
docker-compose up --build
```

### Smoke test

```bash
cd backend
python test_api.py
```

---

## Deploying to Render

### Step 1 — Push to GitHub

```bash
git add .
git commit -m "deploy: render config"
git push origin main
```

### Step 2 — Create Render account

Sign up at https://render.com (free tier is enough).

### Step 3 — New Blueprint

1. Dashboard → **New +** → **Blueprint**
2. Connect your GitHub repo
3. Render auto-detects `backend/render.yaml`
4. Click **Apply**

### Step 4 — Add secret env var

In the Render dashboard for your service:

**Environment** tab → **Add Environment Variable**

| Key | Value |
|-----|-------|
| `GROQ_API_KEY` | your key from console.groq.com |

All other variables are already set in `render.yaml`.

### Step 5 — Wait for build (~5-10 min)

Render will:
1. Build the Docker image (downloads sentence-transformers model — baked in)
2. Mount the 5GB persistent disk at `/app/data`
3. Start uvicorn on `$PORT`
4. Hit `/health` to confirm it's up

### Step 6 — Verify

```bash
# Replace with your actual Render URL
export BASE_URL=https://autostream-agent.onrender.com

curl $BASE_URL/health
# {"status":"ok","service":"AutoStream Agent API","startup_seconds":22.4,...}

curl -X POST $BASE_URL/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"hi","session_id":"test1"}'
# {"response":"Hello!...","intent":"greeting","lead_captured":false,...}

# Run full smoke test against production
BASE_URL=https://autostream-agent.onrender.com python backend/test_api.py
```

### Step 7 — Deploy Frontend to Vercel

1. Go to https://vercel.com → **New Project** → import your repo
2. Set **Root Directory** to `frontend`
3. Add env var: `VITE_API_URL=https://autostream-agent.onrender.com`
4. Deploy

Then update `CORS_ORIGINS` in Render to your Vercel URL.

---

## Render Free Tier Notes

**Cold starts:** The service spins down after 15 min of inactivity. First request after sleep takes ~20-30s (model is pre-baked in Docker image, so it's just process startup). The `/health` endpoint responds immediately once up.

**Persistent disk:** ChromaDB writes to `/app/data/chromadb` on the mounted disk — survives restarts and redeploys. The knowledge base is reloaded from `data/knowledge_base.json` on every startup (fast, ~1s after first run).

**Memory:** sentence-transformers/all-MiniLM-L6-v2 uses ~90MB. ChromaDB + FastAPI + LangGraph fits comfortably in 512MB.

**Logs:** All structured JSON logs go to stdout — visible in Render's **Logs** tab.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check (Render pings this) |
| POST | `/api/v1/chat` | Send message to agent |
| GET | `/api/v1/leads` | List all captured leads |
| GET | `/api/v1/leads/export` | Download leads as CSV |
| GET | `/api/v1/webhook/whatsapp` | WhatsApp verification handshake |
| POST | `/api/v1/webhook/whatsapp` | Receive WhatsApp messages |

### Chat request/response

```json
// POST /api/v1/chat
{ "message": "I want to sign up for Pro", "session_id": "user-abc" }

// Response
{
  "response": "Great choice! To get you connected...",
  "session_id": "user-abc",
  "intent": "high_purchase_intent",
  "intent_confidence": 0.9,
  "lead_captured": false,
  "turn_count": 1
}
```

---

## Agent Flow

1. Message arrives → **Layer 1** keyword scan (0ms) — catches "sign up", "buy", "Pro", etc.
2. If no keyword match → **Layer 2** Groq LLM classification (~300ms)
3. RAG retrieves top-3 relevant chunks from ChromaDB (cosine similarity)
4. LLM generates response using retrieved context
5. On `high_purchase_intent` → collect name → email → platform (one field per turn)
6. Smart parser handles combined input like `"Name: Satvik Email: foo@bar.com"`
7. All 3 fields collected → `capture_lead` tool fires → lead stored

---

## WhatsApp Integration

### Setup

1. Meta Developer account → https://developers.facebook.com
2. Create app → Add **WhatsApp** product
3. Get `WHATSAPP_TOKEN` and `PHONE_NUMBER_ID` from the dashboard
4. Set `WHATSAPP_VERIFY_TOKEN` in env (any string)

### Local testing with ngrok

```bash
ngrok http 8000
# Set webhook URL in Meta dashboard:
# https://abc123.ngrok.io/api/v1/webhook/whatsapp
```

### Message flow

```
WhatsApp User → Meta Cloud API → POST /api/v1/webhook/whatsapp
                                          ↓
                                   LangGraph Agent
                                          ↓
                              WhatsApp Cloud API → User
```

---

## Tests

```bash
cd backend
pytest tests/ -v
# 11 tests — intent, RAG, lead capture, API endpoints
```

---

## Environment Variables

See `backend/.env.example` for all variables with descriptions.
