import logging
import os
import pprint
import re
import secrets
import subprocess
import tempfile
import time
import uuid

import aiofiles
import google.generativeai as genai
from dotenv import load_dotenv
from fastapi import (
    Body,
    Depends,
    FastAPI,
    File,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

logging.basicConfig(level=logging.INFO)

app = FastAPI()

# Set up HTTP Basic Auth
security = HTTPBasic()

# Mount static files directory
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://schulaufgabe-frontend.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
# Counter metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status"],
)
UPLOAD_COUNT = Counter("upload_total", "Total number of file uploads")


# Secure temp directory management
TEMP_ROOT_DIR = tempfile.gettempdir()


def get_secure_temp_dir(session_id):
    """Create and return a secure temporary directory path based on session_id"""
    # Validate session_id format (UUID format only)
    if not isinstance(session_id, str) or not len(session_id) == 36:
        raise ValueError("Invalid session ID format")

    temp_dir = os.path.join(TEMP_ROOT_DIR, "schulaufgabe", session_id)
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir


def run_tectonic(tex_path, output_dir):
    """Securely run the tectonic command with validated paths"""
    # Path validation
    if not os.path.exists(tex_path) or not os.path.isfile(tex_path):
        raise ValueError(f"Invalid TeX file path: {tex_path}")
    if not os.path.exists(output_dir) or not os.path.isdir(output_dir):
        raise ValueError(f"Invalid output directory: {output_dir}")

    # Use absolute path to tectonic binary for better security
    tectonic_path = "/usr/local/bin/tectonic"

    # Execute with strict parameters
    return subprocess.run(
        [
            tectonic_path,
            tex_path,
            "--outdir",
            output_dir,
            "--print",
            "--synctex=none",
            "--keep-logs=no",
            "--keep-intermediates=no",
        ],
        capture_output=True,
        text=True,
        check=True,
    )


LATEX_GENERATION_COUNT = Counter(
    "latex_generation_total", "Total number of LaTeX generations", ["status"]
)
PDF_COMPILATION_COUNT = Counter(
    "pdf_compilation_total", "Total number of PDF compilations", ["status"]
)

# Timing metrics
REQUEST_TIME = Histogram(
    "request_processing_seconds",
    "Time spent processing request",
    ["method", "endpoint"],
)
LATEX_GENERATION_TIME = Histogram(
    "latex_generation_seconds", "Time spent generating LaTeX"
)
PDF_COMPILATION_TIME = Histogram("pdf_compilation_seconds", "Time spent compiling PDF")

# Gauge metrics
ACTIVE_SESSIONS = Gauge("active_sessions", "Number of active sessions")


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    REQUEST_TIME.labels(request.method, request.url.path).observe(process_time)
    REQUEST_COUNT.labels(request.method, request.url.path, response.status_code).inc()
    return response


def verify_prometheus_auth(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify Prometheus metrics access credentials"""
    # Load environment variables if not already loaded
    load_dotenv()

    # Get environment variables
    correct_username = os.getenv("METRICS_USERNAME")
    correct_password = os.getenv("METRICS_PASSWORD")

    # Ensure environment variables are loaded and not None
    if not correct_username or not correct_password:
        logging.error("METRICS_USERNAME or METRICS_PASSWORD not set in environment")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error: Metrics authentication not properly configured",
        )

    is_correct_username = secrets.compare_digest(credentials.username, correct_username)
    is_correct_password = secrets.compare_digest(credentials.password, correct_password)

    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials


@app.get("/metrics")
async def metrics(credentials: HTTPBasicCredentials = Depends(verify_prometheus_auth)):
    # Ensure the response has proper headers for production
    content = generate_latest()
    response = PlainTextResponse(content, media_type=CONTENT_TYPE_LATEST)
    # Add CORS headers explicitly for this endpoint
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    return response


# Adding an API version of the metrics endpoint as a fallback


@app.get("/api/metrics")
async def api_metrics(
    credentials: HTTPBasicCredentials = Depends(verify_prometheus_auth),
):
    content = generate_latest()
    response = PlainTextResponse(content, media_type=CONTENT_TYPE_LATEST)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    return response


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Serve favicon.ico"""
    return FileResponse(os.path.join(static_dir, "favicon.ico"))


@app.get("/")
async def root():
    """Health check endpoint for CI and monitoring"""
    return {"status": "ok", "service": "schulaufgabe-backend"}


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    UPLOAD_COUNT.inc()
    session_id = str(uuid.uuid4())
    upload_dir = get_secure_temp_dir(session_id)
    file_path = os.path.join(upload_dir, "input.jpg")
    logging.info(f"[UPLOAD] Saving uploaded file to {file_path}")
    async with aiofiles.open(file_path, "wb") as out_file:
        content = await file.read()
        await out_file.write(content)
    logging.info(f"[UPLOAD] File saved. Returning session_id: {session_id}")
    ACTIVE_SESSIONS.inc()
    return JSONResponse({"session_id": session_id})


@app.post("/api/generate-latex", response_class=PlainTextResponse)
async def generate_latex(session_id: str = Body(..., embed=True)):
    """
    Receives a session_id, loads the image, sends it to Gemini, and returns LaTeX.
    """
    start_time = time.time()
    load_dotenv()

    # Check if we're in test mode
    TEST_MODE = os.getenv("TEST_MODE", "0") == "1"
    if TEST_MODE:
        logging.info("[TEST MODE] Running in test mode with mock responses")
        # Return a successful mock response
        mock_latex = r"\documentclass{article}\usepackage{amsmath}\begin{document}\section*{Test Worksheet}\begin{enumerate}\item $2+2=4$\item $\frac{1}{2} + \frac{1}{3} = \frac{5}{6}$\end{enumerate}\end{document}"
        return PlainTextResponse(mock_latex, media_type="text/plain")

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logging.error("[GEMINI] GOOGLE_API_KEY not set in environment.")
        return PlainTextResponse("Gemini API key not set", status_code=500)
    genai.configure(api_key=api_key)
    image_path = os.path.join(get_secure_temp_dir(session_id), "input.jpg")
    logging.info(
        f"[LATEX] Generating LaTeX for session_id={session_id}, image_path={image_path}"
    )
    if not os.path.exists(image_path):
        logging.error(f"[LATEX] Image not found: {image_path}")
        return PlainTextResponse("Image not found", status_code=404)

    # Read image as bytes
    with open(image_path, "rb") as img_file:
        image_bytes = img_file.read()

    # Prepare prompt (load from gemini_system_prompt.txt)
    prompt_path = os.path.join(os.path.dirname(__file__), "gemini_system_prompt.txt")
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt = f.read().strip()
    except Exception as e:
        logging.error(f"[PROMPT] Could not read prompt file: {e}")
        return PlainTextResponse("Prompt file error", status_code=500)

    try:
        model_name = "gemini-2.0-flash"
        logging.info(f"[GEMINI] Using model: {model_name}")
        logging.info(
            f"[GEMINI] Prompt: {prompt[:200]}{'...' if len(prompt) > 200 else ''}"
        )
        logging.info(f"[GEMINI] Image size: {len(image_bytes)} bytes")
        model = genai.GenerativeModel(model_name)
        contents = [{"data": image_bytes, "mime_type": "image/jpeg"}, prompt]
        logging.info(f"[GEMINI] Contents: {[str(type(c)) for c in contents]}")
        response = model.generate_content(contents)
        logging.info(f"[GEMINI] Raw response type: {type(response)}")
        try:
            logging.info(f"[GEMINI] Response as dict: {response.__dict__}")
        except Exception as e:
            logging.info(f"[GEMINI] Could not log response as dict: {e}")
        try:
            logging.info(f"[GEMINI] Response dir: {dir(response)}")
        except Exception as e:
            logging.info(f"[GEMINI] Could not log response dir: {e}")
        logging.info(f"[GEMINI] Response pprint: {pprint.pformat(response)}")
        latex = getattr(response, "text", None)
        if not latex:
            raise Exception(f"No LaTeX returned from Gemini API. Response: {response}")
        logging.info(
            f"[LATEX] Returning LaTeX for session_id={session_id}, length={len(latex)}"
        )
        latex = clean_latex(latex)
        LATEX_GENERATION_COUNT.labels("success").inc()
        LATEX_GENERATION_TIME.observe(time.time() - start_time)
        return PlainTextResponse(latex, media_type="text/plain")
    except Exception as e:
        import traceback

        tb = traceback.format_exc()
        logging.error(f"[GEMINI] Error: {e}\nTraceback:\n{tb}")
        LATEX_GENERATION_COUNT.labels("failure").inc()
        LATEX_GENERATION_TIME.observe(time.time() - start_time)
        return PlainTextResponse(f"Gemini API error: {e}", status_code=500)


def clean_latex(latex: str) -> str:
    # Remove all code block markers (```latex, ```) anywhere in the string
    s = latex.strip()
    s = re.sub(r"```latex", "", s, flags=re.IGNORECASE)
    s = re.sub(r"```", "", s)
    return s.strip()


@app.post("/api/compile-pdf")
async def compile_pdf(session_id: str = Body(...), latex: str = Body(...)):
    """
    Receives session_id and LaTeX string, compiles to PDF using tectonic, saves as /tmp/{session_id}/output.pdf
    """
    start_time = time.time()
    base_dir = get_secure_temp_dir(session_id)
    tex_path = os.path.join(base_dir, "output.tex")
    pdf_path = os.path.join(base_dir, "output.pdf")
    latex = clean_latex(latex)
    logging.info(f"[PDF] Writing LaTeX to {tex_path}")

    # Check if we're in test mode
    TEST_MODE = os.getenv("TEST_MODE", "0") == "1"

    async with aiofiles.open(tex_path, "w") as f:
        await f.write(latex.lstrip())

    if TEST_MODE:
        logging.info("[TEST MODE] Skipping actual PDF compilation, creating mock PDF")
        # Create a minimal valid PDF file for testing
        with open(pdf_path, "wb") as f:
            f.write(
                b"%PDF-1.5\n%Mock PDF for testing\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 595 842]/Parent 2 0 R/Resources<<>>>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000017 00000 n\n0000000065 00000 n\n0000000123 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n193\n%%EOF"
            )
        PDF_COMPILATION_COUNT.labels("success").inc()
        PDF_COMPILATION_TIME.observe(time.time() - start_time)
        return {"success": True, "pdf_path": pdf_path}

    # Compile with tectonic (non-test mode)
    try:
        logging.info(f"[PDF] Running tectonic for {tex_path}")
        result = run_tectonic(tex_path, base_dir)
        logging.info(f"[PDF] Tectonic stdout: {result.stdout}")
        logging.info(f"[PDF] Tectonic stderr: {result.stderr}")
    except subprocess.CalledProcessError as e:
        logging.error(f"[PDF] Tectonic failed: {e.stderr}")
        PDF_COMPILATION_COUNT.labels("failure").inc()
        PDF_COMPILATION_TIME.observe(time.time() - start_time)
        return {"success": False, "error": e.stderr}

    # Clean up .tex file
    try:
        os.remove(tex_path)
        logging.info(f"[PDF] Removed temp .tex file: {tex_path}")
    except Exception as ex:
        logging.warning(f"[PDF] Could not remove .tex file: {ex}")

    # Check PDF exists
    if not os.path.exists(pdf_path):
        logging.error(f"[PDF] PDF not generated: {pdf_path}")
        PDF_COMPILATION_COUNT.labels("failure").inc()
        PDF_COMPILATION_TIME.observe(time.time() - start_time)
        return {"success": False, "error": "PDF not generated"}
    logging.info(f"[PDF] PDF generated: {pdf_path}")

    PDF_COMPILATION_COUNT.labels("success").inc()
    PDF_COMPILATION_TIME.observe(time.time() - start_time)
    return {"success": True, "pdf_path": pdf_path}


@app.get("/api/render-pdf")
async def render_pdf(session_id: str):
    """
    Streams the compiled PDF for the given session_id.
    """
    ACTIVE_SESSIONS.dec()
    pdf_path = os.path.join(get_secure_temp_dir(session_id), "output.pdf")
    logging.info(f"[RENDER] Requested PDF for session_id={session_id}, path={pdf_path}")
    if not os.path.exists(pdf_path):
        logging.error(f"[RENDER] PDF not found: {pdf_path}")
        return PlainTextResponse("PDF not found", status_code=404)
    logging.info(f"[RENDER] Streaming PDF: {pdf_path}")
    return FileResponse(
        pdf_path, media_type="application/pdf", filename="mathecheck-worksheet.pdf"
    )
