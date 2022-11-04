from fastapi.testclient import TestClient
from .main import app

client = TestClient(app)


def test_signup():
    response = client.post("/signup", json={
        "email": "test@example.com",
        "username": "user",
        "password": "secret"
    })
    assert response.status_code == 200
    assert response.json() == {"msg": "Hello World"}
