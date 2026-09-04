import sys
from pathlib import Path
from fastapi.staticfiles import StaticFiles

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import gradio as gr
import spaces
from app.main import app as fastapi_app
from app.websocket.chat_ws import router as chat_ws_router

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

# Include all FastAPI API routes directly into Gradio's underlying FastAPI app
demo.app.include_router(fastapi_app.router)
demo.app.include_router(chat_ws_router)

# Health endpoint at root /health
@demo.app.get("/health", tags=["System"])
async def health_check():
    return {"status": "ok", "env": "production", "platform": "huggingface"}

# Static uploads
_uploads_dir = Path(__file__).resolve().parent / "uploads"
_uploads_dir.mkdir(exist_ok=True)
demo.app.mount("/uploads", StaticFiles(directory=str(_uploads_dir)), name="uploads")

# Launch Gradio server which binds to 0.0.0.0:7860 and registers ZeroGPU
demo.queue().launch(server_name="0.0.0.0", server_port=7860)
