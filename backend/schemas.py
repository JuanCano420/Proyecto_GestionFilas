from datetime import date, datetime, time
from typing import Optional

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    nombre: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=180)
    telefono: str = ""
    password: str = Field(min_length=6, max_length=80)


class LoginRequest(BaseModel):
    email: str
    password: str


class TurnoRequest(BaseModel):
    urgency: int
    nurse_ratio: float
    specialists: int
    beds: int


class CitaCreate(BaseModel):
    fecha: date
    hora: time
    motivo: str = Field(min_length=3, max_length=255)


class CitaEstadoUpdate(BaseModel):
    estado: str


class ConfigUpdate(BaseModel):
    nurse_ratio: float
    specialists: int
    beds: int
    umbral_alerta_min: int = 30


class UserOut(BaseModel):
    id: int
    nombre: str
    email: str
    telefono: str
    rol: str

    class Config:
        from_attributes = True


class CitaOut(BaseModel):
    id: int
    codigo_turno: str
    paciente_id: Optional[int]
    nombre_paciente: str
    fecha: date
    hora: time
    motivo: str
    urgency: int
    nurse_ratio: float
    specialists: int
    beds: int
    tiempo_estimado_min: float
    alerta: str
    modelo: str
    estado: str
    origen: str
    creado_en: datetime

    class Config:
        from_attributes = True
