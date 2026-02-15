FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY governor/ ./governor/

RUN pip install --no-cache-dir ".[fastapi]" uvicorn

COPY <<'ENTRYPOINT' /app/run_server.py
import asyncio
import os
from governor.dashboard.server import create_dashboard

async def main():
    port = int(os.environ.get("PORT", "8765"))
    dashboard = create_dashboard(host="0.0.0.0", port=port)
    await dashboard.start()

if __name__ == "__main__":
    asyncio.run(main())
ENTRYPOINT

EXPOSE 8765

CMD ["python", "run_server.py"]
