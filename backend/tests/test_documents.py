"""
Automated tests for the Ajaia Docs API.

Run with:
    cd backend
    pytest tests/ -v
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from database import get_db
from models import Base
from seed import seed_users

# ── Test database setup ───────────────────────────────────────────────────────

TEST_DB_URL = "sqlite:///./test_ajaia.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    db = TestSessionLocal()
    seed_users(db)
    db.close()
    yield
    Base.metadata.drop_all(bind=test_engine)


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

# ── Helpers ───────────────────────────────────────────────────────────────────

def login(email="alice@ajaia.com", password="password123"):
    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


# ── Tests: Authentication ─────────────────────────────────────────────────────

def test_login_success():
    r = client.post("/auth/login", json={"email": "alice@ajaia.com", "password": "password123"})
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["user"]["email"] == "alice@ajaia.com"


def test_login_wrong_password():
    r = client.post("/auth/login", json={"email": "alice@ajaia.com", "password": "wrong"})
    assert r.status_code == 401


def test_login_unknown_user():
    r = client.post("/auth/login", json={"email": "ghost@ajaia.com", "password": "x"})
    assert r.status_code == 401


# ── Tests: Documents ──────────────────────────────────────────────────────────

def test_create_document():
    token = login()
    r = client.post("/documents", json={"title": "My Doc"}, headers=auth_headers(token))
    assert r.status_code == 201
    assert r.json()["title"] == "My Doc"
    assert r.json()["role"] == "owner"


def test_list_documents():
    token = login()
    client.post("/documents", json={"title": "Doc A"}, headers=auth_headers(token))
    client.post("/documents", json={"title": "Doc B"}, headers=auth_headers(token))
    r = client.get("/documents", headers=auth_headers(token))
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_update_document_content():
    token = login()
    doc_id = client.post("/documents", json={"title": "Edit Me"}, headers=auth_headers(token)).json()["id"]
    r = client.put(f"/documents/{doc_id}", json={"content": "<p>Hello</p>"}, headers=auth_headers(token))
    assert r.status_code == 200
    assert r.json()["content"] == "<p>Hello</p>"


def test_delete_document():
    token = login()
    doc_id = client.post("/documents", json={"title": "Delete Me"}, headers=auth_headers(token)).json()["id"]
    r = client.delete(f"/documents/{doc_id}", headers=auth_headers(token))
    assert r.status_code == 204
    r2 = client.get(f"/documents/{doc_id}", headers=auth_headers(token))
    assert r2.status_code == 404


def test_delete_document_non_owner_blocked():
    alice_token = login("alice@ajaia.com")
    bob_token = login("bob@ajaia.com")
    doc_id = client.post("/documents", json={"title": "Alice's"}, headers=auth_headers(alice_token)).json()["id"]
    r = client.delete(f"/documents/{doc_id}", headers=auth_headers(bob_token))
    assert r.status_code == 403


# ── Tests: Sharing ────────────────────────────────────────────────────────────

def test_share_document_with_viewer():
    alice_token = login("alice@ajaia.com")
    bob_token = login("bob@ajaia.com")

    # Get Bob's user id
    bob_id = client.post("/auth/login", json={"email": "bob@ajaia.com", "password": "password123"}).json()["user"]["id"]

    doc_id = client.post("/documents", json={"title": "Shared"}, headers=auth_headers(alice_token)).json()["id"]

    r = client.post(f"/documents/{doc_id}/share", json={"user_id": bob_id, "permission": "viewer"}, headers=auth_headers(alice_token))
    assert r.status_code == 201

    # Bob should see it in his list
    r2 = client.get("/documents", headers=auth_headers(bob_token))
    ids = [d["id"] for d in r2.json()]
    assert doc_id in ids


def test_viewer_cannot_edit():
    alice_token = login("alice@ajaia.com")
    bob_id = client.post("/auth/login", json={"email": "bob@ajaia.com", "password": "password123"}).json()["user"]["id"]
    bob_token = login("bob@ajaia.com")

    doc_id = client.post("/documents", json={"title": "Protected"}, headers=auth_headers(alice_token)).json()["id"]
    client.post(f"/documents/{doc_id}/share", json={"user_id": bob_id, "permission": "viewer"}, headers=auth_headers(alice_token))

    r = client.put(f"/documents/{doc_id}", json={"content": "<p>Hack</p>"}, headers=auth_headers(bob_token))
    assert r.status_code == 403


def test_editor_can_edit():
    alice_token = login("alice@ajaia.com")
    carol_id = client.post("/auth/login", json={"email": "carol@ajaia.com", "password": "password123"}).json()["user"]["id"]
    carol_token = login("carol@ajaia.com")

    doc_id = client.post("/documents", json={"title": "Collab"}, headers=auth_headers(alice_token)).json()["id"]
    client.post(f"/documents/{doc_id}/share", json={"user_id": carol_id, "permission": "editor"}, headers=auth_headers(alice_token))

    r = client.put(f"/documents/{doc_id}", json={"content": "<p>Carol's edit</p>"}, headers=auth_headers(carol_token))
    assert r.status_code == 200


# ── Tests: File Upload ────────────────────────────────────────────────────────

def test_upload_txt_file():
    token = login()
    doc_id = client.post("/documents", json={"title": "From File"}, headers=auth_headers(token)).json()["id"]
    r = client.post(
        f"/documents/{doc_id}/upload",
        files={"file": ("hello.txt", b"Hello World\nSecond line", "text/plain")},
        headers=auth_headers(token),
    )
    assert r.status_code == 200
    assert "<p>" in r.json()["content"]


def test_upload_unsupported_type():
    token = login()
    doc_id = client.post("/documents", json={"title": "Bad Upload"}, headers=auth_headers(token)).json()["id"]
    r = client.post(
        f"/documents/{doc_id}/upload",
        files={"file": ("bad.exe", b"binary", "application/octet-stream")},
        headers=auth_headers(token),
    )
    assert r.status_code == 400
