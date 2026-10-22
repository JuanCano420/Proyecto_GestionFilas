# Sistema Inteligente de Gestión de Filas y Tiempos de Espera

Proyecto de Ingeniería de Software con IA integrada (Colección III).

## Arquitectura
- **Frontend:** HTML/JS (demo)
- **Backend:** FastAPI (Puerto 8000)
- **Microservicio IA:** FastAPI + Scikit-learn (Puerto 8001)
- **Dataset:** Hospital Wait Time Data (Kaggle)

## Requisitos
- Python 3.10+
- Docker (opcional)

## Instalación local
1. `pip install -r requirements.txt`
2. `python ai_service/train.py`
3. `uvicorn ai_service.main:app --port 8001`
4. `uvicorn backend.main:app --port 8000`
5. Abrir `frontend/index.html` en el navegador.

## Pruebas
`pytest tests/`

## Métricas IA
- Baseline: Predecir la media histórica.
- Modelo final: Random Forest (ver `Laboratorio_IA.ipynb`).