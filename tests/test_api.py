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


def test_login_admin_demo():
    response = client.post("/api/auth/login", json={
        "email": "admin@clinica.local",
        "password": "admin123",
    })
    assert response.status_code == 200
    assert response.json()["user"]["rol"] == "admin"


def test_register_y_listar_citas():
    response = client.post("/api/auth/register", json={
        "nombre": "Prueba",
        "email": "prueba_citas_" + os.urandom(4).hex() + "@clinica.local",
        "telefono": "3001112233",
        "password": "clave123",
    })
    assert response.status_code == 200
    token = response.json()["token"]
    citas = client.get("/api/citas", headers={"Authorization": f"Bearer {token}"})
    assert citas.status_code == 200
    assert citas.json() == []

# Nota: El test de éxito requiere que el servicio IA esté corriendo.
# Para pruebas unitarias aisladas, se recomienda mockear httpx.