from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="API Gestión de Filas - Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite peticiones de cualquier origen (como tu puerto 5500)
    allow_credentials=True,
    allow_methods=["*"],  # Permite GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],
)

IA_URL = os.getenv("IA_SERVICE_URL", "http://127.0.0.1:8001/predict")
API_KEY = os.getenv("API_KEY", "mi_clave_secreta_123")

class TurnoRequest(BaseModel):
    urgency: int
    nurse_ratio: float
    specialists: int
    beds: int

def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="API Key inválida")
    return x_api_key

@app.post("/api/turno", dependencies=[Depends(verify_api_key)])
async def crear_turno(data: TurnoRequest):
    # 1. Validaciones de negocio (ej. urgencia válida)
    if data.urgency not in [1, 2, 3, 4]:
        raise HTTPException(status_code=400, detail="Urgency debe ser 1-4")

    # 2. Llamada al microservicio IA
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(IA_URL, json=data.dict(), timeout=5.0)
            response.raise_for_status()
            ia_data = response.json()
            
            tiempo = ia_data["predicted_wait_minutes"]
            
            # 3. Regla de negocio: Alerta si espera > 30 min
            alerta = "Alta espera" if tiempo > 30 else "Normal"
            
            return {
                "turno": f"A-{data.urgency:02d}",
                "tiempo_estimado_min": tiempo,
                "alerta": alerta,
                "modelo": ia_data.get("model_version", "desconocido")
            }
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Servicio de IA no disponible")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"status": "ok"}