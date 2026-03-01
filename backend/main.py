from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
import sys
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
from models import DashboardData, DashboardRequest, DashboardResponse
import time

try:
    from mistralai.models.sdkerror import SDKError
except ImportError:
    SDKError = Exception  # fallback if SDK structure changes

# Load environment variables
load_dotenv()

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

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    await mcp_client.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
