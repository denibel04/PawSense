from pydantic import BaseModel, Field
from typing import List

class ClinicalReportSchema(BaseModel):
    resena: str = Field(description="Reseña del paciente", default="")
    anamnesis: str = Field(description="Anamnesis e historia clínica", default="")
    exploracion_fisica: str = Field(description="Exploración física general", default="")
    exploracion_especial: str = Field(description="Exploración específica u oftalmológica", default="")
    diagnostico: str = Field(description="Diagnóstico presuntivo", default="")
    tratamiento: List[str] = Field(description="Tratamiento pautado", default=[])
    recomendaciones: List[str] = Field(description="Recomendaciones y revisión", default=[])

class TrainingReportSchema(BaseModel):
    fecha: str = Field(description="Fecha de la sesión en formato dd/mm/yyyy", default="", pattern=r"^(?:(?:0[1-9]|[12]\d|3[01])/(?:0[1-9]|1[0-2])/\d{4})?$")
    duracion: str = Field(description="Duración de la sesión", default="")
    objetivos: List[str] = Field(description="Objetivos específicos de la sesión", default=[])
    conductas_resultados: str = Field(description="Conductas trabajadas y sus resultados", default="")
    tipo_refuerzo: str = Field(description="Tipo de refuerzo utilizado", default="")
    observaciones_actitud: str = Field(description="Observaciones generales o actitud del perro", default="")
