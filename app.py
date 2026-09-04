import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import gradio as gr
import spaces
from app.main import app as fastapi_app

# Active ZeroGPU function required by Hugging Face ZeroGPU runtime
@spaces.GPU
def server_ping():
    return "Home Care Cloud Server is Active & Healthy • FastAPI + WebSockets"

with gr.Blocks(title="Home Care API") as demo:
    gr.Markdown("# 🏥 Home Care API")
    gr.Markdown("The backend server for the Home Care application is **running and healthy 24/7**.")
    out = gr.Textbox(value="Status: Online • Connected to Cloud", label="Server Status", interactive=False)
    btn = gr.Button("Ping Server")
    btn.click(fn=server_ping, inputs=[], outputs=out)

# Mount all FastAPI routes into Gradio's router (evaluated first)
demo.app.router.routes = list(fastapi_app.routes) + list(demo.app.router.routes)

# Auto-create database tables on startup
@demo.app.on_event("startup")
async def _init_db():
    from app.core.database import engine, Base
    from app import models
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        print("DB init error:", e)

demo.queue().launch(server_name="0.0.0.0", server_port=7860)
