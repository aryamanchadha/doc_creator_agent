# Doc Creator Agent

This project has a React frontend (`frontend/src`) and a FastAPI backend (`frontend/backend`) that turns screenshots into HTML documentation via OCR and a Google AI agent.

## Prerequisites

Backend requirements (see `frontend/backend/requirements.txt`) include `fastapi`, `uvicorn`, `pytesseract`, `Pillow`, and `python-dotenv`. Two additional items are required at runtime:

- **Tesseract OCR binary**: Install it for your OS and ensure the `tesseract` executable is on your PATH. On Windows, you may need to set `TESSERACT_CMD` to the full executable path (e.g., `C:\\Program Files\\Tesseract-OCR\\tesseract.exe`).
- **Google API key**: Provide via the `GOOGLE_API_KEY` environment variable (can be set in `frontend/backend/.env`).

## Running the backend

```bash
cd frontend/backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

# Optional: point pytesseract to a non-PATH install
export TESSERACT_CMD="/usr/bin/tesseract"  # adjust for Windows

export GOOGLE_API_KEY="your_api_key"
uvicorn main:app --reload --port 8000
```

If Tesseract is missing, the backend now fails fast at startup and the upload endpoint returns a clear error indicating how to install/configure it.

## Running the frontend

```bash
cd frontend
npm install
npm start
```

The React dev server runs on port 3000 and calls the backend on port 8000.
