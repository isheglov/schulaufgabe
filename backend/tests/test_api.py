import os
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

SAMPLE_IMAGE_PATH = os.path.join(os.path.dirname(__file__), "sample.jpg")


def _upload_and_get_session_id():
    with open(SAMPLE_IMAGE_PATH, "rb") as f:
        response = client.post(
            "/api/upload", files={"file": ("sample.jpg", f, "image/jpeg")}
        )
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    return data["session_id"]


def _generate_latex_and_get(session_id):
    response = client.post("/api/generate-latex", json={"session_id": session_id})
    assert response.status_code == 200
    assert r"\documentclass" in response.text or r"\documentclass" in response.text
    return response.text


def _compile_pdf_and_get_path(session_id, latex):
    response = client.post(
        "/api/compile-pdf", json={"session_id": session_id, "latex": latex}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert os.path.exists(data["pdf_path"])
    return data["pdf_path"]


def test_upload():
    _upload_and_get_session_id()


def mock_generate_content(contents):
    mock_response = MagicMock()
    mock_response.text = (
        "\\documentclass{article}\n\\begin{document}\nMocked LaTeX\n\\end{document}"
    )
    return mock_response


def mock_subprocess_run(*args, **kwargs):
    # Find the output directory and PDF path from the args
    if isinstance(args[0], list):
        try:
            outdir_index = args[0].index("--outdir")
            base_dir = args[0][outdir_index + 1]
            pdf_path = os.path.join(base_dir, "output.pdf")
            # Create a dummy PDF file with >100 bytes
            dummy_pdf = b"%PDF-1.4\n%Dummy PDF\n" + b"0" * 120
            with open(pdf_path, "wb") as f:
                f.write(dummy_pdf)
        except Exception:
            pass
    mock_result = MagicMock()
    mock_result.stdout = "Tectonic mock output"
    mock_result.stderr = ""
    mock_result.returncode = 0
    return mock_result


def test_generate_latex():
    session_id = _upload_and_get_session_id()
    with patch(
        "google.generativeai.GenerativeModel.generate_content",
        side_effect=mock_generate_content,
    ):
        _generate_latex_and_get(session_id)


def test_compile_pdf():
    session_id = _upload_and_get_session_id()
    with patch(
        "google.generativeai.GenerativeModel.generate_content",
        side_effect=mock_generate_content,
    ):
        latex = _generate_latex_and_get(session_id)
    with patch("subprocess.run", side_effect=mock_subprocess_run):
        _compile_pdf_and_get_path(session_id, latex)


def test_render_pdf():
    session_id = _upload_and_get_session_id()
    with patch(
        "google.generativeai.GenerativeModel.generate_content",
        side_effect=mock_generate_content,
    ):
        latex = _generate_latex_and_get(session_id)
    with patch("subprocess.run", side_effect=mock_subprocess_run):
        _compile_pdf_and_get_path(session_id, latex)
    response = client.get(f"/api/render-pdf?session_id={session_id}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert len(response.content) > 100  # PDF should not be empty
