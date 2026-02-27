"""
Utilidades para el servicio de chat con Gemini.
Incluye validación de dominio, mensajes amables y construcción de prompts.
"""

import re

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
        "Responde siempre en español o ingles con tono cercano, natural y práctico. "
        "PROHIBIDO USAR MARKDOWN: Nunca uses **, *, ###, ##, #, ```, ni listas con viñetas (- o *). "
        "En lugar de negritas (**texto**), simplemente escribe el texto normal sin decoración. "
        "En lugar de listas con viñetas, usa frases separadas por puntos o saltos de línea naturales. "
        "USA puntuación natural (como signos de exclamación ¡! y puntos) para sonar amable y humano. "
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


# ===== WHITELIST MODE (Intent Detection & Official Sources) =====

MEDICAL_KEYWORDS = {
    # Síntomas y signos
    "vómito", "vómitos", "vomita", "vomitar", "diarrea", "diarreas", "estreñimiento",
    "fiebre", "tos", "estornudo", "secreción nasal", "flujo nasal",
    "sangrado", "sangra", "hemorragia", "herida", "lesión", "cojera", "cojea",
    "inflamación", "inflamado", "inflamada", "hinchazón", "hinchado",
    "otitis", "sarna", "picazón", "rasguño", "alergia", "alergias",
    "convulsión", "convulsiones", "espasmo", "temblor", "temblores",
    "dificultad respiratoria", "respiración dificultosa", "jadeo", "asfixia",
    "colapso", "desvanecimiento", "pérdida de conciencia",
    "tóxico", "toxina", "envenenamiento", "intoxicación", "envenenado",
    "golpe de calor", "hipotermia", "insolación",
    "parásito", "parásitos", "pulgas", "garrapatas", "gusanos", "lombriz",
    "pulga", "garrapata",  # formas singulares
    "enfermedad", "enfermedad", "dolencia", "patología", "condición médica",
    "infección", "infecciones", "bacteriana", "viral", "fungal",
    "medicamento", "medicina", "antibiótico", "antinflamatorio", "vacuna",
    "dosis", "posología", "tratamiento", "terapeútica", "terapia",
    "diabetes", "epilepsia", "cáncer", "tumor", "displasia",
    "artritis", "artrósis", "artrosis", "degeneración discal",
    # Piel e irritaciones
    "rasca", "rascarse", "rascado", "rascando", "se rasca",
    "irritación", "irritada", "irritado", "irritar",
    "piel", "pelaje", "dermatitis", "eczema", "eccema",
    "picor", "comezón", "comezon", "prurito",
    "champú", "champu", "baño medicinal",
    # Contexto veterinario
    "veterinario", "veterinaria", "veterinarios", "clínica veterinaria",
    "cita veterinaria", "cita con el veterinario", "consulta veterinaria",
    "clínica", "clinica", "diagnóstico", "diagnostico",
    "cirugía", "cirugia", "operación", "operacion",
    "radiografía", "ecografía", "análisis", "analisis",
    # Inglés
    "vomit", "vomiting", "diarrhea", "diarrheal", "constipation",
    "fever", "cough", "sneeze", "nasal discharge",
    "bleeding", "hemorrhage", "wound", "injury", "lameness",
    "inflammation", "swelling", "inflamed",
    "otitis", "mange", "itching", "scratch", "allergy", "allergic",
    "seizure", "seizures", "convulsion", "tremor", "trembling",
    "respiratory distress", "difficulty breathing", "panting", "asphyxia",
    "collapse", "fainting", "loss of consciousness",
    "toxic", "toxin", "poison", "poisoning", "toxicity",
    "heat stroke", "hypothermia", "heat exhaustion",
    "parasite", "parasites", "flea", "tick", "worm", "helminth",
    "disease", "illness", "condition", "pathology", "medical condition",
    "infection", "infections", "bacterial", "viral", "fungal",
    "medication", "medicine", "antibiotic", "anti-inflammatory", "vaccine",
    "dosage", "dose", "treatment", "therapy", "therapeutic",
    "diabetes", "epilepsy", "cancer", "tumor", "dysplasia",
    "arthritis", "arthritis", "arthritis", "disc degeneration",
    "skin", "rash", "irritation", "itchy", "scratching", "vet",
}

TRAINING_KEYWORDS = {
    # Adiestramiento y comportamiento
    "adiestrar", "adiestramientos", "adiestramiento", "entrenar", "entrenamiento",
    "obediencia", "obediente", "comando", "comandos", "orden", "órdenes",
    "ladrar", "ladrido", "ladridos", "ladra", "ladran", "ladrador",
    "morder", "mordida", "muerde", "muerden", "agresión", "agresividad",
    "tirar de correa", "tire de", "tira de", "jalón", "estira",
    "saltar", "salta", "saltan", "saltador", "salta sobre",
    "ansiedad", "ansioso", "ansiosa", "separación", "angustia",
    "miedo", "asustado", "fobia", "fobias", "temeroso",
    "agresivo", "agresiva", "agresivos", "agresivas", "agresividad",
    "dominancia", "dominante", "dominancia", "jerarquía",
    "socialización", "socializar", "socializado", "unsocial",
    "refuerzo", "refuerzo positivo", "estímulo", "recompensa", "castigo",
    "conducta", "comportamiento", "comportamientos", "hábito", "costumbre",
    "destrucción", "destructivo", "destructiva", "destruye", "destruyen",
    "masticar", "mastica", "mastican", "mal hábito",
    "tirar objetos", "tira", "destroza", "daño",
    "excitación", "excitado", "excitada", "hiperactividad",
    "pasividad", "pasivo", "pasiva", "apatía",
    "reacción", "reacciona", "reaccionan", "respuesta",
    # Inglés
    "train", "training", "teach", "teaching", "obedience", "obedient",
    "command", "commands", "order", "orders",
    "bark", "barking", "barks", "barker",
    "bite", "biting", "bites", "aggression", "aggressive",
    "pull", "pulling", "pulls", "leash pulling", "tugging",
    "jump", "jumps", "jumping", "jumper",
    "anxiety", "anxious", "separation anxiety", "distress",
    "fear", "scared", "phobia", "phobias", "fearful",
    "aggressive", "aggression", "dominance", "dominant",
    "socialization", "socialize", "socialized",
    "reinforcement", "positive reinforcement", "stimulus", "reward", "punishment",
    "behavior", "behaviours", "habit", "conduct",
    "destructive", "destructiveness", "chewing", "destruction",
    "chew", "chews", "destructive chewing",
    "excitement", "excited", "excitable", "hyperactivity",
    "passivity", "passive", "apathy",
    "reaction", "reacts", "responding",
}

MEDICAL_EMERGENCY_KEYWORDS = {
    "convulsión", "convulsiones", "espasmo", "colapso", "desvanecimiento",
    "dificultad respiratoria", "respiración dificultosa", "ahogo", "asfixia",
    "sangrado abundante", "hemorragia", "sangra mucho", "sangrado grave",
    "intoxicación", "envenenamiento", "tóxico agudo", "veneno",
    "golpe de calor", "golpe de calor severo", "insolación grave",
    "pérdida de conciencia", "inconsciente", "inconsciencia",
    "parálisis", "paralizado", "paralizada",
    "trauma", "traumatismo", "accidente grave", "golpe fuerte",
    "seizure", "seizures", "spasm", "collapse", "fainting",
    "respiratory distress", "choking", "asphyxia", "difficulty breathing",
    "heavy bleeding", "hemorrhage", "severe bleeding", "profuse bleeding",
    "poisoning", "toxicity", "acute poisoning", "venom",
    "heat stroke", "severe heat stroke", "heat exhaustion severe",
    "loss of consciousness", "unconscious", "unconsciousness",
    "paralysis", "paralyzed", "paralyze",
    "trauma", "traumatic injury", "severe accident", "major injury",
}

REPORT_KEYWORDS = {
    # Español
    "informe", "reporte", "generar informe", "generar reporte",
    "crear informe", "crear reporte", "hacer informe", "hacer reporte",
    "genera un informe", "genera un reporte", "hazme un informe",
    "hazme un reporte", "quiero un informe", "quiero un reporte",
    "necesito un informe", "necesito un reporte", "preparar informe",
    "preparar reporte", "generar documento", "crear documento",
    "informe veterinario", "informe clínico", "informe de adiestramiento",
    "reporte veterinario", "reporte clínico", "reporte de adiestramiento",
    "resumen clínico", "resumen veterinario", "resumen de la conversación",
    "generar pdf", "crear pdf", "descargar informe", "descargar reporte",
    # Inglés
    "report", "generate report", "create report", "make report",
    "generate a report", "create a report", "clinical report",
    "training report", "veterinary report", "summary report",
    "generate pdf", "create pdf", "download report",
}

OFFICIAL_SOURCES = {
    "medical": [
        "https://www.avma.org/",
        "https://www.rvc.ac.uk/",
        "https://vet.cornell.edu/",
        "https://www.msdvetmanual.com/",
        "https://www.aspca.org/",
        "https://www.aaha.org/",
    ],
    "training": [
        "https://avsab.org/",
        "https://www.dogstrust.org.uk/",
        "https://www.rspca.org.uk/",
        "https://iaabc.org/",
        "https://www.akc.org/",
    ],
}


def detect_intent(question: str, context: str = "") -> str:
    """
    Detecta la intención de la pregunta: medical, training o general.
    
    Args:
        question: La pregunta del usuario.
        context: Contexto del perro (opcional).
    
    Returns:
        "medical" | "training" | "general"
    """
    search_text = (question + " " + context).lower()
    
    # Contar matches con keywords médicas y de adiestramiento
    medical_matches = sum(1 for kw in MEDICAL_KEYWORDS if kw in search_text)
    training_matches = sum(1 for kw in TRAINING_KEYWORDS if kw in search_text)
    
    # Retornar la intención con más matches
    if medical_matches > training_matches and medical_matches > 0:
        return "medical"
    elif training_matches > 0:
        return "training"
    else:
        return "general"


def is_medical_emergency(question: str, context: str = "") -> bool:
    """
    Detecta si la pregunta indica una urgencia médica veterinaria.
    
    Args:
        question: La pregunta del usuario.
        context: Contexto del perro (opcional).
    
    Returns:
        True si hay indicadores de urgencia médica, False en caso contrario.
    """
    search_text = (question + " " + context).lower()
    
    # Buscar keywords de emergencia
    for keyword in MEDICAL_EMERGENCY_KEYWORDS:
        if keyword in search_text:
            return True
    
    return False


def get_emergency_response() -> str:
    """
    Retorna mensaje de urgencia médica.
    
    Returns:
        Mensaje de triage y derivación a urgencias.
    """
    return (
        "Esto parece una urgencia veterinaria. Los signos que describes requieren "
        "atención inmediata de un veterinario. NO esperes: contacta a una clínica "
        "veterinaria de urgencias ahora mismo o llama al servicio de emergencias animal de tu zona. "
        "Mientras llegas, mantén al perro en un lugar tranquilo y seguro. "
        "No intentes medicar sin supervisión veterinaria."
    )


def build_whitelist_system_prompt(intent: str, context: str = "") -> str:
    """
    Construye el system prompt para Gemini con restricciones de whitelist.
    
    Para intents médicos y de adiestramiento, incluye:
    - Obligación de justificar con fuentes oficiales
    - Prohibición de dosis farmacológicas
    - Obligación de incluir URLs de whitelist al final
    
    Args:
        intent: "medical" | "training" | "general"
        context: Contexto del perro (opcional).
    
    Returns:
        System prompt personalizado según intención.
    """
    base_prompt = (
        "Eres un experto en perros amable y servicial. "
        "Responde siempre en español con tono cercano, natural y práctico. "
        "PROHIBIDO USAR MARKDOWN: Nunca uses **, *, ###, ##, #, ```, ni listas con viñetas (- o *). "
        "En lugar de negritas (**texto**), simplemente escribe el texto normal sin decoración. "
        "En lugar de listas con viñetas, usa frases separadas por puntos o saltos de línea naturales. "
        "Ejemplo INCORRECTO: '**Champú de avena** para perros' → Ejemplo CORRECTO: 'Champú de avena para perros'. "
        "Ejemplo INCORRECTO: '* Primer punto\n* Segundo punto' → Ejemplo CORRECTO: 'Primer punto. Segundo punto.' "
        "USA puntuación natural (puntos, signos de exclamación ¡!) para ser amable y humano. "
        "Mantén respuestas cortas y directas."
    )
    
    if context and context.strip():
        base_prompt += f"\n\nINFORMACIÓN DEL PERRO: {context}"
    
    sources_medical = (
        "\n\nFUENTES OFICIALES OBLIGATORIAS (SIEMPRE incluir al final de cada respuesta):\n"
        "Estas son las URLs exactas que DEBES referenciar. Copia las URLs tal cual:\n"
        "   - AVMA: https://www.avma.org/\n"
        "   - RVC: https://www.rvc.ac.uk/\n"
        "   - Cornell Vet: https://vet.cornell.edu/\n"
        "   - MSD Vet Manual: https://www.msdvetmanual.com/\n"
        "   - ASPCA: https://www.aspca.org/\n"
        "   - AAHA: https://www.aaha.org/\n"
    )
    
    sources_training = (
        "\n\nFUENTES OFICIALES OBLIGATORIAS (SIEMPRE incluir al final de cada respuesta):\n"
        "Estas son las URLs exactas que DEBES referenciar. Copia las URLs tal cual:\n"
        "   - AVSAB: https://avsab.org/\n"
        "   - Dogs Trust: https://www.dogstrust.org.uk/\n"
        "   - RSPCA: https://www.rspca.org.uk/\n"
        "   - IAABC: https://iaabc.org/\n"
        "   - AKC: https://www.akc.org/\n"
    )
    
    if intent == "medical":
        base_prompt += (
            "\n\n=== MODO MÉDICO VETERINARIO ===\n"
            "OBLIGATORIO:\n"
            "1) Basa tus respuestas en información verificable de estas fuentes oficiales:\n"
            "   AVMA, RVC, Cornell Vet, MSD Vet Manual, ASPCA, AAHA.\n"
            "2) NO INVENTES información ni medicamentos.\n"
            "3) PROHIBIDO: dar dosis exactas de medicamentos o pautas farmacológicas.\n"
            "4) Si NO puedes confirmarlo con esas fuentes, di: "
            "'No puedo confirmarlo con fuentes oficiales. Consulta a tu veterinario.'\n"
            "5) SIEMPRE termina tu respuesta con un bloque de fuentes. Esto es OBLIGATORIO, no opcional.\n"
            "   El bloque DEBE aparecer al final de CADA respuesta, sin excepción.\n"
            "   Formato EXACTO que debes seguir (sin markdown, sin **, sin viñetas):\n\n"
            "   Fuentes (para contrastar):\n"
            "   AVMA - https://www.avma.org/\n"
            "   MSD Vet Manual - https://www.msdvetmanual.com/\n"
            "   ASPCA - https://www.aspca.org/\n\n"
            "   Selecciona entre 2 y 4 fuentes relevantes de la lista según el tema.\n"
            "6) Si hay signos de urgencia (convulsiones, respiración dificultosa, colapso, "
            "sangrado abundante, intoxicación aguda, golpe de calor), advierte urgencias veterinarias."
        )
        base_prompt += sources_medical
    
    elif intent == "training":
        base_prompt += (
            "\n\n=== MODO ADIESTRAMIENTO Y COMPORTAMIENTO ===\n"
            "OBLIGATORIO:\n"
            "1) Basa tus respuestas en información verificable de estas fuentes oficiales:\n"
            "   AVSAB, Dogs Trust, RSPCA, IAABC, AKC.\n"
            "2) NO INVENTES técnicas ni remedios.\n"
            "3) PROHIBIDO: recomendar castigo físico o métodos aversivos sin justificación científica.\n"
            "4) Si NO puedes confirmarlo, di: "
            "'No puedo confirmarlo con fuentes oficiales. Consulta a un educador certificado.'\n"
            "5) SIEMPRE termina tu respuesta con un bloque de fuentes. Esto es OBLIGATORIO, no opcional.\n"
            "   El bloque DEBE aparecer al final de CADA respuesta, sin excepción.\n"
            "   Formato EXACTO que debes seguir (sin markdown, sin **, sin viñetas):\n\n"
            "   Fuentes (para contrastar):\n"
            "   AVSAB - https://avsab.org/\n"
            "   AKC - https://www.akc.org/\n"
            "   Dogs Trust - https://www.dogstrust.org.uk/\n\n"
            "   Selecciona entre 2 y 4 fuentes relevantes de la lista según el tema.\n"
            "6) Enfatiza técnicas basadas en refuerzo positivo."
        )
        base_prompt += sources_training
    
    else:  # general
        base_prompt += (
            "\n\nSolo responde preguntas sobre perros: razas, cuidados, temperamento, etc. "
            "Si es otro tema, explica que solo ayudas con temas caninos."
        )
    
    return base_prompt


def strip_markdown(text: str) -> str:
    """
    Post-procesa el texto para eliminar restos de markdown que Gemini pueda devolver.
    
    Elimina: **, *, ###, ##, #, ```, viñetas con - o *.
    Preserva URLs y líneas que contienen fuentes/referencias.
    
    Args:
        text: El texto a limpiar.
    
    Returns:
        Texto limpio sin markdown.
    """
    if not text:
        return text
    
    # Eliminar bloques de código ```...```
    text = re.sub(r'```[\s\S]*?```', '', text)
    # Eliminar code inline `texto`
    text = re.sub(r'`([^`]+)`', r'\1', text)
    # Eliminar headers ### ## #
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    # Eliminar bold **texto** o __texto__
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    # Eliminar italic *texto* o _texto_ (cuidado con no romper URLs)
    text = re.sub(r'(?<!\w)\*([^*]+)\*(?!\w)', r'\1', text)
    
    # Eliminar viñetas al inicio de línea SOLO si NO contienen URLs
    # Preservar líneas tipo "- AVMA: https://..." o "- https://..."
    cleaned_lines = []
    for line in text.split('\n'):
        if re.match(r'^\s*[-*]\s+', line) and not re.search(r'https?://', line):
            # Es una viñeta sin URL -> quitar el marcador
            line = re.sub(r'^\s*[-*]\s+', '', line)
        cleaned_lines.append(line)
    text = '\n'.join(cleaned_lines)
    
    # Limpiar líneas vacías múltiples
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()


def detect_report_intent(question: str, context: str = "") -> bool:
    """
    Detecta si el usuario está pidiendo generar un informe/reporte desde el chat.
    
    Args:
        question: La pregunta del usuario.
        context: Contexto del perro (opcional).
    
    Returns:
        True si el usuario quiere generar un informe, False en caso contrario.
    """
    search_text = (question).lower()
    
    for keyword in REPORT_KEYWORDS:
        if keyword in search_text:
            return True
    
    return False


def detect_report_type_from_conversation(history: list) -> str:
    """
    Analiza el historial de la conversación para determinar si el informe
    debe ser veterinario o de adiestramiento.
    
    IMPORTANTE: Solo analiza mensajes del USUARIO para evitar que palabras
    del asistente (ej: el mensaje de bienvenida menciona "adiestramiento")
    sesguen la clasificación.
    
    Args:
        history: Lista de mensajes del chat [{role, content}, ...]
    
    Returns:
        "veterinario" | "adiestramiento"
    """
    # Solo analizar mensajes del usuario, no del asistente
    user_text = " ".join(
        (msg.get("content", "") if isinstance(msg, dict) else getattr(msg, 'content', ''))
        for msg in history
        if (msg.get("role", "") if isinstance(msg, dict) else getattr(msg, 'role', '')) == "user"
    ).lower()
    
    medical_score = sum(1 for kw in MEDICAL_KEYWORDS if kw in user_text)
    training_score = sum(1 for kw in TRAINING_KEYWORDS if kw in user_text)
    
    if training_score > medical_score:
        return "adiestramiento"
    return "veterinario"


# Preguntas que el chatbot hará para recopilar datos del perro antes de generar el informe
REPORT_DOG_QUESTIONS = {
    "veterinario": [
        {"field": "nombre", "question": "¿Cómo se llama tu perro?"},
        {"field": "raza", "question": "¿De qué raza es?"},
        {"field": "edad", "question": "¿Qué edad tiene?"},
        {"field": "peso", "question": "¿Cuánto pesa aproximadamente (en kg)?"},
        {"field": "genero", "question": "¿Es macho o hembra?"},
    ],
    "adiestramiento": [
        {"field": "nombre", "question": "¿Cómo se llama tu perro?"},
        {"field": "raza", "question": "¿De qué raza es?"},
        {"field": "edad", "question": "¿Qué edad tiene?"},
        {"field": "peso", "question": "¿Cuánto pesa aproximadamente (en kg)?"},
    ],
}


def extract_known_dog_info(context: str, history: list) -> dict:
    """
    Extrae datos del perro que ya se conocen del contexto (predicción de raza)
    y del historial de la conversación.
    
    IMPORTANTE: Solo analiza mensajes del USUARIO (role='user') para evitar
    extraer datos inventados por el asistente (ej: edades mencionadas en consejos).
    
    Args:
        context: Contexto del perro (ej: "Raza: Airedale Terrier\nTemperamento: ...")
        history: Lista de mensajes del chat [{role, content}, ...]
    
    Returns:
        Dict con campos conocidos: {nombre, raza, edad, peso, genero}
    """
    known = {}
    
    # 1. Extraer raza del contexto (viene de la predicción / TheDogAPI)
    if context:
        raza_match = re.search(r'raza:\s*(.+?)(?:\n|$)', context, re.IGNORECASE)
        if raza_match:
            known["raza"] = raza_match.group(1).strip()
    
    # 2. Solo analizar mensajes del USUARIO para extraer datos
    #    NUNCA analizar mensajes del asistente (pueden mencionar edades, pesos, etc. genéricamente)
    user_text = " ".join(
        (msg.get("content", "") if isinstance(msg, dict) else getattr(msg, 'content', ''))
        for msg in history
        if (msg.get("role", "") if isinstance(msg, dict) else getattr(msg, 'role', '')) == "user"
    )
    user_lower = user_text.lower()
    
    # Intentar extraer nombre del perro - SOLO patrones explícitos
    # Debe ser "se llama X" o "su nombre es X", NO "mi perro tiene..." 
    nombre_patterns = [
        r'se llama\s+(\w+)',
        r'su nombre es\s+(\w+)',
        r'(?:tengo un|tengo una)\s+\w+\s+(?:llamad[oa]|que se llama)\s+(\w+)',
    ]
    # Palabras comunes que NO son nombres de perro
    stop_words = {"el", "la", "un", "una", "mi", "su", "tiene", "es", "muy",
                  "pero", "que", "como", "con", "por", "para", "del", "los", "las",
                  "perro", "perra", "cachorro", "cachorra"}
    for pattern in nombre_patterns:
        match = re.search(pattern, user_lower)
        if match and "nombre" not in known:
            nombre = match.group(1).strip().capitalize()
            if (nombre and len(nombre) > 1 
                and nombre.lower() not in DOG_DOMAIN_KEYWORDS 
                and nombre.lower() not in stop_words):
                known["nombre"] = nombre
    
    # Intentar extraer edad - solo de texto del usuario
    edad_patterns = [
        r'tiene\s+(\d+\s*(?:años|año|meses|mes))',
        r'(?:de|con)\s+(\d+\s*(?:años|año|meses|mes))',
        r'edad[:\s]+(\d+\s*(?:años|año|meses|mes))',
    ]
    for pattern in edad_patterns:
        match = re.search(pattern, user_lower)
        if match and "edad" not in known:
            known["edad"] = match.group(1).strip()
    
    # Intentar extraer peso - solo de texto del usuario
    peso_patterns = [
        r'(\d+[\.,]?\d*)\s*(?:kg|kilos|kilogramos)',
        r'pesa\s+(\d+[\.,]?\d*)\s*(?:kg|kilos|kilogramos)?',
    ]
    for pattern in peso_patterns:
        match = re.search(pattern, user_lower)
        if match and "peso" not in known:
            known["peso"] = match.group(1).strip() + " kg"
    
    # Intentar extraer género - solo de texto del usuario
    genero_patterns = [
        r'(?:es\s+)?\b(macho|hembra)\b',
        r'(?:es\s+)?\b(male|female)\b',
    ]
    for pattern in genero_patterns:
        match = re.search(pattern, user_lower)
        if match and "genero" not in known:
            g = match.group(1)
            known["genero"] = "Macho" if g in ("macho", "male") else "Hembra"
    
    return known
