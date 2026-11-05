# Sistema Inteligente de Gestión de Filas y Tiempos de Espera

Proyecto de Ingeniería de Software con IA integrada (Colección III).

## Arquitectura
- **Frontend:** HTML/JS
- **Backend:** FastAPI (Puerto 8000)
- **Microservicio IA:** FastAPI + Scikit-learn (Puerto 8001)
- **Dataset:** Hospital Wait Time Data (Kaggle)

## Requisitos
- Python 3.12.XX
- Docker (opcional)

## Instalación local
1. `pip install -r requirements.txt`
2. `python ai_service/train.py`
3. `uvicorn ai_service.main:app --port 8001`
4. `uvicorn backend.main:app --port 8000`
5. Abrir `http://127.0.0.1:8000/` en el navegador.

## Portales
- **Pacientes:** registro, agendamiento de citas y consulta del tiempo de espera estimado por IA.
- **Administradores:** verificación de citas, capacidad operativa, métricas del modelo y dataset de entrenamiento.
- Cuentas demo: `paciente@clinica.local / paciente123` y `admin@clinica.local / admin123`.
- Base de datos SQLite en `data/app.db`.

## Pruebas
`pytest tests/`

## Métricas IA
- Baseline: Predecir la media histórica.
- Modelo final: Random Forest (ver `Laboratorio_IA.ipynb`).