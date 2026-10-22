from fastapi.testclient import TestClient
from backend.main import app
import os

client = TestClient(app)

API_KEY = os.getenv("API_KEY", "mi_clave_secreta_123")
HEADERS = {"x-api-key": API_KEY}

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_crear_turno_sin_api_key():
    response = client.post("/api/turno", json={
        "urgency": 2, "nurse_ratio": 3.5, "specialists": 5, "beds": 100
    })
    assert response.status_code == 403  # Sin API key

def test_crear_turno_urgencia_invalida():
    response = client.post("/api/turno", headers=HEADERS, json={
        "urgency": 5, "nurse_ratio": 3.5, "specialists": 5, "beds": 100
    })
    assert response.status_code == 400

# Nota: El test de éxito requiere que el servicio IA esté corriendo.
# Para pruebas unitarias aisladas, se recomienda mockear httpx.