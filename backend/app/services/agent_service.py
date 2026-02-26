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
extrae y estructura la información en un JSON que incluya:

INFORMACIÓN CRÍTICA (DEBE llenar):
- tipoInforme: siempre "veterinaria"
- paciente: objeto con nombre, especie, edad, raza, peso, genero (extrae del contexto)
- sintomas: lista de síntomas clínicos mencionados (array de strings)
- diagnostico: diagnóstico provisional o definitivo
- tratamiento: medicamentos, dosis, procedimientos indicados
- recomendaciones: consejos para el propietario sobre cuidados posteriores
- notas: observaciones adicionales
- fechaConsulta: fecha actual en ISO format

INFORMACIÓN SECUNDARIA (completa si está disponible):
- antecedentes_patologicos: enfermedades previas o complicaciones
- antecedentes_no_patologicos: vacunaciones, cirugías previas, hábitos
- examen_fisico: hallazgos del examen físico realizado

Si algún campo no se menciona explícitamente, usa valores por defecto apropiados ("No especificado", arrays vacíos, etc).
NO devuelvas texto explicativo, SOLO JSON válido.

Transcripción de la consulta:
\"\"\"{transcribed_text}\"\"\"
"""
    else:
        schema = TrainingReportSchema
        prompt = f"""Eres un experto certificado en adiestramiento canino. A partir de la transcripción de una sesión de entrenamiento, \
extrae y estructura la información en un JSON que incluya:

INFORMACIÓN CRÍTICA (DEBE llenar):
- tipoInforme: siempre "adiestramiento"
- paciente: objeto con nombre, especie, edad, raza, peso, genero (extrae del contexto)
- comportamiento_observado: el comportamiento principal del perro durante la sesión
- correcciones: lista de técnicas, comandos o correcciones aplicadas (array de strings)
- tareas_casa: ejercicios específicos que el propietario debe practicar en casa
- recomendaciones: consejos para mejorar el entrenamiento
- notas: observaciones sobre el progreso o actitud del perro
- fechaConsulta: fecha actual en ISO format

Si algún campo no se menciona explícitamente, usa valores por defecto apropiados.
NO devuelvas texto explicativo, SOLO JSON válido.

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
        print(f"[AGENT] Texto recibido: {response.text if hasattr(response, 'text') else 'N/A'}")
        return {}
    except Exception as e:
        print(f"[AGENT] ERROR inesperado: {e}")
        return {}
