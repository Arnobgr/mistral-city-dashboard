from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import os
from dotenv import load_dotenv

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
MAX_AGENT_ITERATIONS = int(os.getenv("MAX_AGENT_ITERATIONS", "10"))

# Pydantic models
class DashboardRequest(BaseModel):
    city: str = Field(..., min_length=1)

class DashboardResponse(BaseModel):
    data: dict
    duration_seconds: float
    iterations: int

@app.post("/api/dashboard")
async def get_dashboard(request: DashboardRequest):
    # Placeholder for agentic loop implementation
    return {
        "data": {
            "city": request.city,
            "summary": "This is a placeholder summary.",
            "metrics": []
        },
        "duration_seconds": 0.0,
        "iterations": 0
    }

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
