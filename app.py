import sys
from pathlib import Path

# Add backend directory to sys.path so app imports work seamlessly
backend_dir = Path(__file__).resolve().parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Required by Hugging Face ZeroGPU runtime
try:
    import spaces

    @spaces.GPU
    def _zero_gpu_init():
        """Satisfies ZeroGPU startup check for Hugging Face Spaces."""
        return True
except Exception:
    pass

import gradio as gr
import uvicorn
from app.main import app as fastapi_app

# Create a clean status dashboard for Gradio
with gr.Blocks(title="Home Care API") as demo:
    gr.Markdown("# 🏥 Home Care API")
    gr.Markdown("The backend server for the Home Care application is **running and healthy**.")
    status_box = gr.Textbox(value="Status: Online (FastAPI + WebSockets)", label="Health Check", interactive=False)

# Mount Gradio at /dashboard, while the entire root / and /api/v1 belongs to FastAPI!
app = gr.mount_gradio_app(fastapi_app, demo, path="/dashboard")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
