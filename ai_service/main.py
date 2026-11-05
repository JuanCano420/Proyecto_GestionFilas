from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ai_service.model_utils import ensure_model, predecir_espera

app = FastAPI(title="Servicio IA - Predicción de Espera")
model = ensure_model()


class QueueInput(BaseModel):
    urgency: int
    nurse_ratio: float
    specialists: int
    beds: int


@app.post("/predict")
def predict_wait(data: QueueInput):
    if model is None:
        raise HTTPException(status_code=503, detail="Modelo no cargado")
    return predecir_espera(
        model,
        data.urgency,
        data.nurse_ratio,
        data.specialists,
        data.beds,
    )


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": model is not None}
