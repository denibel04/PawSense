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
    get_whitelist_references,
)

logger = logging.getLogger(__name__)

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

        # Domain Check
        if not is_dog_domain(request.question, request.context):
            logger.info(f"Out of domain question: {request.question[:50]}...")
            yield get_out_of_domain_message()
            return

        # Intent Detection
        intent = detect_intent(request.question, request.context)
        logger.info(f"Detected intent: {intent}")

        # Medical Emergency Check
        if is_medical_emergency(request.question, request.context):
            logger.warning(f"Medical emergency detected: {request.question[:50]}...")
            emergency_msg = get_emergency_response()
            whitelist_refs = get_whitelist_references("medical", num_refs=3)
            yield f"{emergency_msg}\n\n{whitelist_refs}"
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
        chat_history.append(types.Content(
            role="model",
            parts=[types.Part.from_text(text="Entendido. Responderé basándome en fuentes confiables.")]
        ))
        
        for msg in request.history:
            role = "model" if msg.role == "assistant" else "user"
            chat_history.append(types.Content(
                role=role,
                parts=[types.Part.from_text(text=msg.content)]
            ))

        model_name = 'gemini-2.5-pro'
        
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
                
                async for chunk in response_stream:
                    if chunk.text:
                        yield chunk.text
                
                # If we finish the stream successfully, verify domain specific additions
                if intent in ("medical", "training"):
                    whitelist_refs = get_whitelist_references(intent, num_refs=4)
                    yield f"\n\n{whitelist_refs}"
                
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
