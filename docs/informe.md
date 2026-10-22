# Documento de Proyecto: Sistema Inteligente de Gestión de Filas y Tiempos de Espera

**Curso:** PDI Y VISION ARTIFICIAL 
**Proyecto:** Proyecto Final
**Docente:** Julián René Muñoz Burbano  
**Integrantes:** Juan Fernando Cano, David Cuartas y Juan Sebastian Beron 
**Fecha:** 22 de Octubre del 2026 

---

## 1. Visión y Alcance del Proyecto

*   **Problema:** La gestión manual de filas de espera en entornos como clínicas u oficinas de atención genera incertidumbre en los usuarios, mala asignación de recursos y cuellos de botella operativos.
*   **Solución:** Un sistema de software completo que permite registrar turnos y, mediante un microservicio de Inteligencia Artificial (Random Forest), estima el tiempo de espera en minutos basándose en variables operativas (urgencia, disponibilidad de personal, capacidad instalada).
*   **Alcance:**
    *   **Incluye:** Generación de turnos, predicción de tiempos de espera, panel de visualización para operadores (Frontend), API REST (Backend) y servicio de inferencia (IA).
    *   **Excluye:** Gestión de historias clínicas de pacientes, control automático de puertas o pantallas físicas de llamado.

---

## 2. Ingeniería de Requisitos

### 2.1 Historias de Usuario y Criterios de Aceptación

| ID | Historia de Usuario | Criterio de Aceptación |
| :--- | :--- | :--- |
| **HU-01** | Como operador, quiero ingresar los datos operativos actuales (urgencia, enfermeras, especialistas, camas) para generar un nuevo turno. | El sistema debe validar que la urgencia esté entre 1 y 4. Debe devolver un ID de turno y el tiempo estimado. |
| **HU-02** | Como operador, quiero que el sistema me alerte si el tiempo de espera estimado supera los 30 minutos, para tomar acciones correctivas. | Si la predicción de la IA es > 30 min, el sistema debe mostrar una alerta visual en color rojo. |
| **HU-03** | Como administrador, quiero que el sistema use un modelo de IA entrenado y versionado para asegurar que las predicciones sean precisas y reproducibles. | El backend debe consumir el microservicio de IA, el cual debe reportar la versión del modelo utilizado en la respuesta JSON. |
| **HU-04** | Como administrador de TI, quiero que las APIs estén protegidas para que solo el personal autorizado pueda generar turnos. | El backend debe exigir un `API_KEY` válido en los headers para procesar la solicitud de turno. |

### 2.2 Matriz de Trazabilidad

| Requisito | Componente | Prueba Asociada (Evidencia) |
| :--- | :--- | :--- |
| **HU-01** | Backend (`/api/turno`) / Frontend | `test_crear_turno_urgencia_invalida` / Prueba manual en Frontend |
| **HU-02** | Backend (Regla de negocio) | Validación en `backend/main.py` (línea 31) / Captura de pantalla |
| **HU-03** | Microservicio IA (`/predict`) | `ai_service/train.py` (guardado del modelo) / JSON de respuesta |
| **HU-04** | Backend (Seguridad) | `test_crear_turno_sin_api_key` |

---

## 3. Arquitectura y Diseño

### 3.1 Diagrama de Contexto y Componentes

El sistema sigue una arquitectura desacoplada de microservicios:

1.  **Frontend (HTML/JS):** Interfaz de usuario para ingreso de datos y visualización.
2.  **Backend (FastAPI):** Contiene las reglas de negocio (alertas, validaciones) y seguridad (API Key).
3.  **Microservicio IA (FastAPI + Scikit-learn):** Encargado exclusivo de la inferencia del modelo.

graph TD
    A[Usuario/Operador] -->|Ingresa datos| B(Frontend Web)
    B -->|POST /api/turno| C{Backend API}
    C -->|Valida API Key| D[Reglas de Negocio]
    D -->|POST /predict| E[Microservicio IA]
    E -->|Carga model.pkl| F((Random Forest))
    E -->|Retorna Predicción| D
    D -->|Genera Turno y Alerta| B