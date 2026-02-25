from pydantic import BaseModel, Field
from typing import List

class ClinicalReportSchema(BaseModel):
    symptoms: List[str] = Field(description="Lista de síntomas reportados", default=[])
    diagnosis: str = Field(description="Diagnóstico preliminar o definitivo", default="No especificado")
    treatment: str = Field(description="Tratamiento recomendado", default="Ninguno")
    notes: str = Field(description="Notas adicionales", default="")

class TrainingReportSchema(BaseModel):
    behavior_observed: str = Field(description="Comportamiento principal observado", default="")
    corrections: List[str] = Field(description="Lista de correcciones aplicadas o intentadas", default=[])
    homework: str = Field(description="Tareas asignadas para la casa", default="Ninguna")
    notes: str = Field(description="Notas generales sobre el progreso", default="")
