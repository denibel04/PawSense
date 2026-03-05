from typing import AsyncGenerator
import logging
import asyncio
import random
from fastapi import HTTPException, status
from google import genai
from google.genai import types
from app.core.config import settings
from app.schemas.chat import ChatRequest
from app.services.chat_utils import (
    is_dog_domain,
    get_rate_limit_message,
    get_out_of_domain_message,
    build_system_prompt,
    is_rate_limit_error,
    detect_intent,
    is_medical_emergency,
    get_emergency_response,
    build_whitelist_system_prompt,
    strip_markdown,
    detect_report_intent,
    detect_report_type_from_conversation,
    REPORT_DOG_QUESTIONS,
    extract_known_dog_info,
    OFFICIAL_SOURCES,
)

logger = logging.getLogger(__name__)


# Phrases that indicate the model is redirecting an off-topic question
_REDIRECTION_INDICATORS = [
    "como experto en perros",
    "solo puedo ayudar",
    "temas caninos",
    "mi propósito es ayudarte con",
    "nuestros amigos peludos",
    "todo lo relacionado con",
    "sobre perros",
    "no puedo ayudarte con",
    "fuera de mi área",
    "as a dog expert",
    "only help with dog",
]


def _is_redirection_response(text: str) -> bool:
    """Detect if the model response is redirecting an off-topic question."""
    lower = text.lower()
    return sum(1 for ind in _REDIRECTION_INDICATORS if ind in lower) >= 2


def _ensure_sources(text: str, intent: str) -> str:
    """
    If the model response doesn't already contain source URLs,
    append the relevant ones based on intent.
    Skip sources entirely when the response is just redirecting an off-topic question.
    """
    # Never append sources to redirection / off-topic responses
    if _is_redirection_response(text):
        return text

    # Check if ANY whitelist URL is already present
    sources = OFFICIAL_SOURCES.get(intent, [])
    has_sources = any(url in text for url in sources)
    
    if has_sources:
        return text
    
    # Append sources block
    if intent == "medical":
        sources_block = (
            "\n\nFuentes (para contrastar):\n"
            "AVMA - https://www.avma.org/\n"
            "MSD Vet Manual - https://www.msdvetmanual.com/\n"
            "ASPCA - https://www.aspca.org/"
        )
    elif intent == "training":
        sources_block = (
            "\n\nFuentes (para contrastar):\n"
            "AVSAB - https://avsab.org/\n"
            "AKC - https://www.akc.org/\n"
            "Dogs Trust - https://www.dogstrust.org.uk/"
        )
    else:
        return text
    
    return text + sources_block

class ChatService:
    def __init__(self):
        try:
            self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        except Exception as e:
            logger.error(f"Error initializing Google GenAI Client: {e}")
            self.client = None

    async def process_chat_request(self, request: ChatRequest) -> AsyncGenerator[str, None]:
        # Validations
        if not settings.GOOGLE_API_KEY:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Google API Key not configured."
            )

        if not self.client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI Service not initialized."
            )

        if not request.question or not request.question.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Question cannot be empty."
            )

        # Domain Check (include conversation history for follow-up messages)
        history_dicts = [{
            "role": m.role, "content": m.content
        } for m in request.history] if request.history else []
        if not is_dog_domain(request.question, request.context, history_dicts):
            logger.info(f"Out of domain question: {request.question[:50]}...")
            yield get_out_of_domain_message()
            return

        # Report Intent Check - detect if user wants to generate a report
        if detect_report_intent(request.question):
            report_type = detect_report_type_from_conversation(history_dicts)
            all_questions = REPORT_DOG_QUESTIONS.get(report_type, REPORT_DOG_QUESTIONS["veterinario"])
            
            # Extract already-known data from context and conversation (user messages only)
            known_info = extract_known_dog_info(request.context, history_dicts)
            
            # Filter out questions for fields we already know
            missing_questions = [q for q in all_questions if q["field"] not in known_info]
            
            # Build the response
            tipo_label = "veterinario" if report_type == "veterinario" else "de adiestramiento"
            
            if known_info:
                known_parts = []
                field_labels = {"nombre": "Nombre", "raza": "Raza", "edad": "Edad", "peso": "Peso", "genero": "Género"}
                for field, value in known_info.items():
                    label = field_labels.get(field, field.capitalize())
                    known_parts.append(f"{label}: {value}")
                known_str = ", ".join(known_parts)
                msg = (
                    f"¡Perfecto! Voy a preparar un informe {tipo_label} basado en nuestra conversación. "
                    f"Ya tengo estos datos de tu perro: {known_str}. "
                )
            else:
                msg = (
                    f"¡Perfecto! Voy a preparar un informe {tipo_label} basado en nuestra conversación. "
                )
            
            if missing_questions:
                msg += "Solo necesito que me confirmes algunos datos más:\n\n"
                for i, q in enumerate(missing_questions, 1):
                    msg += f"{i}. {q['question']}\n"
            else:
                msg += "Ya tengo toda la información necesaria. ¡Generando el informe!"
            
            # Encode known info and missing fields in the marker
            import json as _json
            known_json = _json.dumps(known_info, ensure_ascii=False)
            missing_fields_json = _json.dumps([q['field'] for q in missing_questions], ensure_ascii=False)
            msg += (
                f"\n[REPORT_INTENT:{report_type}|KNOWN:{known_json}|MISSING:{missing_fields_json}]"
            )
            yield msg
            return

        # Intent Detection
        intent = detect_intent(request.question, request.context)
        logger.info(f"Detected intent: {intent}")

        # Medical Emergency Check
        if is_medical_emergency(request.question, request.context):
            logger.warning(f"Medical emergency detected: {request.question[:50]}...")
            emergency_msg = get_emergency_response()
            yield emergency_msg
            return

        # Prepare Chat History
        chat_history = []
        
        if intent in ("medical", "training"):
            system_prompt = build_whitelist_system_prompt(intent, request.context)
        else:
            system_prompt = build_system_prompt(request.context)
        
        chat_history.append(types.Content(
            role="user",
            parts=[types.Part.from_text(text=system_prompt)]
        ))
        
        # Reforzar el cumplimiento de fuentes en la respuesta priming del modelo
        if intent in ("medical", "training"):
            priming_text = (
                "Entendido. Responderé basándome en las fuentes oficiales indicadas. "
                "Al final de cada respuesta informativa sobre perros incluiré el bloque de 'Fuentes (para contrastar):' "
                "con las URLs correspondientes de la whitelist. No usaré markdown. "
                "Si la pregunta no es sobre perros, solo redirigiré al usuario amablemente sin incluir fuentes."
            )
        else:
            priming_text = "Entendido. Responderé de forma natural sin markdown."
        
        chat_history.append(types.Content(
            role="model",
            parts=[types.Part.from_text(text=priming_text)]
        ))
        
        for msg in request.history:
            role = "model" if msg.role == "assistant" else "user"
            chat_history.append(types.Content(
                role=role,
                parts=[types.Part.from_text(text=msg.content)]
            ))

        model_name = 'gemini-2.5-flash'
        
        # Retry Logic with Exponential Backoff
        max_retries = 3
        base_delay = 1.0  # seconds
        
        for attempt in range(max_retries):
            try:
                # Using async client for streaming
                async_client = genai.Client(api_key=settings.GOOGLE_API_KEY)
                async_chat = async_client.aio.chats.create(
                    model=model_name,
                    history=chat_history
                )
                
                response_stream = await async_chat.send_message_stream(
                    message=request.question,
                    config=types.GenerateContentConfig(response_mime_type="text/plain")
                )
                
                # Accumulate full response for markdown stripping
                full_response = ""
                async for chunk in response_stream:
                    if chunk.text is not None:
                        full_response += chunk.text
                
                # Post-process: strip any remaining markdown
                cleaned_response = strip_markdown(full_response)
                
                # Force-append sources if the model didn't include them
                if intent in ("medical", "training"):
                    cleaned_response = _ensure_sources(cleaned_response, intent)
                
                yield cleaned_response
                
                # Break the retry loop on success
                return

            except Exception as e:
                is_last_attempt = attempt == max_retries - 1
                
                if is_rate_limit_error(e):
                    if not is_last_attempt:
                        # Exponential backoff + Jitter
                        delay = (base_delay * (2 ** attempt)) + random.uniform(0, 0.5)
                        logger.warning(f"Rate limit exceeded. Retrying in {delay:.2f}s (Attempt {attempt + 1}/{max_retries})")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        logger.error(f"Rate limit exceeded after {max_retries} attempts.")
                        yield f"\n\n{get_rate_limit_message()}"
                        return
                else:
                    # Non-retriable error (or we decided not to retry other errors)
                    logger.error(f"Error during chat streaming: {e}")
                    yield f"\n\n[System Error: Unable to complete response. Please try again later.]"
                    return
