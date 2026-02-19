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
    "enfermedad", "enfermedad", "dolencia", "patología", "condición médica",
    "infección", "infecciones", "bacteriana", "viral", "fungal",
    "medicamento", "medicina", "antibiótico", "antinflamatorio", "vacuna",
    "dosis", "posología", "tratamiento", "terapeútica", "terapia",
    "diabetes", "epilepsia", "cáncer", "tumor", "displasia",
    "artritis", "artrósis", "artrosis", "degeneración discal",
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
        "NO uses markdown: sin **, ###, listas con viñetas (a menos que sea imprescindible). "
        "Mantén respuestas cortas y directas."
    )
    
    if context and context.strip():
        base_prompt += f"\n\nINFORMACIÓN DEL PERRO: {context}"
    
    if intent == "medical":
        base_prompt += (
            "\n\n=== MODO MÉDICO VETERINARIO ===\n"
            "OBLIGATORIO:\n"
            "1) Solo responde si puedes JUSTIFICAR con fuentes OFICIALES de esta lista:\n"
            "   - AVMA (American Veterinary Medical Association)\n"
            "   - RVC (Royal Veterinary College)\n"
            "   - Cornell University College of Veterinary Medicine\n"
            "   - MSD Vet Manual\n"
            "   - ASPCA\n"
            "   - AAHA (American Animal Hospital Association)\n"
            "2) NO INVENTES información ni medicamentos.\n"
            "3) PROHIBIDO: dar dosis exactas de medicamentos o pautas farmacológicas.\n"
            "4) Si NO puedes confirmarlo con esas fuentes, di: "
            "'No puedo confirmarlo con fuentes oficiales. Consulta a un veterinario veterinario.'\n"
            "5) Termina SIEMPRE con 'Fuentes (para contrastar):' + 3-6 URLs de la whitelist.\n"
            "6) Si hay signos de urgencia (convulsiones, respiración dificultosa, colapso, "
            "sangrado abundante, intoxicación aguda, golpe de calor), advierte urgencias veterinarias."
        )
    
    elif intent == "training":
        base_prompt += (
            "\n\n=== MODO ADIESTRAMIENTO Y COMPORTAMIENTO ===\n"
            "OBLIGATORIO:\n"
            "1) Solo responde si puedes JUSTIFICAR con fuentes OFICIALES de esta lista:\n"
            "   - AVSAB (American Veterinary Society of Animal Behavior)\n"
            "   - Dogs Trust (Dog behavior, welfare)\n"
            "   - RSPCA (Royal Society for Prevention of Cruelty to Animals)\n"
            "   - IAABC (International Association of Animal Behavior Consultants)\n"
            "   - AKC (American Kennel Club)\n"
            "2) NO INVENTES técnicas ni remedios.\n"
            "3) PROHIBIDO: recomendar castigo físico o métodos aversivos sin justificación científica.\n"
            "4) Si NO puedes confirmarlo, di: "
            "'No puedo confirmarlo con fuentes oficiales. Consulta a un educador certificado.'\n"
            "5) Termina SIEMPRE con 'Fuentes (para contrastar):' + 3-6 URLs de la whitelist.\n"
            "6) Enfatiza técnicas basadas en refuerzo positivo."
        )
    
    else:  # general
        base_prompt += (
            "\n\nSolo responde preguntas sobre perros: razas, cuidados, temperamento, etc. "
            "Si es otro tema, explica que solo ayudas con temas caninos."
        )
    
    return base_prompt


def get_whitelist_references(intent: str, num_refs: int = 4) -> str:
    """
    Retorna referencias de la whitelist según la intención.
    
    Args:
        intent: "medical" | "training" | "general"
        num_refs: Número de referencias a retornar (default 4).
    
    Returns:
        String con URLs formateadas.
    """
    sources = OFFICIAL_SOURCES.get(intent, [])
    selected = sources[:num_refs]
    
    if not selected:
        return ""
    
    return "Fuentes (para contrastar):\n" + "\n".join(f"- {url}" for url in selected)
