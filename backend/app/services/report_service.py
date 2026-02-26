import os
import json
import asyncio
import logging
from datetime import datetime
from typing import AsyncGenerator, Dict, Any, Optional
from pathlib import Path
import tempfile
import base64

from app.services.agent_service import generate_report

logger = logging.getLogger(__name__)

class ReportService:
    """
    Servicio mejorado para generar reportes veterinarios y de adiestramiento.
    Integra Gemini como agente IA para extraer datos y generar HTML/PDF.
    """

    # Mapeo de placeholders para veterinario
    VETERINARY_PLACEHOLDERS = {
        # Paciente
        "IA_NOMBRE_MASCOTA": "paciente.nombre",
        "IA_EDAD": "paciente.edad",
        "IA_RAZA": "paciente.raza",
        "IA_PESO": "paciente.peso",
        "IA_ESPECIE": "paciente.especie",
        
        # Síntomas y diagnóstico
        "IA_SIGNOS": "sintomas_formateados",
        "IA_DIAGNOSTICO": "diagnostico",
        "IA_RECETA_DETALLADA": "tratamiento",
        "IA_ANTECEDENTES_SI": "antecedentes_patologicos",
        "IA_ANTECEDENTES_NO": "antecedentes_no_patologicos",
        "IA_EXAMEN_FISICO": "examen_fisico",
        
        # Recomendaciones
        "IA_RECOMENDACIONES": "recomendaciones",
        
        # Metadata
        "IA_HISTORIA": "historia_clinica",
        "IA_FECHA": "fechaConsulta",
        "IA_NOTAS": "notas",
    }

    # Mapeo de placeholders para adiestramiento
    TRAINING_PLACEHOLDERS = {
        # Paciente
        "[NOMBRE_MASCOTA]": "paciente.nombre",
        "[EDAD]": "paciente.edad",
        "[RAZA]": "paciente.raza",
        "[PESO]": "paciente.peso",
        
        # Sesión de entrenamiento
        "[COMPORTAMIENTO]": "comportamiento_observado",
        "[CORRECCIONES]": "correcciones_formateadas",
        "[TAREAS]": "tareas_casa",
        "[PROGRESO]": "notas",
        "[FECHA]": "fechaConsulta",
    }

    @staticmethod
    async def extract_data_with_gemini(
        transcript: str,
        report_type: str = "veterinario"
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Envía la transcripción a Gemini y extrae datos estructurados.
        Usa yield para reportar progreso en tiempo real.
        """
        yield {"status": "Extracción", "message": "Conectando con Gemini..."}

        try:
            yield {"status": "Extracción", "message": "Procesando transcripción..."}

            extracted_data = await generate_report(transcript, report_type)

            yield {"status": "Extracción", "message": "Validando respuesta..."}

            # Validar campos requeridos
            _validate_extracted_data(extracted_data, report_type)
            
            yield {"status": "Extracción", "data": extracted_data, "completed": True}
            
        except json.JSONDecodeError as e:
            logger.error(f"Error al parsear JSON de Gemini: {e}")
            yield {
                "status": "error",
                "message": f"Error al procesar respuesta de Gemini: {str(e)}"
            }
            raise ValueError(f"Respuesta inválida de Gemini: {str(e)}")
        except Exception as e:
            logger.error(f"Error en extract_data_with_gemini: {e}")
            yield {
                "status": "error",
                "message": f"Error en extracción: {str(e)}"
            }
            raise

    @staticmethod
    async def generate_html_report(
        extracted_data: Dict[str, Any],
        report_type: str = "veterinario"
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Genera el HTML del reporte usando plantilla y datos extraídos.
        """
        yield {"status": "Revisión", "message": "Generando HTML..."}

        try:
            # Cargar plantilla
            template_path = Path(__file__).parent.parent / "templates"
            if report_type == "veterinario":
                template_file = template_path / "veterinario.html"
            else:
                template_file = template_path / "adiestramiento.html"

            if not template_file.exists():
                raise FileNotFoundError(f"Plantilla no encontrada: {template_file}")

            with open(template_file, 'r', encoding='utf-8') as f:
                template = f.read()

            # Preparar datos para sustitución
            placeholders = (
                ReportService.VETERINARY_PLACEHOLDERS
                if report_type == "veterinario"
                else ReportService.TRAINING_PLACEHOLDERS
            )

            # Reemplazar placeholders
            html = ReportService._replace_placeholders(
                template,
                extracted_data,
                placeholders
            )

            yield {
                "status": "Revisión",
                "message": "HTML generado exitosamente",
                "html": html,
                "completed": True
            }

        except Exception as e:
            logger.error(f"Error generando HTML: {e}")
            yield {"status": "error", "message": f"Error en generación HTML: {str(e)}"}
            raise

    @staticmethod
    async def generate_pdf_report(
        html_content: str,
        report_type: str = "veterinario",
        filename: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Genera PDF a partir del HTML usando Playwright.
        Ejecuta Playwright en un hilo separado con su propio event loop para
        compatibilidad con Windows (uvicorn usa SelectorEventLoop que no soporta subprocesos).
        """
        yield {"status": "Informe Final", "message": "Generando PDF..."}

        if filename is None:
            filename = f"report_{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        tmp_html_path = None
        try:
            import playwright  # Verificar que está instalado antes de continuar

            # Crear archivo temporal para HTML
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.html',
                delete=False,
                encoding='utf-8'
            ) as tmp_file:
                tmp_file.write(html_content)
                tmp_html_path = tmp_file.name

            yield {"status": "Informe Final", "message": "Inicializando renderizador..."}

            # Ejecutar en hilo separado con su propio event loop (fix para Windows)
            # asyncio.to_thread lanza la función en ThreadPoolExecutor.
            # Dentro del hilo, asyncio.run() crea un ProactorEventLoop (compatible con subprocesos).
            pdf_bytes = await asyncio.to_thread(
                _run_playwright_sync,
                tmp_html_path,
                filename
            )

            yield {"status": "Informe Final", "message": "Renderizando documento..."}

            if pdf_bytes is None:
                raise RuntimeError("Playwright no devolvió contenido PDF")

            # Guardar PDF en disco
            with open(filename, 'wb') as f:
                f.write(pdf_bytes)

            pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
            logger.info(f"PDF generado exitosamente: {filename}")

            yield {
                "status": "Informe Final",
                "message": "PDF generado exitosamente",
                "pdfPath": filename,
                "pdfBase64": pdf_base64,
                "completed": True
            }

        except ImportError:
            logger.warning("playwright no está instalado. Retornando solo HTML.")
            yield {
                "status": "Informe Final",
                "message": "PDF no disponible (playwright no instalado). Ejecuta: playwright install",
                "pdfPath": None,
                "htmlOnly": True,
                "completed": True
            }
        except Exception as e:
            logger.error(f"Error generando PDF: {type(e).__name__}: {e}")
            yield {
                "status": "Informe Final",
                "message": "PDF no disponible (reporte en HTML)",
                "pdfPath": None,
                "htmlOnly": True,
                "completed": True,
                "error": str(e)
            }
        finally:
            if tmp_html_path and os.path.exists(tmp_html_path):
                try:
                    os.unlink(tmp_html_path)
                except:
                    pass

    @staticmethod
    def _replace_placeholders(
        template: str,
        data: Dict[str, Any],
        placeholders: Dict[str, str]
    ) -> str:
        """
        Reemplaza placeholders en el template con datos extraídos.
        """
        html = template

        for placeholder_key, data_path in placeholders.items():
            value = _get_nested_value(data, data_path)

            if value is None:
                value = "—"
            elif isinstance(value, list):
                value = ", ".join(str(v) for v in value)
            else:
                value = str(value)

            html = html.replace(placeholder_key, value)

        return html

    @staticmethod
    async def full_pipeline(
        transcript: str,
        report_type: str = "veterinario"
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Pipeline completo: Extracción → HTML → PDF con progreso en tiempo real.
        """
        try:
            # Fase 1: Extracción con Gemini
            extracted_data = None
            async for progress in ReportService.extract_data_with_gemini(transcript, report_type):
                yield progress
                if progress.get("completed"):
                    extracted_data = progress.get("data")

            if not extracted_data:
                raise ValueError("No se pudo extraer datos del reporte")

            # Fase 2: Generar HTML
            html_content = None
            async for progress in ReportService.generate_html_report(extracted_data, report_type):
                yield progress
                if progress.get("completed"):
                    html_content = progress.get("html")

            if not html_content:
                raise ValueError("No se pudo generar HTML")

            # Fase 3: Generar PDF
            pdf_filename = f"report_{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf_base64 = None
            async for progress in ReportService.generate_pdf_report(html_content, report_type, pdf_filename):
                # Capturar el pdfBase64 del yield intermedio
                if progress.get("pdfBase64"):
                    pdf_base64 = progress.get("pdfBase64")
                yield progress

            # Respuesta final
            yield {
                "status": "completed",
                "message": "Reporte generado exitosamente",
                "extractedData": extracted_data,
                "htmlReport": html_content,
                "pdfPath": pdf_filename,
                "pdfBase64": pdf_base64
            }

        except Exception as e:
            logger.error(f"Error en pipeline completo: {e}")
            yield {
                "status": "error",
                "message": f"Error en generación de reporte: {str(e)}"
            }
            raise


# ============================================================================
# Funciones auxiliares
# ============================================================================

def _run_playwright_sync(html_path: str, filename: str) -> bytes:
    """
    Ejecuta Playwright de forma SÍNCRONA en un hilo separado.
    
    Llama a asyncio.run() que crea un event loop NUEVO (ProactorEventLoop en Windows),
    independiente del SelectorEventLoop de uvicorn. Esto resuelve el NotImplementedError
    que ocurre cuando Playwright intenta crear subprocesos desde el loop de uvicorn.
    """
    import sys

    async def _playwright_task() -> bytes:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                page = await browser.new_page()
                try:
                    await page.goto(
                        f'file:///{os.path.abspath(html_path).replace(os.sep, "/")}',
                        wait_until='networkidle',
                        timeout=30000
                    )
                    pdf_bytes = await page.pdf(
                        format='A4',
                        margin={'top': '0.5in', 'right': '0.5in',
                                'bottom': '0.5in', 'left': '0.5in'},
                        print_background=True
                    )
                    return pdf_bytes
                finally:
                    await page.close()
            finally:
                await browser.close()

    # En Windows, forzar ProactorEventLoop para el loop nuevo
    if sys.platform == 'win32':
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(_playwright_task())
        finally:
            loop.close()
    else:
        return asyncio.run(_playwright_task())

def _validate_extracted_data(data: Dict[str, Any], report_type: str) -> None:
    """Valida que los datos extraídos contienen los campos requeridos."""
    required_fields = [
        "tipoInforme",
        "paciente",
        "sintomas" if report_type == "veterinario" else "comportamiento_observado",
        "diagnostico" if report_type == "veterinario" else "correcciones",
        "tratamiento" if report_type == "veterinario" else "tareas_casa",
        "fechaConsulta"
    ]

    for field in required_fields:
        if field not in data:
            raise ValueError(f"Campo requerido faltante en respuesta: {field}")

    if not isinstance(data.get("paciente"), dict):
        raise ValueError("'paciente' debe ser un objeto")

    paciente = data["paciente"]
    required_paciente_fields = ["nombre", "especie", "edad", "raza", "peso"]
    for field in required_paciente_fields:
        if field not in paciente:
            raise ValueError(f"Campo requerido en 'paciente': {field}")


def _get_nested_value(data: Dict[str, Any], path: str) -> Any:
    """
    Obtiene un valor anidado usando notación de puntos.
    Ejemplo: "paciente.nombre" → data['paciente']['nombre']
    """
    keys = path.split('.')
    value = data

    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return None

    return value
