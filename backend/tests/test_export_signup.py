import pytest
from tests.test_documents import client, auth_headers, test_engine, TestSessionLocal, Base, seed_users

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    db = TestSessionLocal()
    seed_users(db)
    db.close()
    yield
    Base.metadata.drop_all(bind=test_engine)

# ── Sign-up Tests ─────────────────────────────────────────────────────────────

def test_signup_success():
    payload = {
        "name": "Dave",
        "email": "dave@ajaia.com",
        "password": "password123"
    }
    r = client.post("/auth/signup", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert "access_token" in data
    assert data["user"]["name"] == "Dave"
    assert data["user"]["email"] == "dave@ajaia.com"

    # Verify we can login with these credentials now
    r_login = client.post("/auth/login", json={"email": "dave@ajaia.com", "password": "password123"})
    assert r_login.status_code == 200


def test_signup_email_exists():
    payload = {
        "name": "Duplicate Alice",
        "email": "alice@ajaia.com",
        "password": "newpassword"
    }
    r = client.post("/auth/signup", json=payload)
    assert r.status_code == 400
    assert "already registered" in r.json()["detail"].lower()


# ── Export Tests ──────────────────────────────────────────────────────────────

def test_export_document_formats():
    # 1. Login Alice
    r_login = client.post("/auth/login", json={"email": "alice@ajaia.com", "password": "password123"})
    token = r_login.json()["access_token"]
    headers = auth_headers(token)

    # 2. Create document with formatting
    doc_payload = {
        "title": "Test Formatting Doc",
        "content": "<h1>Title Here</h1><p>This is a <strong>bold</strong> paragraph.</p><blockquote>Quote text</blockquote><pre><code>code_here()</code></pre>"
    }
    doc_response = client.post("/documents", json=doc_payload, headers=headers)
    assert doc_response.status_code == 201
    doc_id = doc_response.json()["id"]

    # 3. Export as txt
    r_txt = client.get(f"/documents/{doc_id}/export?format=txt", headers=headers)
    assert r_txt.status_code == 200
    assert "attachment" in r_txt.headers["content-disposition"]
    assert "Test Formatting Doc.txt" in r_txt.headers["content-disposition"]
    assert "Title Here" in r_txt.text
    assert "bold" in r_txt.text
    assert "<strong>" not in r_txt.text

    # 4. Export as md
    r_md = client.get(f"/documents/{doc_id}/export?format=md", headers=headers)
    assert r_md.status_code == 200
    assert "Test Formatting Doc.md" in r_md.headers["content-disposition"]
    assert "# Title Here" in r_md.text
    assert "**bold**" in r_md.text
    assert "> Quote text" in r_md.text
    assert "```\ncode_here()\n```" in r_md.text

    # 5. Export as html
    r_html = client.get(f"/documents/{doc_id}/export?format=html", headers=headers)
    assert r_html.status_code == 200
    assert "Test Formatting Doc.html" in r_html.headers["content-disposition"]
    assert "<!DOCTYPE html>" in r_html.text
    assert "<h1>Title Here</h1>" in r_html.text

    # 6. Export as pdf
    r_pdf = client.get(f"/documents/{doc_id}/export?format=pdf", headers=headers)
    assert r_pdf.status_code == 200
    assert "Test Formatting Doc.pdf" in r_pdf.headers["content-disposition"]
    assert r_pdf.headers["content-type"] == "application/pdf"

    # 7. Export invalid format
    r_invalid = client.get(f"/documents/{doc_id}/export?format=invalid", headers=headers)
    assert r_invalid.status_code == 400


def test_export_permissions():
    # Login Alice (owner)
    token_alice = client.post("/auth/login", json={"email": "alice@ajaia.com", "password": "password123"}).json()["access_token"]
    # Login Bob (no access yet)
    token_bob = client.post("/auth/login", json={"email": "bob@ajaia.com", "password": "password123"}).json()["access_token"]

    # Alice creates doc with content
    r_create = client.post("/documents", json={"title": "Alice Secret", "content": "Alice Secret content"}, headers=auth_headers(token_alice))
    doc_id = r_create.json()["id"]

    # Bob tries to export (should fail)
    r_bob_fail = client.get(f"/documents/{doc_id}/export?format=txt", headers=auth_headers(token_bob))
    assert r_bob_fail.status_code == 403

    # Share with Bob as viewer
    r_share = client.post(f"/documents/{doc_id}/share", json={"user_id": 2, "permission": "viewer"}, headers=auth_headers(token_alice))
    assert r_share.status_code == 201

    # Bob tries to export now (should succeed)
    r_bob_success = client.get(f"/documents/{doc_id}/export?format=txt", headers=auth_headers(token_bob))
    assert r_bob_success.status_code == 200
    assert "Alice Secret content" in r_bob_success.text
