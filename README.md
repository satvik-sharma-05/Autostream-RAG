# AutoStream Agent

AI-powered conversational lead generation agent for AutoStream — a video editing SaaS platform.

## Architecture

```
User (Chat UI) → FastAPI → LangGraph Agent → Groq LLM (Llama 3.3 70B)
                                ↓
                         ChromaDB (RAG)
                                ↓
                      Lead Capture Tool → In-memory store
```

**Stack:** Python 3.11 · FastAPI · LangGraph · Groq · ChromaDB · sentence-transformers · React + Vite

---

## Quick Start (Local)

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # fill in GROQ_API_KEY
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 for the chat UI.  
Open http://localhost:5173/dashboard for the leads dashboard.  
Open http://localhost:8000/docs for Swagger API docs.

### Docker (one command)

```bash
docker-compose up --build
```

---

## Agent Flow

1. User sends message → intent classified via Groq
2. RAG retrieves relevant context from ChromaDB knowledge base
3. LLM generates response using context
4. On `high_purchase_intent` → agent starts collecting name → email → platform
5. Once all 3 fields collected → `capture_lead` tool fires → lead saved

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/chat` | Send message to agent |
| GET | `/api/v1/leads` | List all captured leads |
| GET | `/api/v1/leads/export` | Download leads as CSV |
| GET | `/api/v1/webhook/whatsapp` | WhatsApp webhook verification |
| POST | `/api/v1/webhook/whatsapp` | Receive WhatsApp messages |
| GET | `/health` | Health check |

---

## WhatsApp Integration

### Setup

1. Create a Meta Developer account at https://developers.facebook.com
2. Create an app → Add "WhatsApp" product
3. Get your `WHATSAPP_TOKEN` and `PHONE_NUMBER_ID` from the dashboard
4. Set `WHATSAPP_VERIFY_TOKEN` in `.env` (any string you choose)

### Local Testing with ngrok

```bash
ngrok http 8000
# Copy the https URL, e.g. https://abc123.ngrok.io
```

Set webhook URL in Meta dashboard: `https://abc123.ngrok.io/api/v1/webhook/whatsapp`

### Message Flow

```
WhatsApp User → Meta Cloud API → POST /webhook/whatsapp
                                        ↓
                                  LangGraph Agent
                                        ↓
                              Response → WhatsApp Cloud API → User
```

### Sample Webhook Payload

```json
{
  "entry": [{
    "changes": [{
      "value": {
        "messages": [{
          "from": "1234567890",
          "text": { "body": "What are your plans?" }
        }]
      }
    }]
  }]
}
```

---

## Deployment

### Render (Backend)

1. Push to GitHub
2. New Web Service → connect repo → set root to `backend/`
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables from `.env.example`
6. Add a Disk: mount path `/app/data` (for ChromaDB persistence)

### Vercel (Frontend)

1. Import GitHub repo → set root to `frontend/`
2. Framework: Vite
3. Add env var: `VITE_API_URL=https://your-render-url.onrender.com`

---

## Tests

```bash
cd backend
pytest tests/ -v
```

11 tests covering intent classification, RAG retrieval, lead capture, and API endpoints.

---

## Environment Variables

See `backend/.env.example` for all required variables.
