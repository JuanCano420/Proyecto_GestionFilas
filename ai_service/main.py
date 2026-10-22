from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import numpy as np
import os

app = FastAPI(title="Servicio IA - Predicción de Espera")

# Cargar modelo al iniciar
model_path = os.path.join(os.path.dirname(__file__), 'model.pkl')
if os.path.exists(model_path):
    model = joblib.load(model_path)
else:
    model = None
    print("Advertencia: Modelo no encontrado. Ejecuta train.py primero.")

# Mantenemos las 4 variables por si el frontend las envía, 
# para que no genere error de "datos no esperados"
class QueueInput(BaseModel):
    urgency: int  # 1-4
    nurse_ratio: float
    specialists: int
    beds: int

@app.post("/predict")
def predict_wait(data: QueueInput):
    if model is None:
        return {"error": "Modelo no cargado"}
    
    # SOLUCIÓN: Solo le pasamos el dato de urgencia al modelo (1 sola feature)
    features = np.array([[data.urgency]])
    prediction = model.predict(features)[0]
    
    return {
        "predicted_wait_minutes": round(float(prediction), 2),
        "model_version": "v1.0-random-forest"
    }

@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": model is not None}