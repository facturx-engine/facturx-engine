import os
import subprocess
import sys
import time

import gradio as gr
import httpx

# 1. Start the Backend (FastAPI) in a subprocess
# Forward the environment so that LICENSE_KEY is picked up from Hugging Face Settings
backend_process = subprocess.Popen(
    ["uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
    cwd="/app",  # The original app code is here in the base image
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    env=os.environ.copy()
)

print("Starting Factur-X Engine Backend...")
# Simple wait loop to ensure backend is up
for _ in range(30):
    try:
        r = httpx.get("http://127.0.0.1:8000/health")
        if r.status_code == 200:
            print("Backend is ready!")
            break
    except httpx.ConnectError:
        time.sleep(1)
        print("Waiting for backend...")
else:
    print("Backend failed to start.")
    sys.exit(1)

# 2. Define the Frontend Logic (Client)

def validate_pdf(file):
    if not file:
        return "Please upload a file."
    
    try:
        # Call the local API
        with open(file.name, "rb") as f:
            files = {"file": (os.path.basename(file.name), f, "application/pdf")}
            response = httpx.post("http://127.0.0.1:8000/v1/validate", files=files, timeout=30.0)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": response.text, "status": response.status_code}
            
    except Exception as e:
        return {"error": str(e)}

def extract_xml(file):
    if not file:
        return "Please upload a file."
    
    try:
        with open(file.name, "rb") as f:
            files = {"file": (os.path.basename(file.name), f, "application/pdf")}
            # Pro Endpoint: Serialization instead of raw extraction
            response = httpx.post("http://127.0.0.1:8000/v1/serialize", files=files, timeout=30.0)
            
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": response.text, "status": response.status_code}

    except Exception as e:
        return {"error": str(e)}


# 3. Build the UI
# 3. Helper for HTML Report
def format_validation_report(data):
    if "error" in data:
        return f"""
        <div style="background-color: #fee2e2; border: 1px solid #ef4444; border-radius: 8px; padding: 16px; color: #b91c1c;">
            <h3 style="margin: 0; display: flex; align-items: center;">
                <span style="font-size: 24px; margin-right: 8px;">❌</span> System Error
            </h3>
            <p style="margin: 8px 0 0 0;">{data['error']}</p>
        </div>
        """
    
    is_valid = data.get("valid", False)
    color = "#d1fae5" if is_valid else "#fee2e2"
    border = "#10b981" if is_valid else "#ef4444"
    text_color = "#047857" if is_valid else "#b91c1c"
    icon = "✅" if is_valid else "❌"
    title = "Invoice is Compliance" if is_valid else "Invoice has Errors"
    
    profile = data.get("flavor", "Unknown")
    
    # Extract error count
    errors = data.get("errors", [])
    error_html = ""
    if errors:
        error_html = f"<p style='margin-top: 8px;'><strong>{len(errors)} error(s) found.</strong> See details below.</p>"

    return f"""
    <div style="background-color: {color}; border: 1px solid {border}; border-radius: 8px; padding: 20px; color: {text_color}; margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h3 style="margin: 0; display: flex; align-items: center; font-size: 20px;">
                <span style="margin-right: 12px; font-size: 28px;">{icon}</span> {title}
            </h3>
            <span style="background-color: rgba(255,255,255,0.5); padding: 4px 12px; rounded: 12px; font-weight: bold; border-radius: 20px; font-size: 14px;">
                {profile}
            </span>
        </div>
        {error_html}
    </div>
    """

def validate_pdf_wrapper(file):
    json_result = validate_pdf(file)
    html_report = format_validation_report(json_result)
    return html_report, json_result

# 4. Build the UI
theme = gr.themes.Soft(
    primary_hue="amber",
    neutral_hue="slate",
).set(
    button_primary_background_fill="#f59e0b",
    button_primary_background_fill_hover="#d97706",
    button_primary_text_color="white",
)

css = """
.gradio-container {
    max-width: 1200px !important;
    margin-left: auto !important;
    margin-right: auto !important;
} 
footer {display: none !important}
.center-content {text-align: center; margin-bottom: 20px;}
"""

with gr.Blocks(title="Factur-X Engine", theme=theme, css=css) as demo:
    
    with gr.Row():
        gr.Markdown(
            """
            <div class="center-content">
                <h1>⚡ Factur-X Engine <span style="color: #f59e0b; font-size: 0.6em; vertical-align: middle;">PRO</span></h1>
                <p><b>Official SaxonC Validation</b> | Air-Gapped | Python</p>
            </div>
            """
        )
    
    with gr.Tab("🛡️ Validate Invoice"):
        gr.Markdown("Checks compliance against **EN 16931** (Profile: Comfort, Basic, etc.)")
        
        # Row 1: Upload + Status summary side by side
        with gr.Row():
            with gr.Column(scale=1, min_width=280):
                in_file_val = gr.File(label="📄 Upload PDF Invoice", file_types=[".pdf"])
                btn_val = gr.Button("✅ Check Compliance", variant="primary", size="lg")
            
            with gr.Column(scale=2):
                out_html_val = gr.HTML(
                    label="Status",
                    value='<div style="background-color: #f8fafc; padding: 32px; border-radius: 8px; text-align: center; color: #94a3b8; border: 1px dashed #cbd5e1; height: 100%; box-sizing: border-box;">Upload a PDF and click "Check Compliance"</div>'
                )
        
        # Row 2: Full-width JSON
        with gr.Row():
            out_json_val = gr.JSON(label="📋 Detailed JSON Report")
        
        btn_val.click(validate_pdf_wrapper, inputs=in_file_val, outputs=[out_html_val, out_json_val])

    with gr.Tab("📄 Serialize Data (Pro)"):
        gr.Markdown("Transforms complex Factur-X XML directly into a **normalized, flat JSON** schema for ERPs.")
        
        with gr.Row():
            with gr.Column(scale=1, min_width=280):
                in_file_ext = gr.File(label="📄 Upload PDF Invoice", file_types=[".pdf"])
                btn_ext = gr.Button("⚙️ Serialize JSON", variant="primary", size="lg")
            with gr.Column(scale=2):
                gr.Markdown(
                    '<div style="background-color: #f8fafc; padding: 32px; border-radius: 8px; text-align: center; color: #94a3b8; border: 1px dashed #cbd5e1;">Upload a PDF and click "Serialize JSON"</div>'
                )
        
        with gr.Row():
            out_json_ext = gr.JSON(label="📋 Extracted JSON Data")
                
        btn_ext.click(extract_xml, inputs=in_file_ext, outputs=out_json_ext)

    gr.Markdown(
        """
        <div style="text-align: center; margin-top: 40px; opacity: 0.6; font-size: 12px;">
            Powered by <a href="https://github.com/facturx-engine/facturx-engine" target="_blank" style="color: #f59e0b;">Factur-X Engine</a>. 
            Runs locally in Docker.
        </div>
        """
    )


# 4. Launch
if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
