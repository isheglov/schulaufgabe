import os
import uuid
from fastapi import FastAPI, File, UploadFile, Body
from fastapi.responses import JSONResponse, PlainTextResponse
import aiofiles
import subprocess

app = FastAPI()

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    session_id = str(uuid.uuid4())
    upload_dir = f"/tmp/{session_id}"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, "input.jpg")
    async with aiofiles.open(file_path, "wb") as out_file:
        content = await file.read()
        await out_file.write(content)
    return JSONResponse({"session_id": session_id})

@app.post("/api/generate-latex", response_class=PlainTextResponse)
async def generate_latex(session_id: str = Body(..., embed=True)):
    """
    Receives a session_id, loads the image, sends it to Gemini, and returns LaTeX.
    For now, Gemini integration is mocked.
    """
    image_path = f"/tmp/{session_id}/input.jpg"
    if not os.path.exists(image_path):
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
    return PlainTextResponse(latex, media_type="text/plain")

@app.post("/api/compile-pdf")
async def compile_pdf(session_id: str = Body(...), latex: str = Body(...)):
    """
    Receives session_id and LaTeX string, compiles to PDF using tectonic, saves as /tmp/{session_id}/output.pdf
    """
    import shutil
    base_dir = f"/tmp/{session_id}"
    os.makedirs(base_dir, exist_ok=True)
    tex_path = os.path.join(base_dir, "output.tex")
    pdf_path = os.path.join(base_dir, "output.pdf")

    # Write LaTeX to file
    async with aiofiles.open(tex_path, "w") as f:
        await f.write(latex)

    # Compile with tectonic
    try:
        result = subprocess.run([
            "tectonic",
            tex_path,
            "--outdir", base_dir,
            "--print",
            "--synctex=none",
            "--keep-logs=no",
            "--keep-intermediates=no"
        ], capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": e.stderr}

    # Clean up .tex file
    try:
        os.remove(tex_path)
    except Exception:
        pass

    # Check PDF exists
    if not os.path.exists(pdf_path):
        return {"success": False, "error": "PDF not generated"}

    return {"success": True, "pdf_path": pdf_path} 
