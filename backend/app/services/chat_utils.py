"""
Utilidades para el servicio de chat con Gemini.
Incluye validación de dominio, mensajes amables y construcción de prompts.
"""

DOG_DOMAIN_KEYWORDS = {
    # Español
    "perro", "perros", "cachorro", "cachorros", "raza", "razas",
    "pienso", "comida", "croquetas", "alimentacion", "alimentación",
    "vacuna", "vacunas", "veterinario", "vet", "salud", "enfermedad",
    "enfermedad", "síntoma", "problemas", "herida", "parásito",
    "adiestrar", "adiestramientos", "adiestramiento", "entrenamiento",
    "paseo", "paseos", "ejercicio", "juego", "comportamiento",
    "temperamento", "carácter", "socialización", "juguete",
    "peso", "altura", "tamaño", "edad", "años",
    "ladrar", "ladrido", "morder", "mordida", "agresividad",
    "ansiedad", "stress", "miedo", "fobia", "angustia",
    "oreja", "orejas", "cola", "pata", "patas", "piel", "pelaje",
    "baño", "aseo", "cepillo", "peluquería", "corte",
    "celo", "esterilización", "castración", "reproducción",
    "criador", "crianza", "línea", "pedigrí", "pedigree",
    "origen", "historia", "grupo", "estándar",
    "husky", "golde", "golden", "labrador", "pastor", "bulldog",
    "poodle", "caniche", "terrier", "schnauzer", "dachshund",
    "chihuahua", "bulldog", "doberman", "rottweiler", "pitbull",
    "beagle", "cocker", "springer", "pointer", "boxer", "dálmata",
    "shiba", "akita", "corgi", "bóxer",
    # Inglés
    "dog", "dogs", "puppy", "puppies", "breed", "breeds",
    "food", "kibble", "diet", "nutrition",
    "vaccination", "vaccine", "vet", "health", "illness",
    "disease", "symptom", "injury", "parasite",
    "training", "train", "obedience", "command",
    "walk", "walks", "exercise", "play", "behavior",
    "temperament", "socialization", "toy", "toys",
    "weight", "height", "size", "age", "years",
    "bark", "barking", "bite", "biting", "aggression",
    "anxiety", "stress", "fear", "phobia",
    "ear", "ears", "tail", "paw", "paws", "coat", "fur",
    "bath", "grooming", "brush", "trim", "haircut",
    "heat", "spay", "neuter", "breeding", "reproduction",
    "breeder", "breeding", "lineage", "pedigree",
    "origin", "history", "group", "standard",
}

def is_dog_domain(question: str, context: str = "") -> bool:
    """
    Valida si una pregunta está relacionada con perros.
    
    Heurística simple:
    - Si la pregunta contiene al menos una keyword sobre perros, es on-domain.
    - Si no hay keywords pero hay contexto que mencione perro, es on-domain.
    - Si no hay keywords ni contexto relevante, es out-of-domain.
    
    Args:
        question: La pregunta del usuario.
        context: Contexto del perro (opcional, ej: "Tengo un Golden Retriever").
    
    Returns:
        True si la pregunta está en el dominio de perros, False en caso contrario.
    """
    search_text = (question + " " + context).lower()
    
    # Buscar cualquier keyword en el texto
    for keyword in DOG_DOMAIN_KEYWORDS:
        if keyword in search_text:
            return True
    
    return False


def get_rate_limit_message() -> str:
    """
    Mensaje amable para cuando se alcanza el límite de tasa (429).
    
    Returns:
        Mensaje de error amable.
    """
    return (
        "Ahora mismo estoy saturado. Prueba en 30–60 segundos o reformula "
        "la pregunta en una sola frase. Gracias por tu paciencia."
    )


def get_out_of_domain_message() -> str:
    """
    Mensaje de redirección cuando la pregunta no está relacionada con perros.
    
    Returns:
        Mensaje de redirección.
    """
    return (
        "Puedo ayudarte con cosas sobre perros: razas, cuidados, salud, "
        "entrenamiento, comportamiento y más. ¿Qué necesitas saber de tu perro?"
    )


def build_system_prompt(context: str = "") -> str:
    """
    Construye el prompt del sistema para Gemini con instrucciones de estilo.
    
    Instrucciones:
    - Responde en español, tono cercano y natural.
    - Sin markdown excesivo.
    - Respuestas cortas y prácticas.
    - Si falta información, hacer 1 pregunta.
    - Solo responder temas de perros.
    
    Args:
        context: Contexto del perro (ej: "Tengo un Golden Retriever de 3 años").
    
    Returns:
        Prompt del sistema para Gemini.
    """
    system_prompt = (
        "Eres un experto en perros amable y servicial. "
        "Responde siempre en español con tono cercano, natural y práctico. "
        "NO uses markdown: sin **, ###, listas con viñetas (a menos que sea imprescindible). "
        "Mantén respuestas cortas y directas. "
        "Si te falta información importante, haz una sola pregunta aclaratoria. "
        "Solo responde preguntas sobre perros: razas, cuidados, salud, alimentación, "
        "entrenamiento, comportamiento, temperamento, etc. "
        "Si es otro tema fuera de perros, explica que solo puedes ayudar con temas caninos."
    )
    
    if context and context.strip():
        system_prompt += (
            f"\n\nINFORMACIÓN DEL PERRO DEL USUARIO: {context} "
            "Usa este contexto para personalizar tus respuestas."
        )
    
    return system_prompt


def is_rate_limit_error(error: Exception) -> bool:
    """
    Detecta si una excepción es un error de rate limit (429).
    
    Busca indicadores:
    - google.api_core.exceptions.ResourceExhausted
    - google.api_core.exceptions.TooManyRequests
    - El mensaje contiene "429" o "RESOURCE_EXHAUSTED"
    
    Args:
        error: La excepción a verificar.
    
    Returns:
        True si es un rate limit error, False en caso contrario.
    """
    error_str = str(error).lower()
    error_type = type(error).__name__.lower()
    
    # Buscar indicadores de rate limit
    if any(indicator in error_str for indicator in ["429", "resource_exhausted", "too many requests", "quota"]):
        return True
    
    if any(indicator in error_type for indicator in ["resourceexhausted", "toomanyrequests"]):
        return True
    
    return False
