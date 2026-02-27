import asyncio
import base64
import json
import logging
import os
import sys
import tempfile
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Optional

logger = logging.getLogger(__name__)

class ReportGenerationError(Exception):
    """Excepción base para errores en la generación de reportes."""
    pass

class DataExtractionError(ReportGenerationError):
    """Error al extraer o validar datos de la transcripción/audio."""
    pass

class HTMLGenerationError(ReportGenerationError):
    """Error al generar el HTML a partir de la plantilla y los datos."""
    pass

class TemplateNotFoundError(HTMLGenerationError):
    """La plantilla HTML requerida no existe."""
    pass

class PDFGenerationError(ReportGenerationError):
    """Error al convertir el HTML a PDF usando Playwright."""
    pass

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
                raise TemplateNotFoundError(f"Plantilla no encontrada: {template_file}")

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
            if isinstance(e, ReportGenerationError):
                logger.error(f"Error en plantilla: {e}")
                yield {"status": "error", "message": str(e), "error": True}
                raise
            logger.error(f"Error generando HTML: {e}", exc_info=True)
            yield {"status": "error", "message": f"Error inesperado en generación HTML: {str(e)}", "error": True}
            raise HTMLGenerationError(f"Error inesperado en html: {str(e)}") from e

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

            yield {"status": "Informe Final", "message": "Renderizando documento..."}

            # Enviar trabajo de renderizado al navegador global persistente
            pdf_bytes = await asyncio.to_thread(
                PlaywrightPDFGenerator.generate_pdf_sync,
                tmp_html_path
            )

            if pdf_bytes is None:
                raise PDFGenerationError("Playwright devolvió contenido PDF nulo")

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
                "completed": True,
                "error": True
            }
        except RuntimeError as e:
            logger.error(f"Error de ejecución generando PDF: {e}", exc_info=True)
            yield {
                "status": "Informe Final",
                "message": "PDF no disponible debido a error de ejecución",
                "pdfPath": None,
                "htmlOnly": True,
                "completed": True,
                "error": True,
                "errorMessage": str(e)
            }
        except Exception as e:
            logger.error(f"Error general generando PDF: {type(e).__name__}: {e}", exc_info=True)
            yield {
                "status": "Informe Final",
                "message": "PDF no disponible (reporte en HTML)",
                "pdfPath": None,
                "htmlOnly": True,
                "completed": True,
                "error": True,
                "errorMessage": str(e)
            }
        finally:
            if tmp_html_path and os.path.exists(tmp_html_path):
                try:
                    os.unlink(tmp_html_path)
                except Exception as e:
                    logger.warning(f"No se pudo eliminar archivo temporal {tmp_html_path}: {e}")

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


# ============================================================================
# Funciones auxiliares
# ============================================================================

class PlaywrightPDFGenerator:
    """
    Gestiona una instancia persistente del navegador de Playwright en un hilo
    separado para una generación de PDF ultrarrápida. Evita tener que iniciar
    y cerrar el motor Chromium en cada petición.
    """
    _thread = None
    _loop = None
    _browser = None
    _playwright = None

    @classmethod
    def start(cls):
        if cls._thread is not None:
            return
        
        # Crear un loop exclusivo para Playwright (ProactorEventLoop requerido en Windows)
        if sys.platform == 'win32':
            cls._loop = asyncio.ProactorEventLoop()
        else:
            cls._loop = asyncio.new_event_loop()
            
        cls._thread = threading.Thread(target=cls._run_loop, daemon=True)
        cls._thread.start()
        
        # Esperar a que el navegador se inicialice
        future = asyncio.run_coroutine_threadsafe(cls._init_browser(), cls._loop)
        try:
            future.result(timeout=15)
        except Exception as e:
            logger.error(f"Error inicializando Playwright persistente: {e}")

    @classmethod
    def _run_loop(cls):
        try:
            asyncio.set_event_loop(cls._loop)
            cls._loop.run_forever()
        except Exception as e:
            logger.error(f"Event loop persistente detenido de forma inesperada: {e}")

    @classmethod
    async def _init_browser(cls):
        try:
            from playwright.async_api import async_playwright
            cls._playwright = await async_playwright().start()
            cls._browser = await cls._playwright.chromium.launch(headless=True)
            logger.info("Navegador persistente de Playwright inicializado.")
        except ImportError:
            logger.warning("No se pudo iniciar el navegador persistente porque Playwright no está instalado. Ejecute: pip install playwright && playwright install")
            raise
        except Exception as e:
            logger.error(f"Error en _init_browser: {e}")
            raise

    @classmethod
    def stop(cls):
        if cls._loop and cls._loop.is_running():
            future = asyncio.run_coroutine_threadsafe(cls._close_browser(), cls._loop)
            try:
                future.result(timeout=5)
            except Exception:
                pass
            cls._loop.call_soon_threadsafe(cls._loop.stop)
            if cls._thread:
                cls._thread.join(timeout=5)

    @classmethod
    async def _close_browser(cls):
        if cls._browser:
            await cls._browser.close()
        if cls._playwright:
            await cls._playwright.stop()
        logger.info("Navegador persistente de Playwright cerrado.")

    @classmethod
    def generate_pdf_sync(cls, html_path: str) -> bytes:
        if not cls._loop or not cls._loop.is_running():
            raise RuntimeError("El navegador persistente no está corriendo. ¿Se llamó a PlaywrightPDFGenerator.start()?")
        
        future = asyncio.run_coroutine_threadsafe(
            cls._generate_pdf_async(html_path), 
            cls._loop
        )
        return future.result()

    @classmethod
    async def _generate_pdf_async(cls, html_path: str) -> bytes:
        if not cls._browser:
            raise RuntimeError("Browser persistente no inicializado.")
        
        page = await cls._browser.new_page()
        try:
            val = f'file:///{os.path.abspath(html_path).replace(os.sep, "/")}'
            await page.goto(val, wait_until='load', timeout=30000)
            
            pdf_bytes = await page.pdf(
                format='A4',
                margin={'top': '0.5in', 'right': '0.5in', 'bottom': '0.5in', 'left': '0.5in'},
                print_background=True
            )
            return pdf_bytes
        finally:
            await page.close()

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
            raise DataExtractionError(f"Campo requerido faltante en respuesta: {field}")

    if not isinstance(data.get("paciente"), dict):
        raise DataExtractionError("'paciente' debe ser un objeto")

    paciente = data["paciente"]
    required_paciente_fields = ["nombre", "especie", "edad", "raza", "peso"]
    for field in required_paciente_fields:
        if field not in paciente:
            raise DataExtractionError(f"Campo requerido en 'paciente': {field}")


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
