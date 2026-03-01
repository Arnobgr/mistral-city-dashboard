from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
import logging
import os
import sys
from pathlib import Path
import httpx
from dotenv import load_dotenv


class FlushingStreamHandler(logging.StreamHandler):
    """Handler that flushes after each log so output appears in real time."""

    def emit(self, record):
        super().emit(record)
        self.flush()


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[FlushingStreamHandler(sys.stderr)],
    force=True,
)
log = logging.getLogger("main")
from agent import DashboardAgent
from mcp_client import MCPClient
from models import DashboardData, DashboardRequest, DashboardResponse, TTSRequest
import time

try:
    from mistralai.models.sdkerror import SDKError
except ImportError:
    SDKError = Exception  # fallback if SDK structure changes

# Load environment variables from project root
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MCP_BASE_URL = os.getenv("MCP_BASE_URL", "https://mcp.data.gouv.fr/mcp")
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "mistral-large-latest")
MAX_AGENT_ITERATIONS = int(os.getenv("MAX_AGENT_ITERATIONS", "15"))

# Initialize MCP client and agent
mcp_client = MCPClient(base_url=MCP_BASE_URL)
if not MISTRAL_API_KEY:
    raise ValueError("MISTRAL_API_KEY environment variable is required")

agent = DashboardAgent(
    mcp_client=mcp_client,
    mistral_api_key=MISTRAL_API_KEY,
    model=MISTRAL_MODEL
)

@app.on_event("startup")
async def startup_event():
    """Fetch and cache MCP tool definitions at startup."""
    log.info("Initializing MCP tools...")
    await agent.initialize_tools()
    log.info("MCP tools initialized")

@app.post("/api/dashboard")
async def get_dashboard(request: DashboardRequest):
    start_time = time.time()
    log.info("Dashboard request received for city: %s", request.city)

    try:
        # Run the agentic loop
        dashboard_data, iterations = await agent.run_dashboard_agent(request.city)
        duration_seconds = time.time() - start_time

        log.info("Dashboard completed for %s in %.2fs (%d iterations)", request.city, duration_seconds, iterations)
        return DashboardResponse(
            data=dashboard_data,
            duration_seconds=duration_seconds,
            iterations=iterations
        )
    except RuntimeError as e:
        log.warning("Dashboard failed for %s: %s", request.city, e)
        if "failed to complete after" in str(e).lower():
            raise HTTPException(status_code=504, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))
    except SDKError as e:
        err_msg = str(e)
        log.warning("Mistral SDK error for %s: %s", request.city, err_msg)
        if "401" in err_msg or "Unauthorized" in err_msg:
            raise HTTPException(
                status_code=401,
                detail="Mistral API key invalid or missing. Set MISTRAL_API_KEY in .env with a valid key from https://console.mistral.ai/"
            )
        raise HTTPException(status_code=502, detail=f"Mistral API error: {err_msg}")
    except Exception as e:
        log.exception("Unexpected error for %s", request.city)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


# ElevenLabs TTS Configuration
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")


@app.post("/api/tts")
async def text_to_speech(body: TTSRequest):
    """Convert text to speech using ElevenLabs API."""
    if not ELEVENLABS_API_KEY:
        raise HTTPException(status_code=501, detail="TTS not configured")

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY, 
        "Content-Type": "application/json",
        "Accept": "audio/mpeg"
    }
    payload = {
        "text": body.text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            try:
                error_data = response.json()
                error_message = error_data.get("detail", {}).get("message", "ElevenLabs API error")
                raise HTTPException(status_code=response.status_code, detail=error_message)
            except:
                raise HTTPException(status_code=response.status_code, detail="ElevenLabs API error")
        
        return Response(content=response.content, media_type="audio/mpeg")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    await mcp_client.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
