# PRD — Civic Data Dashboard ("Ma Ville en Chiffres")

## 1. Overview

**Product name:** Ma Ville en Chiffres  
**Tagline:** *Any French city. Real government data. Instant insights.*  
**Built for:** Mistral Hackathon  
**Stack:** Python 3.11+ · FastAPI · Mistral API (`mistral-large-latest`) · datagouv MCP server · React 18 · TypeScript · Recharts · Docker Compose  

The app lets a user type any French city, commune, or département name and get an auto-assembled civic dashboard: population trend, unemployment rate, housing prices, and more — all sourced live from data.gouv.fr via an AI agentic loop.

---

## 2. Goals & Non-Goals

### Goals
- Demonstrate Mistral function-calling + MCP integration end-to-end.
- Return a structured, visually rich dashboard from a single text input.
- Keep the codebase small and demo-able in < 5 minutes.

### Non-Goals
- User accounts, authentication, persistence.
- Support for non-French territories (out of scope for hackathon).
- Real-time data streaming to the frontend (polling is fine).
- Mobile-first design (desktop-first is sufficient).

---

## 3. Architecture

```
┌─────────────────────────────────────────────────┐
│                React Frontend                   │
│  - Search input                                 │
│  - Dashboard grid (KPI cards + charts)          │
│  - Loading state with step-by-step progress     │
└───────────────┬─────────────────────────────────┘
                │ HTTP (REST)
┌───────────────▼─────────────────────────────────┐
│              FastAPI Backend                    │
│  POST /api/dashboard  →  agentic loop           │
│    1. Build Mistral messages + tool definitions │
│    2. Call Mistral /v1/chat/completions         │
│    3. If tool_calls → execute MCP calls         │
│    4. Append tool results, loop                 │
│    5. Parse final JSON → return to frontend     │
└───────────────┬─────────────────────────────────┘
                │ HTTP (Streamable MCP)
┌───────────────▼─────────────────────────────────┐
│   data.gouv.fr MCP Server (hosted)              │
│   https://mcp.data.gouv.fr/mcp                 │
│   Tools: search_datasets, get_dataset_info,     │
│          list_dataset_resources,                │
│          query_resource_data,                   │
│          download_and_parse_resource            │
└─────────────────────────────────────────────────┘
```

---

## 4. Repository Structure

```
civic-dashboard/
├── backend/
│   ├── main.py               # FastAPI app entrypoint
│   ├── agent.py              # Agentic loop (Mistral + MCP)
│   ├── mcp_client.py         # HTTP client for datagouv MCP
│   ├── models.py             # Pydantic request/response models
│   ├── prompts.py            # System prompt constants
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── SearchBar.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── KPICard.tsx
│   │   │   ├── LineChartWidget.tsx
│   │   │   ├── BarChartWidget.tsx
│   │   │   └── LoadingOverlay.tsx
│   │   ├── api.ts            # Fetch wrapper for backend
│   │   └── types.ts          # TypeScript interfaces
│   ├── package.json
│   ├── vite.config.ts
│   ├── nginx.conf            # Serves built frontend + proxies /api
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 5. Backend Specification

### 5.1 Environment Variables

```
MISTRAL_API_KEY=<your key>
MCP_BASE_URL=https://mcp.data.gouv.fr/mcp   # or http://localhost:8000/mcp
MISTRAL_MODEL=mistral-large-latest
MAX_AGENT_ITERATIONS=10
```

### 5.2 `mcp_client.py` — MCP HTTP Client

Implements a minimal async MCP client using the **Streamable HTTP transport**.

MCP uses JSON-RPC 2.0 over HTTP. Each tool call is a `POST` to `/mcp` with the following body:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "<tool_name>",
    "arguments": { ... }
  }
}
```

The response is a JSON-RPC result with a `content` array of `{ "type": "text", "text": "..." }` objects.

**Functions to implement:**

```python
async def call_tool(tool_name: str, arguments: dict) -> str:
    """Call an MCP tool and return the text content as a string."""

async def list_tools() -> list[dict]:
    """Fetch available tools from the MCP server (used at startup to build Mistral tool definitions)."""
```

Use `httpx.AsyncClient` for all requests. Set a 30-second timeout.

### 5.3 `agent.py` — Agentic Loop

```python
async def run_dashboard_agent(city: str) -> DashboardData:
    """
    Run the full agentic loop for a given city name.
    Returns a structured DashboardData object.
    """
```

**Loop logic:**

1. Build `messages` list with the system prompt and a user message: `"Build a civic dashboard for: {city}"`.
2. Call `mistral_client.chat.complete(model=MISTRAL_MODEL, tools=TOOL_DEFINITIONS, tool_choice="auto", messages=messages)`.
3. If `response.choices[0].finish_reason == "tool_calls"`:
   - Extract all `tool_calls` from the assistant message.
   - Append the assistant message to `messages`.
   - For each tool call, call `mcp_client.call_tool(name, args)` **concurrently** using `asyncio.gather`.
   - Append each result as a `{"role": "tool", "tool_call_id": ..., "content": ...}` message.
   - Go back to step 2.
4. If `finish_reason == "stop"`: parse the final message content as JSON → return `DashboardData`.
5. If iterations exceed `MAX_AGENT_ITERATIONS`: raise a timeout error.

**Tool definitions** (passed to Mistral) are built dynamically by calling `mcp_client.list_tools()` on startup and converting MCP tool schemas to Mistral's `{ "type": "function", "function": { "name", "description", "parameters" } }` format.

### 5.4 `prompts.py` — System Prompt

```
You are a civic data analyst. Given a French city or territory name, you must:

1. Search data.gouv.fr for the most relevant official datasets on: 
   population, unemployment, housing prices, income, and any other 
   interesting civic metrics available for that territory.

2. For each topic, find the most appropriate dataset, identify the 
   right resource (preferring CSV files), and query the data 
   using query_resource_data.

3. After gathering data from at least 3 different topics, return 
   ONLY a valid JSON object (no markdown, no explanation) 
   matching this exact schema:

{
  "city": "string — canonical city name",
  "summary": "string — 2-3 sentence human-readable summary of key insights",
  "metrics": [
    {
      "id": "string — snake_case identifier e.g. population_trend",
      "title": "string — display title e.g. Population Trend",
      "type": "kpi | line_chart | bar_chart",
      "unit": "string — e.g. inhabitants, %, €",
      "source_dataset": "string — dataset title from data.gouv.fr",
      "source_url": "string — URL to the dataset on data.gouv.fr",

      // For type = "kpi":
      "value": "number | string",
      "delta": "number | null — change vs previous period",
      "delta_label": "string | null — e.g. vs 2019",

      // For type = "line_chart" or "bar_chart":
      "data": [{ "label": "string", "value": number }]
    }
  ]
}

Always include at least one metric of each type (kpi, line_chart, bar_chart) 
if data is available. If a topic has no data available, skip it silently.
```

### 5.5 `models.py` — Pydantic Models

```python
class MetricKPI(BaseModel):
    id: str
    title: str
    type: Literal["kpi"]
    unit: str
    source_dataset: str
    source_url: str
    value: Union[float, str]
    delta: Optional[float]
    delta_label: Optional[str]

class DataPoint(BaseModel):
    label: str
    value: float

class MetricChart(BaseModel):
    id: str
    title: str
    type: Literal["line_chart", "bar_chart"]
    unit: str
    source_dataset: str
    source_url: str
    data: list[DataPoint]

Metric = Annotated[Union[MetricKPI, MetricChart], Field(discriminator="type")]

class DashboardData(BaseModel):
    city: str
    summary: str
    metrics: list[Metric]

class DashboardRequest(BaseModel):
    city: str

class DashboardResponse(BaseModel):
    data: DashboardData
    duration_seconds: float
    iterations: int
```

### 5.6 `main.py` — FastAPI App

**Endpoints:**

```
POST /api/dashboard
  Body:    { "city": "Lyon" }
  Returns: DashboardResponse
  Errors:  422 (validation), 504 (agent timeout), 500 (unexpected)

GET /api/health
  Returns: { "status": "ok" }
```

**CORS:** Allow `http://localhost:5173` (Vite dev server) in development.

**Error handling:** Wrap the agent call in try/except. Return a clear JSON error with a `detail` field on failure.

### 5.7 `requirements.txt`

```
fastapi>=0.111
uvicorn[standard]>=0.29
mistralai>=1.0
httpx>=0.27
pydantic>=2.7
python-dotenv>=1.0
```

---

## 6. Frontend Specification

### 6.1 Tech Stack

- React 18 + TypeScript
- Vite (dev server on port 5173)
- Recharts for all charts
- Plain CSS modules (no Tailwind, keep it simple for vibe-coding)

### 6.2 App Flow

```
Landing page (search)
    │
    │ user types city + presses Enter or clicks button
    ▼
Loading state (spinner + "Searching datasets…" message)
    │
    │ POST /api/dashboard resolves
    ▼
Dashboard page
    │
    │ user clicks "← Search again"
    ▼
Landing page
```

### 6.3 Component Details

#### `SearchBar.tsx`
- A centered text input with placeholder `"Entrez une ville, commune ou département..."`
- A submit button labelled `"Analyser"`
- On submit: call `api.fetchDashboard(city)` which POSTs to the backend.
- Disable input + button while loading.

#### `LoadingOverlay.tsx`
- Full-page overlay with a spinner.
- Animated text that cycles through messages every 2 seconds:
  - `"Recherche des jeux de données..."`
  - `"Interrogation de data.gouv.fr..."`
  - `"Analyse des données..."`
  - `"Assemblage du tableau de bord..."`

#### `Dashboard.tsx`
- Header: city name (large), summary text (muted), back button.
- A responsive CSS grid (3 columns on desktop, 1 on mobile) rendering all metrics.
- For each metric, renders the appropriate widget component based on `type`.

#### `KPICard.tsx`
- Props: `title`, `value`, `unit`, `delta`, `delta_label`, `source_dataset`, `source_url`
- Shows: large value + unit, title below, optional delta badge (green if positive, red if negative), source link at bottom.

#### `LineChartWidget.tsx`
- Props: `title`, `data: [{label, value}]`, `unit`, `source_dataset`, `source_url`
- Renders a Recharts `LineChart` with `CartesianGrid`, `XAxis`, `YAxis`, `Tooltip`, `Line`.
- Title above, source link below.

#### `BarChartWidget.tsx`
- Same props as LineChartWidget.
- Renders a Recharts `BarChart`.

### 6.4 `types.ts`

Mirror the backend Pydantic models exactly in TypeScript:

```typescript
export type MetricType = "kpi" | "line_chart" | "bar_chart";

export interface DataPoint {
  label: string;
  value: number;
}

export interface MetricBase {
  id: string;
  title: string;
  type: MetricType;
  unit: string;
  source_dataset: string;
  source_url: string;
}

export interface MetricKPI extends MetricBase {
  type: "kpi";
  value: number | string;
  delta: number | null;
  delta_label: string | null;
}

export interface MetricChart extends MetricBase {
  type: "line_chart" | "bar_chart";
  data: DataPoint[];
}

export type Metric = MetricKPI | MetricChart;

export interface DashboardData {
  city: string;
  summary: string;
  metrics: Metric[];
}

export interface DashboardResponse {
  data: DashboardData;
  duration_seconds: number;
  iterations: number;
}
```

### 6.5 `api.ts`

```typescript
const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export async function fetchDashboard(city: string): Promise<DashboardResponse> {
  const res = await fetch(`${BASE_URL}/api/dashboard`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ city }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail ?? "Unknown error");
  }
  return res.json();
}
```

---

## 7. Visual Design Guidelines

- **Color palette:** French tricolore inspired — deep navy `#003189`, warm white `#F8F8F8`, accent red `#E1000F`. Charts use a muted blue-to-teal gradient series.
- **Typography:** System font stack. City name in bold 2.5rem. Section titles in 1rem semibold uppercase tracking.
- **KPI cards:** White card, subtle box-shadow, 1.5rem border-radius, 160px min-height.
- **Chart cards:** Same card style, 300px fixed height for chart area.
- **Grid gap:** 1.5rem.
- **Loading overlay:** Dark semi-transparent background (`rgba(0,0,0,0.6)`), white spinner, white cycling text.

---

## 8. Key Implementation Notes for Claude Code

1. **MCP initialization:** On FastAPI startup (`@app.on_event("startup")`), call `list_tools()` to fetch tool schemas and cache them as the Mistral tool definitions list. This avoids repeating the call on every request.

2. **JSON-RPC session:** The datagouv MCP server uses Streamable HTTP. Each `POST /mcp` is independent — no persistent session or `initialize` handshake is required for tool calls. Just POST directly with the `tools/call` method.

3. **Parallel tool execution:** When Mistral returns multiple `tool_calls` in one turn, execute all MCP calls concurrently with `asyncio.gather` to minimize latency.

4. **JSON parsing robustness:** Mistral may occasionally wrap the final JSON in markdown fences. Strip `` ```json `` and `` ``` `` before parsing.

5. **Timeout handling:** The full agent loop can take 20-40 seconds for a full dashboard. Set `uvicorn` worker timeout accordingly, and show the animated loading overlay on the frontend to reassure the user.

6. **Development proxy:** In `vite.config.ts`, add a proxy so `/api` → `http://localhost:8000` to avoid CORS in dev:
   ```typescript
   server: { proxy: { '/api': 'http://localhost:8000' } }
   ```
   With this proxy, set `VITE_API_URL` to `""` (empty string) in dev so requests go through Vite.

7. **Error UX:** If the backend returns an error, show it inline in the search bar area (red text below input), not as an alert().

---

## 9. Docker Setup

Docker Compose is the **recommended and primary way to run this project**, both locally and for open-source contributors. It starts the backend and frontend with a single command and requires no local Python or Node installation beyond Docker itself.

### 9.1 `docker-compose.yml`

```yaml
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file: .env
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped
```

The frontend container serves the production-built React app via nginx and proxies all `/api/*` requests to the `backend` service — no CORS issues in production.

### 9.2 `backend/Dockerfile`

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-keep-alive", "120"]
```

Note the `--timeout-keep-alive 120` flag to accommodate the 20-40 second agent loop without connection drops.

### 9.3 `frontend/Dockerfile`

Multi-stage build: Node to build, nginx to serve.

```dockerfile
# Stage 1 — build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2 — serve
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

### 9.4 `frontend/nginx.conf`

```nginx
server {
    listen 80;

    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend:8000/api/;
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
    }
}
```

The `proxy_read_timeout 120s` is critical — without it nginx will cut the connection during the agentic loop.

### 9.5 Running with Docker

```bash
git clone https://github.com/<you>/civic-dashboard.git
cd civic-dashboard
cp .env.example .env
# Edit .env and add your MISTRAL_API_KEY
docker compose up --build
```

App is available at `http://localhost`. That's it.

To stop: `docker compose down`  
To rebuild after code changes: `docker compose up --build`

### 9.6 Running Manually (for development / contributors who prefer it)

**Backend:**
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env  # fill in MISTRAL_API_KEY
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev   # starts on http://localhost:5173
```

In this mode, the Vite dev server proxy (configured in `vite.config.ts`) forwards `/api` calls to `http://localhost:8000`, so no CORS configuration is needed.


## 10. `.env.example`

```
MISTRAL_API_KEY=your_mistral_api_key_here
MCP_BASE_URL=https://mcp.data.gouv.fr/mcp
MISTRAL_MODEL=mistral-large-latest
MAX_AGENT_ITERATIONS=10

# Optional — ElevenLabs TTS (post-MVP feature, see section 12)
# ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
# ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM
```


## 11. Post-MVP Feature: ElevenLabs Text-to-Speech

> **Status:** Optional stretch goal. Implement only after the MVP is fully working.  
> **Effort estimate:** ~1-2 hours.  
> **Dependency:** ElevenLabs account + API key.

### 11.1 Overview

After the dashboard loads, a 🔊 button next to the summary text lets the user hear the city summary read aloud via ElevenLabs TTS. The audio is generated server-side and streamed back to the browser.

### 11.2 Backend Changes

**New endpoint in `main.py`:**

```
POST /api/tts
  Body:    { "text": "Lyon est une ville de..." }
  Returns: audio/mpeg stream
  Errors:  501 if ELEVENLABS_API_KEY not set, 500 if ElevenLabs call fails
```

**Implementation** (add to `main.py`, ~30 lines):

```python
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # default: Rachel

@app.post("/api/tts")
async def text_to_speech(body: TTSRequest):
    if not ELEVENLABS_API_KEY:
        raise HTTPException(status_code=501, detail="TTS not configured")

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}/stream"
    headers = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}
    payload = {
        "text": body.text,
        "model_id": "eleven_multilingual_v2",  # supports French natively
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
    }

    async def stream():
        async with httpx.AsyncClient(timeout=30) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as r:
                r.raise_for_status()
                async for chunk in r.aiter_bytes():
                    yield chunk

    return StreamingResponse(stream(), media_type="audio/mpeg")
```

**New Pydantic model** (add to `models.py`):

```python
class TTSRequest(BaseModel):
    text: str
```

No changes needed to `agent.py`, `mcp_client.py`, `prompts.py`, or `docker-compose.yml`. Just add `ELEVENLABS_API_KEY` and optionally `ELEVENLABS_VOICE_ID` to `.env`.

Use `eleven_multilingual_v2` — it handles French text natively with no language configuration needed.

### 11.3 Frontend Changes

**`api.ts`** — add one function:

```typescript
export async function fetchTTS(text: string): Promise<Blob> {
  const res = await fetch(`${BASE_URL}/api/tts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) throw new Error("TTS unavailable");
  return res.blob();
}
```

**`Dashboard.tsx`** — add a speaker button next to the summary paragraph:

```tsx
const handleSpeak = async () => {
  const blob = await fetchTTS(data.summary);
  const url = URL.createObjectURL(blob);
  const audio = new Audio(url);
  audio.play();
  audio.onended = () => URL.revokeObjectURL(url);  // cleanup memory
};

// In JSX, next to the summary paragraph:
<button onClick={handleSpeak} title="Écouter le résumé">🔊</button>
```

No new npm packages required — the native browser `Audio` API handles playback.

### 11.4 Docker — No Changes Needed

The backend `Dockerfile` and `docker-compose.yml` require no modifications. The new env vars are picked up automatically via `env_file: .env`. If `ELEVENLABS_API_KEY` is absent, the `/api/tts` endpoint returns `501`; the frontend button can be hidden or disabled accordingly with a simple feature-flag check (e.g. try the endpoint on mount and hide the button if it returns 501).

---

## 12. Demo Script (for hackathon presentation)

1. Open `http://localhost` (Docker) or `http://localhost:5173` (manual dev).
2. Type `"Lyon"` → click Analyser.
3. While loading, explain: *"The AI is searching data.gouv.fr in real-time, finding the right datasets, querying them, and structuring the result."*
4. Dashboard appears → point out: KPI cards (population, unemployment), a line chart (trend over years), a bar chart (comparison).
5. Click source links to show real data.gouv.fr dataset pages.
6. Back → try `"Marseille"` or `"Seine-Saint-Denis"` to show it works for any territory.
7. Highlight the `duration_seconds` and `iterations` metadata to show the agentic loop depth.
8. *(If ElevenLabs implemented)* Click 🔊 on the summary to play the spoken city summary.
