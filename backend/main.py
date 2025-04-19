import os
import uuid
from fastapi import FastAPI, File, UploadFile, Body
from fastapi.responses import JSONResponse, PlainTextResponse, FileResponse
import aiofiles
import subprocess
from fastapi.middleware.cors import CORSMiddleware
import logging

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
    For now, Gemini integration is mocked.
    """
    image_path = f"/tmp/{session_id}/input.jpg"
    logging.info(
        f"[LATEX] Generating LaTeX for session_id={session_id}, image_path={image_path}"
    )
    if not os.path.exists(image_path):
        logging.error(f"[LATEX] Image not found: {image_path}")
        return PlainTextResponse("Image not found", status_code=404)

    # TODO: Integrate with Gemini API here
    # For now, return a mock LaTeX document
    latex = r"""
\\documentclass[a4paper,12pt]{article}
\\usepackage[utf8]{inputenc}
\\begin{document}

\\section*{Mathe Arbeitsblatt}

\\begin{enumerate}
  \item Löse die Gleichung: $3x + 5 = 20$
  \item Berechne den Umfang eines Kreises mit Radius $r = 4$ cm.
  \item Addiere: $\frac{2}{3} + \frac{1}{6}$
\end{enumerate}

\\end{document}
"""
    logging.info(
        f"[LATEX] Returning LaTeX for session_id={session_id}, length={len(latex)}"
    )
    return PlainTextResponse(latex, media_type="text/plain")


@app.post("/api/compile-pdf")
async def compile_pdf(session_id: str = Body(...), latex: str = Body(...)):
    """
    Receives session_id and LaTeX string, compiles to PDF using tectonic, saves as /tmp/{session_id}/output.pdf
    """
    base_dir = f"/tmp/{session_id}"
    os.makedirs(base_dir, exist_ok=True)
    tex_path = os.path.join(base_dir, "output.tex")
    pdf_path = os.path.join(base_dir, "output.pdf")
    logging.info(f"[PDF] Writing LaTeX to {tex_path}")
    async with aiofiles.open(tex_path, "w") as f:
        await f.write(latex)

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
