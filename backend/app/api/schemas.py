from pydantic import BaseModel

class InputData(BaseModel):
    """
    Esquema de datos para la entrada de la predicción del chatbot.
    """
    input_text: str
    model: str
    temperature: float
    top_p: float
    top_k: int
    max_tokens: int