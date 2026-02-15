FROM python:3.11-slim

WORKDIR /app

# Install lyzr-kit with all needed files
COPY lyzr-kit/ ./lyzr-kit/
RUN pip install --no-cache-dir ./lyzr-kit

# Copy lyzr-skills
COPY lyzr-skills/ ./lyzr-skills/

# Install FastAPI + pyyaml
RUN pip install --no-cache-dir fastapi uvicorn pyyaml

COPY <<'ENTRYPOINT' /app/server.py
import os
import sys
sys.path.insert(0, "/app/lyzr-skills")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

app = FastAPI(title="Lyzr Skills & Kit API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/", response_class=HTMLResponse)
def root():
    return """
    <!DOCTYPE html>
    <html><head><title>Lyzr Skills & Kit</title>
    <style>
        body { font-family: system-ui; background: #0f172a; color: #e2e8f0; max-width: 900px; margin: 0 auto; padding: 40px; }
        h1 { color: #38bdf8; } .card { background: #1e293b; padding: 20px; border-radius: 12px; margin: 15px 0; }
        a { color: #38bdf8; } code { background: #334155; padding: 2px 6px; border-radius: 4px; }
    </style></head><body>
    <h1>Lyzr Skills & Kit</h1>
    <div class="card"><h2>Skills Adapters</h2><p>OpenAI, Claude, Gemini adapters for LLM skills</p>
    <p><a href="/api/skills/adapters">/api/skills/adapters</a></p></div>
    <div class="card"><h2>Lyzr Kit CLI</h2><p>Agent management: <code>lk ls</code>, <code>lk get</code>, <code>lk chat</code></p>
    <p><a href="/api/kit/agents">/api/kit/agents</a></p></div>
    <div class="card"><h2>API Docs</h2><p><a href="/docs">/docs</a></p></div>
    </body></html>"""

@app.get("/api/health")
def health():
    return {"status": "healthy"}

@app.get("/api/skills/adapters")
def list_adapters():
    try:
        from adapters import ClaudeAdapter, OpenAIAdapter, GeminiAdapter
        return {"adapters": ["openai", "claude", "gemini"], "status": "loaded"}
    except Exception as e:
        return {"adapters": [], "error": str(e)}

@app.get("/api/kit/agents")
def list_kit_agents():
    try:
        from pathlib import Path
        import yaml
        agents_dir = Path("/app/lyzr-kit/src/lyzr_kit/collection/agents")
        agents = []
        if agents_dir.exists():
            for f in agents_dir.glob("*.yaml"):
                agents.append(f.stem)
        return {"agents": agents, "count": len(agents)}
    except Exception as e:
        return {"agents": [], "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
ENTRYPOINT

EXPOSE 8000

CMD ["python", "server.py"]
