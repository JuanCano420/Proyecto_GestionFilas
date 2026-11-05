import json
import os
from datetime import date, datetime, time
from pathlib import Path

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from backend.auth import (
    create_session,
    get_current_user,
    hash_password,
    require_admin,
    verify_password,
)
from backend.database import BASE_DIR, DATA_DIR, SessionLocal, engine, get_db
from backend.models import Base, Cita, ConfigOperativa, User
from backend.motivos import catalogo_motivos, urgencia_por_motivo
from backend.schemas import (
    CitaCreate,
    CitaEstadoUpdate,
    CitaOut,
    ConfigUpdate,
    LoginRequest,
    RegisterRequest,
    TurnoRequest,
    UserOut,
)

load_dotenv()

app = FastAPI(title="API Gestión de Filas y Citas")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

IA_URL = os.getenv("IA_SERVICE_URL", "http://127.0.0.1:8001/predict")
API_KEY = os.getenv("API_KEY", "mi_clave_secreta_123")
FRONTEND_DIR = BASE_DIR / "frontend"
ESTADOS_VALIDOS = {"pendiente", "confirmada", "en_espera", "atendida", "cancelada"}
HORARIOS = [time(h, m) for h in range(8, 18) for m in (0, 30)]


def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.email == "admin@clinica.local").first():
            db.add(
                User(
                    nombre="Administrador",
                    email="admin@clinica.local",
                    telefono="",
                    password_hash=hash_password("admin123"),
                    rol="admin",
                )
            )
        if not db.query(User).filter(User.email == "paciente@clinica.local").first():
            db.add(
                User(
                    nombre="Paciente Demo",
                    email="paciente@clinica.local",
                    telefono="3000000000",
                    password_hash=hash_password("paciente123"),
                    rol="paciente",
                )
            )
        if not db.query(ConfigOperativa).first():
            db.add(ConfigOperativa())
        db.commit()
    finally:
        db.close()


init_db()


def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="API Key inválida")
    return x_api_key


def get_config(db: Session) -> ConfigOperativa:
    config = db.query(ConfigOperativa).first()
    if not config:
        config = ConfigOperativa()
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


def siguiente_codigo(db: Session) -> str:
    total = db.query(Cita).count() + 1
    return f"A-{total:04d}"


def predecir_local(payload: dict) -> dict:
    from ai_service.model_utils import ensure_model, predecir_espera

    model = ensure_model()
    return predecir_espera(
        model,
        payload["urgency"],
        payload["nurse_ratio"],
        payload["specialists"],
        payload["beds"],
    )


async def predecir_ia(payload: dict) -> dict:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(IA_URL, json=payload, timeout=5.0)
            response.raise_for_status()
            data = response.json()
            if "predicted_wait_minutes" in data:
                return data
        except httpx.HTTPError:
            pass
    return predecir_local(payload)


def serializar_cita(cita: Cita) -> CitaOut:
    return CitaOut.model_validate(cita)


def cargar_json(path: Path, fallback: dict) -> dict:
    if path.exists():
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)
    return fallback


def analizar_dataset() -> dict:
    fuente = cargar_json(
        BASE_DIR / "dataset_fuente.json",
        {"fuente": "No configurada", "registros_aproximados": 0},
    )
    metricas = cargar_json(
        BASE_DIR / "ai_service" / "metrics.json",
        {
            "baseline_mae": None,
            "random_forest_mae": None,
            "model_version": "v1.0-random-forest",
            "features": ["Urgency_Num"],
            "n_samples": None,
        },
    )

    csv_candidates = [
        DATA_DIR / "hospital_wait_time.csv",
        DATA_DIR / "hospital-wait-time-data.csv",
        BASE_DIR / "hospital-wait-time-data.csv",
    ]
    csv_path = next((p for p in csv_candidates if p.exists()), None)

    historico = []
    columnas = []
    registros_reales = None
    archivo = None

    if csv_path:
        try:
            import pandas as pd

            df = pd.read_csv(csv_path)
            columnas = list(df.columns)
            registros_reales = int(len(df))
            archivo = str(csv_path.name)

            if {"CheckInTime", "ProviderStartTime", "TriageCategory"}.issubset(df.columns):
                df["CheckInTime"] = pd.to_datetime(df["CheckInTime"], dayfirst=True, errors="coerce")
                df["ProviderStartTime"] = pd.to_datetime(
                    df["ProviderStartTime"], dayfirst=True, errors="coerce"
                )
                df["espera_min"] = (
                    df["ProviderStartTime"] - df["CheckInTime"]
                ).dt.total_seconds() / 60
                df = df.dropna(subset=["espera_min", "TriageCategory"])
                grouped = (
                    df.groupby("TriageCategory")["espera_min"]
                    .agg(["count", "mean", "median"])
                    .reset_index()
                )
                historico = [
                    {
                        "categoria": str(row["TriageCategory"]),
                        "registros": int(row["count"]),
                        "espera_media_min": round(float(row["mean"]), 2),
                        "espera_mediana_min": round(float(row["median"]), 2),
                    }
                    for _, row in grouped.iterrows()
                ]
        except Exception as exc:
            historico = [{"error": str(exc)}]

    return {
        "fuente": fuente,
        "metricas_entrenamiento": metricas,
        "archivo_csv": archivo,
        "columnas": columnas,
        "registros_reales": registros_reales,
        "espera_historica_por_triage": historico,
        "nota_modelo": (
            "El modelo actual predice con la urgencia (TriageCategory mapeada). "
            "Ratio de enfermeras, especialistas y camas se guardan para trazabilidad operativa."
        ),
    }


@app.post("/api/auth/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    email = data.email.strip().lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="El correo ya está registrado")
    user = User(
        nombre=data.nombre.strip(),
        email=email,
        telefono=data.telefono.strip(),
        password_hash=hash_password(data.password),
        rol="paciente",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_session(db, user)
    return {"token": token, "user": UserOut.model_validate(user)}


@app.post("/api/auth/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email.strip().lower()).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    token = create_session(db, user)
    return {"token": token, "user": UserOut.model_validate(user)}


@app.get("/api/me")
def me(user: User = Depends(get_current_user)):
    return UserOut.model_validate(user)


@app.get("/api/config")
def leer_config(db: Session = Depends(get_db)):
    config = get_config(db)
    return {
        "nurse_ratio": config.nurse_ratio,
        "specialists": config.specialists,
        "beds": config.beds,
        "umbral_alerta_min": config.umbral_alerta_min,
    }


@app.put("/api/admin/config")
def actualizar_config(
    data: ConfigUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    config = get_config(db)
    config.nurse_ratio = data.nurse_ratio
    config.specialists = data.specialists
    config.beds = data.beds
    config.umbral_alerta_min = data.umbral_alerta_min
    config.actualizado_en = datetime.utcnow()
    db.commit()
    return leer_config(db)


@app.get("/api/motivos")
def listar_motivos():
    return catalogo_motivos()


@app.get("/api/citas/horarios")
def horarios_disponibles(fecha: date, db: Session = Depends(get_db)):
    config = get_config(db)
    ocupadas = db.query(Cita).filter(Cita.fecha == fecha, Cita.estado != "cancelada").all()
    conteo = {}
    for cita in ocupadas:
        clave = cita.hora.strftime("%H:%M")
        conteo[clave] = conteo.get(clave, 0) + 1
    cupo = max(config.specialists, 1)
    return [
        {
            "hora": h.strftime("%H:%M"),
            "disponibles": max(cupo - conteo.get(h.strftime("%H:%M"), 0), 0),
        }
        for h in HORARIOS
    ]


@app.post("/api/citas")
async def crear_cita(
    data: CitaCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.rol != "paciente":
        raise HTTPException(status_code=403, detail="Solo pacientes pueden agendar citas")
    urgency = urgencia_por_motivo(data.motivo)
    if urgency is None:
        raise HTTPException(status_code=400, detail="Selecciona un motivo de consulta válido")
    if data.fecha < date.today():
        raise HTTPException(status_code=400, detail="No se puede agendar en una fecha pasada")
    if data.hora not in HORARIOS:
        raise HTTPException(status_code=400, detail="Horario no válido")

    config = get_config(db)
    ocupadas = (
        db.query(Cita)
        .filter(
            Cita.fecha == data.fecha,
            Cita.hora == data.hora,
            Cita.estado != "cancelada",
        )
        .count()
    )
    if ocupadas >= max(config.specialists, 1):
        raise HTTPException(status_code=409, detail="No hay cupo en ese horario")

    payload = {
        "urgency": urgency,
        "nurse_ratio": config.nurse_ratio,
        "specialists": config.specialists,
        "beds": config.beds,
    }
    ia_data = await predecir_ia(payload)
    tiempo = float(ia_data["predicted_wait_minutes"])
    alerta = "Alta espera" if tiempo > config.umbral_alerta_min else "Normal"

    cita = Cita(
        codigo_turno=siguiente_codigo(db),
        paciente_id=user.id,
        nombre_paciente=user.nombre,
        fecha=data.fecha,
        hora=data.hora,
        motivo=data.motivo.strip(),
        urgency=urgency,
        nurse_ratio=config.nurse_ratio,
        specialists=config.specialists,
        beds=config.beds,
        tiempo_estimado_min=tiempo,
        alerta=alerta,
        modelo=ia_data.get("model_version", "desconocido"),
        estado="pendiente",
        origen="paciente",
    )
    db.add(cita)
    db.commit()
    db.refresh(cita)
    return serializar_cita(cita)


@app.get("/api/citas")
def mis_citas(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(Cita).order_by(Cita.fecha.desc(), Cita.hora.desc())
    if user.rol != "admin":
        query = query.filter(Cita.paciente_id == user.id)
    return [serializar_cita(c) for c in query.all()]


@app.patch("/api/citas/{cita_id}")
def actualizar_cita(
    cita_id: int,
    data: CitaEstadoUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cita = db.query(Cita).filter(Cita.id == cita_id).first()
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    if data.estado not in ESTADOS_VALIDOS:
        raise HTTPException(status_code=400, detail="Estado no válido")
    if user.rol == "paciente":
        if cita.paciente_id != user.id:
            raise HTTPException(status_code=403, detail="No puedes modificar esta cita")
        if data.estado != "cancelada":
            raise HTTPException(status_code=403, detail="El paciente solo puede cancelar")
    cita.estado = data.estado
    db.commit()
    db.refresh(cita)
    return serializar_cita(cita)


@app.get("/api/admin/resumen")
def resumen_admin(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    citas = db.query(Cita).all()
    activas = [c for c in citas if c.estado != "cancelada"]
    por_urgencia = {}
    por_estado = {}
    for cita in citas:
        por_urgencia.setdefault(cita.urgency, {"cantidad": 0, "espera_promedio": 0, "suma": 0})
        por_urgencia[cita.urgency]["cantidad"] += 1
        por_urgencia[cita.urgency]["suma"] += cita.tiempo_estimado_min
        por_estado[cita.estado] = por_estado.get(cita.estado, 0) + 1
    for item in por_urgencia.values():
        item["espera_promedio"] = round(item["suma"] / item["cantidad"], 2)
        del item["suma"]

    espera_promedio = (
        round(sum(c.tiempo_estimado_min for c in activas) / len(activas), 2) if activas else 0
    )
    return {
        "total_citas": len(citas),
        "citas_activas": len(activas),
        "alertas_alta_espera": sum(1 for c in activas if c.alerta == "Alta espera"),
        "espera_promedio_ia_min": espera_promedio,
        "por_urgencia": por_urgencia,
        "por_estado": por_estado,
        "pacientes_registrados": db.query(User).filter(User.rol == "paciente").count(),
    }


@app.get("/api/admin/dataset")
def dataset_admin(_: User = Depends(require_admin)):
    return analizar_dataset()


@app.get("/api/admin/comparacion")
def comparacion_ia_dataset(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    dataset = analizar_dataset()
    citas = db.query(Cita).filter(Cita.estado != "cancelada").all()
    por_urgencia = {}
    for cita in citas:
        bucket = por_urgencia.setdefault(str(cita.urgency), [])
        bucket.append(cita.tiempo_estimado_min)
    predicciones = [
        {
            "urgencia": urg,
            "citas": len(valores),
            "espera_promedio_ia_min": round(sum(valores) / len(valores), 2),
        }
        for urg, valores in sorted(por_urgencia.items())
    ]
    return {
        "predicciones_sistema": predicciones,
        "historico_dataset": dataset["espera_historica_por_triage"],
        "metricas_entrenamiento": dataset["metricas_entrenamiento"],
        "interpretacion": (
            "Compara la espera que estima la IA en las citas agendadas "
            "contra la espera media histórica del CSV de entrenamiento."
        ),
    }


@app.post("/api/turno", dependencies=[Depends(verify_api_key)])
async def crear_turno(data: TurnoRequest, db: Session = Depends(get_db)):
    if data.urgency not in [1, 2, 3, 4]:
        raise HTTPException(status_code=400, detail="Urgency debe ser 1-4")

    try:
        ia_data = await predecir_ia(data.model_dump())
        tiempo = float(ia_data["predicted_wait_minutes"])
        config = get_config(db)
        alerta = "Alta espera" if tiempo > config.umbral_alerta_min else "Normal"
        ahora = datetime.now()
        cita = Cita(
            codigo_turno=siguiente_codigo(db),
            paciente_id=None,
            nombre_paciente="Turno mostrador",
            fecha=ahora.date(),
            hora=ahora.time().replace(second=0, microsecond=0),
            motivo="Registro operativo",
            urgency=data.urgency,
            nurse_ratio=data.nurse_ratio,
            specialists=data.specialists,
            beds=data.beds,
            tiempo_estimado_min=tiempo,
            alerta=alerta,
            modelo=ia_data.get("model_version", "desconocido"),
            estado="en_espera",
            origen="operador",
        )
        db.add(cita)
        db.commit()
        db.refresh(cita)
        return {
            "turno": cita.codigo_turno,
            "tiempo_estimado_min": tiempo,
            "alerta": alerta,
            "modelo": cita.modelo,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok"}


if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
