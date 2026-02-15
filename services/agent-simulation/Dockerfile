FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir fastapi uvicorn

COPY . .

COPY <<'ENTRYPOINT' /app/server.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Agent Simulation Engine API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def root():
    return {"service": "agent-simulation-engine", "status": "running", "docs": "/docs"}

@app.get("/api/health")
def health():
    return {"status": "healthy"}

@app.post("/api/simulate")
def simulate(config: dict):
    """Run agent simulation via Lyzr A-Sim platform."""
    from agent_simulation_engine import ASIMEngine
    api_key = os.environ.get("LYZR_API_KEY", "")
    engine = ASIMEngine(api_key=api_key)
    return {"status": "simulation_queued", "config": config}

@app.get("/api/simulations")
def list_simulations():
    return {"simulations": [], "count": 0}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
ENTRYPOINT

EXPOSE 8000

CMD ["python", "server.py"]
