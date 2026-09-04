import sys
from pathlib import Path

# Add backend directory to sys.path so app imports work seamlessly
backend_dir = Path(__file__).resolve().parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import gradio as gr
import spaces
import uvicorn
from app.main import app as fastapi_app

# ZeroGPU requires an active function registered on a Gradio component
@spaces.GPU
def server_status():
    return "Online • FastAPI + WebSockets ready • 24/7 Cloud"

# Create a clean status dashboard for Gradio
with gr.Blocks(title="Home Care API") as demo:
    gr.Markdown("# 🏥 Home Care API")
    gr.Markdown("The backend server for the Home Care application is **running and healthy**.")
    status_display = gr.Textbox(value="Online • FastAPI + WebSockets ready", label="Server Status", interactive=False)
    refresh_btn = gr.Button("Ping Server")
    refresh_btn.click(fn=server_status, inputs=[], outputs=status_display)

# Mount Gradio at /dashboard, while the entire root / and /api/v1 belongs to FastAPI!
app = gr.mount_gradio_app(fastapi_app, demo, path="/dashboard")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
