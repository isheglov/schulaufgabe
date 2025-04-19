import os
import uuid
from fastapi import FastAPI, File, UploadFile, Body
from fastapi.responses import JSONResponse, PlainTextResponse, FileResponse
import aiofiles
import subprocess
from fastapi.middleware.cors import CORSMiddleware
import logging
import google.generativeai as genai
from dotenv import load_dotenv
import pprint
import re

logging.basicConfig(level=logging.INFO)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    session_id = str(uuid.uuid4())
    upload_dir = f"/tmp/{session_id}"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, "input.jpg")
    logging.info(f"[UPLOAD] Saving uploaded file to {file_path}")
    async with aiofiles.open(file_path, "wb") as out_file:
        content = await file.read()
        await out_file.write(content)
    logging.info(f"[UPLOAD] File saved. Returning session_id: {session_id}")
    return JSONResponse({"session_id": session_id})


@app.post("/api/generate-latex", response_class=PlainTextResponse)
async def generate_latex(session_id: str = Body(..., embed=True)):
    """
    Receives a session_id, loads the image, sends it to Gemini, and returns LaTeX.
    """
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logging.error("[GEMINI] GOOGLE_API_KEY not set in environment.")
        return PlainTextResponse("Gemini API key not set", status_code=500)
    genai.configure(api_key=api_key)
    image_path = f"/tmp/{session_id}/input.jpg"
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
        logging.info(f"[GEMINI] Prompt: {prompt[:200]}{'...' if len(prompt) > 200 else ''}")
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
        latex = getattr(response, 'text', None)
        if not latex:
            raise Exception(f"No LaTeX returned from Gemini API. Response: {response}")
        logging.info(f"[LATEX] Returning LaTeX for session_id={session_id}, length={len(latex)}")
        latex = clean_latex(latex)
        return PlainTextResponse(latex, media_type="text/plain")
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logging.error(f"[GEMINI] Error: {e}\nTraceback:\n{tb}")
        return PlainTextResponse(f"Gemini API error: {e}", status_code=500)


def clean_latex(latex: str) -> str:
    # Remove all code block markers (```latex, ```) anywhere in the string
    s = latex.strip()
    s = re.sub(r'```latex', '', s, flags=re.IGNORECASE)
    s = re.sub(r'```', '', s)
    return s.strip()


@app.post("/api/compile-pdf")
async def compile_pdf(session_id: str = Body(...), latex: str = Body(...)):
    """
    Receives session_id and LaTeX string, compiles to PDF using tectonic, saves as /tmp/{session_id}/output.pdf
    """
    base_dir = f"/tmp/{session_id}"
    os.makedirs(base_dir, exist_ok=True)
    tex_path = os.path.join(base_dir, "output.tex")
    pdf_path = os.path.join(base_dir, "output.pdf")
    latex = clean_latex(latex)
    logging.info(f"[PDF] Writing LaTeX to {tex_path}")
    async with aiofiles.open(tex_path, "w") as f:
        await f.write(latex.lstrip())

    # Compile with tectonic
    try:
        logging.info(f"[PDF] Running tectonic for {tex_path}")
        result = subprocess.run(
            [
                "tectonic",
                tex_path,
                "--outdir",
                base_dir,
                "--print",
                "--synctex=none",
                "--keep-logs=no",
                "--keep-intermediates=no",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        logging.info(f"[PDF] Tectonic stdout: {result.stdout}")
        logging.info(f"[PDF] Tectonic stderr: {result.stderr}")
    except subprocess.CalledProcessError as e:
        logging.error(f"[PDF] Tectonic failed: {e.stderr}")
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
        return {"success": False, "error": "PDF not generated"}
    logging.info(f"[PDF] PDF generated: {pdf_path}")

    return {"success": True, "pdf_path": pdf_path}


@app.get("/api/render-pdf")
async def render_pdf(session_id: str):
    """
    Streams the compiled PDF for the given session_id.
    """
    pdf_path = f"/tmp/{session_id}/output.pdf"
    logging.info(f"[RENDER] Requested PDF for session_id={session_id}, path={pdf_path}")
    if not os.path.exists(pdf_path):
        logging.error(f"[RENDER] PDF not found: {pdf_path}")
        return PlainTextResponse("PDF not found", status_code=404)
    logging.info(f"[RENDER] Streaming PDF: {pdf_path}")
    return FileResponse(
        pdf_path, media_type="application/pdf", filename="mathecheck-worksheet.pdf"
    )
