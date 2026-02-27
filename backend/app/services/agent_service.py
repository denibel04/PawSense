import os
import json
from google import genai
from google.genai import types
from app.schemas.report import ClinicalReportSchema, TrainingReportSchema

client = genai.Client()

def get_prompt_and_schema(report_type: str, context_text: str = "") -> tuple:
    if report_type == "veterinario":
        schema = ClinicalReportSchema
        prompt = f"""Eres un asistente veterinario experto. A partir del contexto proporcionado de una consulta veterinaria, \
extrae y estructura la información en un JSON que incluya:

INFORMACIÓN CRÍTICA (DEBE llenar):
- tipoInforme: siempre "veterinaria"
- transcripcion_original: Un resumen detallado o transcripción de lo que se dijo en el audio/texto original.
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
IMPORTANTE FORMATO: Asegúrate de usar mayúsculas y minúsculas correctamente (ej. la primera letra de las oraciones en mayúscula, nombres propios en mayúscula). No escribas todo en minúsculas.
NO devuelvas texto explicativo, SOLO JSON válido.

Contexto de la consulta:
\"\"\"{context_text}\"\"\"
"""
    else:
        schema = TrainingReportSchema
        prompt = f"""Eres un experto certificado en adiestramiento canino. A partir del contexto proporcionado de una sesión de entrenamiento, \
extrae y estructura la información en un JSON que incluya:

INFORMACIÓN CRÍTICA (DEBE llenar):
- tipoInforme: siempre "adiestramiento"
- transcripcion_original: Un resumen textual detallado o transcripción de lo que se dijo en el audio original.
- paciente: objeto con nombre, especie, edad, raza, peso, genero (extrae del contexto)
- comportamiento_observado: el comportamiento principal del perro durante la sesión
- correcciones: lista de técnicas, comandos o correcciones aplicadas (array de strings)
- tareas_casa: ejercicios específicos que el propietario debe practicar en casa
- recomendaciones: consejos para mejorar el entrenamiento
- notas: observaciones sobre el progreso o actitud del perro
- fechaConsulta: fecha actual en ISO format

Si algún campo no se menciona explícitamente, usa valores por defecto apropiados.
IMPORTANTE FORMATO: Asegúrate de usar mayúsculas y minúsculas correctamente (ej. la primera letra de las oraciones en mayúscula, nombres propios en mayúscula). No escribas todo en minúsculas.
NO devuelvas texto explicativo, SOLO JSON válido.

Contexto de la sesión:
\"\"\"{context_text}\"\"\"
"""
    return prompt, schema
