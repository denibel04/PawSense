import os
import json
import asyncio
from google import genai
from google.genai import types
from app.schemas.report import ClinicalReportSchema, TrainingReportSchema

client = genai.Client()

async def generate_report(transcribed_text: str, report_type: str = "veterinario") -> dict:
    if not transcribed_text.strip():
        print("[AGENT] Transcripción vacía, devolviendo {}.")
        return {}

    if report_type == "veterinario":
        schema = ClinicalReportSchema
        prompt = f"""Eres un asistente veterinario experto. A partir de la transcripción de una consulta veterinaria, \
extrae y estructura la información en los siguientes campos:

- symptoms: lista de síntomas clínicos mencionados (array de strings, e.g. ["fiebre", "vómitos"])
- diagnosis: diagnóstico provisional o definitivo mencionado (string)
- treatment: tratamiento indicado, medicamentos o procedimientos (string)
- notes: cualquier otra observación relevante, seguimiento o recomendación (string)

Si algún campo no se menciona explícitamente, déjalo vacío ("" o []).

Transcripción de la consulta:
\"\"\"{transcribed_text}\"\"\"
"""
    else:
        schema = TrainingReportSchema
        prompt = f"""Eres un experto en adiestramiento canino. A partir de la transcripción de una sesión de entrenamiento, \
extrae y estructura la información en los siguientes campos:

- behavior_observed: el comportamiento principal del perro observado durante la sesión (string)
- corrections: lista de correcciones, técnicas o comandos aplicados durante la sesión (array de strings)
- homework: tareas o ejercicios que el dueño debe practicar en casa (string)
- notes: observaciones adicionales sobre el progreso o actitud del perro (string)

Si algún campo no se menciona explícitamente, déjalo vacío ("" o []).

Transcripción de la sesión:
\"\"\"{transcribed_text}\"\"\"
"""

    def _call_gemini():
        return client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
            ),
        )

    try:
        print(f"[AGENT] Llamando a Gemini para '{report_type}' con {len(transcribed_text)} caracteres...")
        response = await asyncio.to_thread(_call_gemini)
        raw = response.text
        print(f"[AGENT] Respuesta raw de Gemini:\n{raw}")
        result = json.loads(raw)
        print(f"[AGENT] Campos extraídos: {list(result.keys())}")
        return result
    except json.JSONDecodeError as e:
        print(f"[AGENT] ERROR al parsear JSON de Gemini: {e}")
        print(f"[AGENT] Texto recibido: {response.text if response else 'N/A'}")
        return {}
    except Exception as e:
        print(f"[AGENT] ERROR inesperado: {e}")
        return {}
