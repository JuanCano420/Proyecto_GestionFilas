URGENCIA_ETIQUETAS = {
    1: "Baja",
    2: "Media",
    3: "Alta",
    4: "Crítica",
}

MOTIVOS = [
    {"motivo": "Control rutinario / chequeo", "urgency": 1},
    {"motivo": "Renovación de fórmula médica", "urgency": 1},
    {"motivo": "Certificado o incapacidad", "urgency": 1},
    {"motivo": "Consulta general", "urgency": 2},
    {"motivo": "Dolor leve o molestia persistente", "urgency": 2},
    {"motivo": "Seguimiento post-operatorio", "urgency": 2},
    {"motivo": "Fiebre o infección", "urgency": 3},
    {"motivo": "Dolor intenso", "urgency": 3},
    {"motivo": "Herida que requiere revisión", "urgency": 3},
    {"motivo": "Dificultad para respirar", "urgency": 4},
    {"motivo": "Dolor de pecho", "urgency": 4},
    {"motivo": "Trauma o sangrado abundante", "urgency": 4},
]

MOTIVO_A_URGENCIA = {item["motivo"]: item["urgency"] for item in MOTIVOS}


def catalogo_motivos():
    return [
        {
            **item,
            "urgencia_etiqueta": URGENCIA_ETIQUETAS[item["urgency"]],
        }
        for item in MOTIVOS
    ]


def urgencia_por_motivo(motivo: str) -> int | None:
    return MOTIVO_A_URGENCIA.get(motivo.strip())
