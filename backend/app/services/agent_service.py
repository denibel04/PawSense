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

- resena: información inicial del paciente como raza, edad, peso (string)
- anamnesis: motivo de la consulta, historia clínica y eventos recientes (string)
- exploracion_fisica: hallazgos de la exploración física general como mucosas, TRC, palpación (string)
- exploracion_especial: observaciones detalladas de la exploración oftalmológica u otra específica (string)
- diagnostico: diagnóstico presuntivo o definitivo (string)
- tratamiento: medicamentos o intervenciones pautadas con sus indicaciones (array de strings)
- recomendaciones: otros consejos como usar collar isabelino o fecha de próxima revisión (array de strings)

Si algún campo no se menciona explícitamente, déjalo vacío ("" o []).

Transcripción de la consulta:
\"\"\"{transcribed_text}\"\"\"
"""
    else:
        schema = TrainingReportSchema
        prompt = f"""Eres un experto en adiestramiento canino. A partir de la transcripción de una sesión de entrenamiento, \
extrae y estructura la información en los siguientes campos:

- fecha: Fecha mencionada en la que se realizó la sesión, estructurada obligatoriamente en formato dd/mm/yyyy (string)
- duracion: Tiempo de duración de la sesión (string)
- objetivos: Lista de objetivos específicos planteados o trabajados (array de strings)
- conductas_resultados: Descripción de las conductas sobre las que se ha trabajado y sus resultados (string)
- tipo_refuerzo: Tipo de métodos o refuerzos usados durante la sesión (string)
- observaciones_actitud: Actitud del perro u observaciones finales (string)

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
