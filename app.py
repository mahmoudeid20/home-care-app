import sys
from pathlib import Path
from fastapi.staticfiles import StaticFiles

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import gradio as gr
import spaces
import uvicorn
from app.main import app as fastapi_app

# Active ZeroGPU function required by Hugging Face ZeroGPU runtime
@spaces.GPU
def server_status(name: str = "Client"):
    return f"Home Care Cloud Backend is Online for {name} • FastAPI + WebSockets Active"

# Gradio Interface that registers the ZeroGPU function
demo = gr.Interface(
    fn=server_status,
    inputs="text",
    outputs="text",
    title="Home Care API Status",
    description="Backend service for Home Care application running 24/7."
)

# Mount Gradio onto the root FastAPI application at /gradio
# This ensures all /api/v1/... and /health and /ws/... routes belong directly to FastAPI!
app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")

# Auto-create database tables on startup
@app.on_event("startup")
async def _init_db():
    from app.core.database import engine, Base
    from app import models
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        print("DB init error:", e)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
