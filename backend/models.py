from datetime import datetime

from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String, Time
from sqlalchemy.orm import relationship

from backend.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(120), nullable=False)
    email = Column(String(180), unique=True, index=True, nullable=False)
    telefono = Column(String(40), default="")
    password_hash = Column(String(255), nullable=False)
    rol = Column(String(20), nullable=False, default="paciente")
    creado_en = Column(DateTime, default=datetime.utcnow)

    citas = relationship("Cita", back_populates="paciente")
    sesiones = relationship("SessionToken", back_populates="user")


class SessionToken(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True)
    token = Column(String(64), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    creado_en = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="sesiones")


class ConfigOperativa(Base):
    __tablename__ = "config_operativa"

    id = Column(Integer, primary_key=True)
    nurse_ratio = Column(Float, nullable=False, default=3.5)
    specialists = Column(Integer, nullable=False, default=5)
    beds = Column(Integer, nullable=False, default=100)
    umbral_alerta_min = Column(Integer, nullable=False, default=30)
    actualizado_en = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Cita(Base):
    __tablename__ = "citas"

    id = Column(Integer, primary_key=True, index=True)
    codigo_turno = Column(String(20), unique=True, index=True, nullable=False)
    paciente_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    nombre_paciente = Column(String(120), nullable=False)
    fecha = Column(Date, nullable=False)
    hora = Column(Time, nullable=False)
    motivo = Column(String(255), default="")
    urgency = Column(Integer, nullable=False)
    nurse_ratio = Column(Float, nullable=False)
    specialists = Column(Integer, nullable=False)
    beds = Column(Integer, nullable=False)
    tiempo_estimado_min = Column(Float, nullable=False)
    alerta = Column(String(40), nullable=False)
    modelo = Column(String(80), default="desconocido")
    estado = Column(String(20), nullable=False, default="pendiente")
    origen = Column(String(20), nullable=False, default="paciente")
    creado_en = Column(DateTime, default=datetime.utcnow)

    paciente = relationship("User", back_populates="citas")
