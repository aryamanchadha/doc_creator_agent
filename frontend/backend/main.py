import os
import base64
import uuid
import re
import shutil
from datetime import datetime
from typing import List

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from google.adk.agents import Agent
from PIL import Image
import pytesseract

# Load environment variables from .env file
load_dotenv()

# Check if the API key is set
if not os.getenv("GOOGLE_API_KEY"):
    raise ValueError("GOOGLE_API_KEY not found in .env file")


def configure_tesseract():
    """Validate that the Tesseract binary is available and allow overrides.

    We avoid raising at import time so the server can still boot and return a
    clearer runtime error with platform-specific guidance.
    """
    custom_tesseract_cmd = os.getenv("TESSERACT_CMD")
    if custom_tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = custom_tesseract_cmd

    tesseract_in_path = shutil.which(pytesseract.pytesseract.tesseract_cmd)
    if not tesseract_in_path:
        # Log a warning but allow the app to start; requests will return a clear
        # HTTP error if Tesseract is still missing at runtime.
        print(
            "Warning: Tesseract OCR binary not found. Install Tesseract and "
            "ensure it is on your PATH or set TESSERACT_CMD to the full "
            "executable path (e.g., C:\\Program Files\\Tesseract-OCR\\tesseract.exe)."
        )
        return False

    return True


TESSERACT_AVAILABLE = configure_tesseract()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define the documentation agent
doc_agent = Agent(
    name="doc_agent",
    instruction="You are a technical writer. Your task is to analyze a conversation about a technical issue and its resolution. "
                "Based on the text provided, identify the core problem and the final solution. "
                "Structure your output with 'Issue:', 'Explanation:', and 'Fix:'.",
)

def generate_html_document(analysis_text: str, image_paths: List[str]) -> str:
    """Generates an HTML document from the analysis and images."""
    html_content = f"""
    <html>
    <head>
        <title>Issue and Fix Documentation</title>
        <style>
            body {{ font-family: sans-serif; margin: 2em; }}
            h1 {{ color: #333; }}
            h2 {{ color: #555; border-bottom: 1px solid #ccc; padding-bottom: 5px; }}
            p {{ line-height: 1.6; }}
            img {{ max-width: 100%; height: auto; border: 1px solid #ddd; margin-top: 1em; }}
        </style>
    </head>
    <body>
        <h1>Documentation</h1>
    """

    for line in analysis_text.split('\n'):
        if line.startswith('Issue:'):
            html_content += f"<h2>Issue</h2><p>{line.replace('Issue:', '').strip()}</p>"
        elif line.startswith('Explanation:'):
            html_content += f"<h2>Explanation</h2><p>{line.replace('Explanation:', '').strip()}</p>"
        elif line.startswith('Fix:'):
            html_content += f"<h2>Fix</h2><p>{line.replace('Fix:', '').strip()}</p>"
        else:
            html_content += f"<p>{line}</p>"

    html_content += "<h2>Screenshots</h2>"
    for image_path in image_paths:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        html_content += f'<img src="data:image/png;base64,{encoded_string}" alt="Screenshot"><br>'

    html_content += """
    </body>
    </html>
    """
    return html_content

def extract_timestamp(text: str):
    """Extracts a timestamp from the text using a regex."""
    match = re.search(r'\d{1,2}:\d{2}\s?[AP]M', text)
    if match:
        try:
            return datetime.strptime(match.group(), '%I:%M %p').time()
        except ValueError:
            return None
    return None

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/upload-images/")
async def create_upload_files(files: List[UploadFile] = File(...)):
    request_id = str(uuid.uuid4())
    upload_dir = f"uploads/{request_id}"
    os.makedirs(upload_dir, exist_ok=True)

    messages = []
    image_paths = []

    for file in files:
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        image_paths.append(file_path)

        image = Image.open(file_path)
        try:
            if not TESSERACT_AVAILABLE and not shutil.which(
                pytesseract.pytesseract.tesseract_cmd
            ):
                raise pytesseract.TesseractNotFoundError()

            text = pytesseract.image_to_string(image)
        except pytesseract.TesseractNotFoundError as exc:
            raise HTTPException(
                status_code=500,
                detail=(
                    "Tesseract OCR binary is missing. Install Tesseract and ensure it "
                    "is on your PATH or set TESSERACT_CMD to its full path "
                    "(e.g., C:\\Program Files\\Tesseract-OCR\\tesseract.exe)."
                ),
            ) from exc

        timestamp = extract_timestamp(text)

        messages.append({"text": text, "timestamp": timestamp, "filename": file.filename})

    messages.sort(key=lambda x: x['timestamp'] if x['timestamp'] else datetime.min.time())
    combined_text = "\n\n".join([msg['text'] for msg in messages])

    analysis = doc_agent.send(combined_text)

    html_doc = generate_html_document(analysis.text, image_paths)

    for image_path in image_paths:
        os.remove(image_path)
    os.rmdir(upload_dir)

    return HTMLResponse(content=html_doc)
