import os
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

SAMPLE_IMAGE_PATH = os.path.join(os.path.dirname(__file__), "sample.jpg")


def test_upload():
    # Print the resolved path for debugging
    print("SAMPLE_IMAGE_PATH:", SAMPLE_IMAGE_PATH)
    # Use a small blank image as a placeholder
    with open(SAMPLE_IMAGE_PATH, "rb") as f:
        response = client.post(
            "/api/upload", files={"file": ("sample.jpg", f, "image/jpeg")}
        )
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    return data["session_id"]


def test_generate_latex():
    session_id = test_upload()
    response = client.post("/api/generate-latex", json={"session_id": session_id})
    assert response.status_code == 200
    assert "\\documentclass" in response.text or "\documentclass" in response.text
    return session_id, response.text


def test_compile_pdf():
    session_id, latex = test_generate_latex()
    response = client.post(
        "/api/compile-pdf", json={"session_id": session_id, "latex": latex}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert os.path.exists(data["pdf_path"])
    return session_id


def test_render_pdf():
    session_id = test_compile_pdf()
    response = client.get(f"/api/render-pdf?session_id={session_id}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert len(response.content) > 100  # PDF should not be empty
