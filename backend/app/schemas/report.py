from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

class PacienteSchema(BaseModel):
    nombre: str = Field(description="Nombre del paciente (perro/gato)", default="No especificado")
    especie: str = Field(description="Especie (perro, gato, etc.)", default="perro")
    edad: str = Field(description="Edad del paciente", default="No especificada")
    raza: str = Field(description="Raza del paciente", default="No especificada")
    peso: str = Field(description="Peso del paciente en Kg", default="No especificado")
    genero: str = Field(description="Sexo (macho/hembra)", default="No especificado")

class ClinicalReportSchema(BaseModel):
    tipoInforme: str = Field(default="veterinaria")
    paciente: PacienteSchema
    sintomas: List[str] = Field(description="Lista de síntomas reportados", default=[])
    diagnostico: str = Field(description="Diagnóstico preliminar o definitivo", default="No especificado")
    tratamiento: str = Field(description="Tratamiento recomendado", default="Ninguno")
    recomendaciones: str = Field(description="Recomendaciones para el propietario", default="")
    notas: str = Field(description="Notas adicionales", default="")
    fechaConsulta: str = Field(description="Fecha de la consulta", default_factory=lambda: datetime.now().isoformat())
    antecedentes_patologicos: str = Field(description="Antecedentes patológicos", default="")
    antecedentes_no_patologicos: str = Field(description="Antecedentes no patológicos", default="")
    examen_fisico: str = Field(description="Resultados del examen físico", default="")

class TrainingReportSchema(BaseModel):
    tipoInforme: str = Field(default="adiestramiento")
    paciente: PacienteSchema
    comportamiento_observado: str = Field(description="Comportamiento principal observado durante la sesión", default="")
    correcciones: List[str] = Field(description="Correcciones, técnicas o comandos aplicados", default=[])
    tareas_casa: str = Field(description="Tareas o ejercicios para practicar en casa", default="Ninguna")
    recomendaciones: str = Field(description="Recomendaciones adicionales", default="")
    notas: str = Field(description="Notas generales sobre el progreso", default="")
    fechaConsulta: str = Field(description="Fecha de la sesión", default_factory=lambda: datetime.now().isoformat())
