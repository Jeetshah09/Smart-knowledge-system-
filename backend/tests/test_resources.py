"""Tests for resource upload, extraction and ownership."""
from io import BytesIO

from docx import Document as DocxDocument


def _txt(name="note.txt", content=b"hello world content"):
    return {"file": (name, BytesIO(content), "text/plain")}


def test_upload_txt(client, auth_headers, notebook_id):
    response = client.post(
        f"/api/resources/upload?notebook_id={notebook_id}",
        files=_txt(content=b"photosynthesis is a process used by plants"),
        headers=auth_headers,
    )
    assert response.status_code == 200
    resource = response.json()["data"]["resource"]
    assert resource["processing_status"] == "completed"
    assert resource["has_content"] is True
    assert "photosynthesis" in resource["content_preview"]


def test_upload_rejects_unsupported_type(client, auth_headers, notebook_id):
    response = client.post(
        f"/api/resources/upload?notebook_id={notebook_id}",
        files={"file": ("evil.exe", BytesIO(b"MZ..."), "application/x-msdownload")},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_upload_requires_ownership_of_notebook(client, notebook_id, bob_headers):
    response = client.post(
        f"/api/resources/upload?notebook_id={notebook_id}",
        files=_txt(),
        headers=bob_headers,
    )
    assert response.status_code == 404  # bob cannot upload into alice's notebook


def test_list_notebook_resources(client, auth_headers, notebook_id):
    response = client.get(f"/api/notebooks/{notebook_id}/resources", headers=auth_headers)
    assert response.status_code == 200
    resources = response.json()["data"]["resources"]
    assert len(resources) >= 1
    assert all("content" not in r for r in resources)  # heavy field stripped from lists


def test_get_resource_with_content(client, auth_headers, notebook_id):
    listed = client.get(f"/api/notebooks/{notebook_id}/resources", headers=auth_headers).json()["data"]["resources"]
    resource_id = listed[0]["id"]
    response = client.get(f"/api/resources/{resource_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["data"]["resource"]["content"]


def test_other_user_cannot_read_resource(client, notebook_id, auth_headers, bob_headers):
    listed = client.get(
        f"/api/notebooks/{notebook_id}/resources", headers=auth_headers
    ).json()["data"]["resources"]
    resource_id = listed[0]["id"]
    response = client.get(f"/api/resources/{resource_id}", headers=bob_headers)
    assert response.status_code == 404


def test_docx_extraction(client, auth_headers, notebook_id):
    buffer = BytesIO()
    doc = DocxDocument()
    doc.add_paragraph("Photosynthesis happens in the chloroplast.")
    doc.save(buffer)
    buffer.seek(0)
    response = client.post(
        f"/api/resources/upload?notebook_id={notebook_id}",
        files={"file": ("test.docx", buffer, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        headers=auth_headers,
    )
    assert response.status_code == 200
    resource = response.json()["data"]["resource"]
    assert resource["type"] == "docx"
    assert "chloroplast" in resource["content_preview"]


def test_youtube_invalid_url_rejected(client, auth_headers, notebook_id):
    response = client.post(
        "/api/resources/youtube",
        json={"notebook_id": notebook_id, "url": "https://not-youtube.com/watch?v=abc"},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_delete_resource(client, auth_headers, notebook_id):
    upload = client.post(
        f"/api/resources/upload?notebook_id={notebook_id}",
        files=_txt(name="todelete.txt"),
        headers=auth_headers,
    ).json()["data"]["resource"]
    assert client.delete(f"/api/resources/{upload['id']}", headers=auth_headers).status_code == 200
