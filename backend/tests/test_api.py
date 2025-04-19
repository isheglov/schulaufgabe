import os
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


def test_generate_latex():
    session_id = _upload_and_get_session_id()
    _generate_latex_and_get(session_id)


def test_compile_pdf():
    session_id = _upload_and_get_session_id()
    latex = _generate_latex_and_get(session_id)
    _compile_pdf_and_get_path(session_id, latex)


def test_render_pdf():
    session_id = _upload_and_get_session_id()
    latex = _generate_latex_and_get(session_id)
    pdf_path = _compile_pdf_and_get_path(session_id, latex)
    response = client.get(f"/api/render-pdf?session_id={session_id}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert len(response.content) > 100  # PDF should not be empty
