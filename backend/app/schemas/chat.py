from pydantic import BaseModel
from typing import List, Optional

class ChatMessage(BaseModel):
    role: str
    content: str
    
class ChatRequest(BaseModel):
    question: str
    context: str
    history: Optional[List[ChatMessage]] = []

class DogInfoResponse(BaseModel):
    found: bool
    breed: Optional[str] = None
    temperament: Optional[str] = None
    life_span: Optional[str] = None
    height_metric: Optional[str] = None
    weight_metric: Optional[str] = None
    bred_for: Optional[str] = None
    breed_group: Optional[str] = None
    origin: Optional[str] = None
    message: Optional[str] = None
