from abc import ABC, abstractmethod
from typing import List, Union, Dict, Any
import ollama
from PIL.Image import Image as PILImage #

from app.core.utils import image_to_base64 #
from app.core.config import settings

# Singleton para el cliente Ollama
_ollama_client_instance = None

class LLMClientBase(ABC): #
    """
    Clase base abstracta para clientes de Large Language Models (LLM).
    Define la interfaz mínima que cualquier cliente LLM debe implementar.
    """
    @abstractmethod
    def list_models(self) -> List[str]: #
        """Lista los modelos disponibles del proveedor LLM."""
        pass
    
    @abstractmethod
    def generate_response(self, model_name: str, prompt: Union[str, List[Union[str, PILImage]]], system_message: str = None) -> Dict[str, Any]:
        """Genera una respuesta del LLM dado un modelo y un prompt."""
        pass

class OllamaClient(LLMClientBase): #
    """
    Cliente concreto para interactuar con el servicio de Ollama.
    """
    def __init__(self, host: str = settings.OLLAMA_HOST): #
        """Inicializa el cliente de Ollama."""
        self.client = ollama.Client(host=host) #
        self.message_history = [] # # Puedes decidir si esta historia es a nivel de cliente o de sesión

    def list_models(self) -> List[str]: #
        """Lista todos los modelos disponibles en el servidor de Ollama."""
        try:
            models_running = self.client.list()['models'] #
            available_models = [model["model"] for model in models_running] #
            return available_models
        except Exception as e:
            print(f"Error listing Ollama models: {e}")
            # Considera elevar una excepción más específica, e.g., OllamaConnectionError
            return []

    def generate_response(self, model_name: str, prompt: Union[str, List[Union[str, PILImage]]], system_message: str = None) -> Dict[str, Any]:
        """
        Envía un mensaje al modelo de Ollama y obtiene la respuesta.
        Soporta prompts de texto e imágenes (multimodal).
        Retorna la respuesta completa del cliente Ollama, no solo el contenido.
        """
        messages = []
        
        if system_message:
            messages.append({"role": "system", "content": system_message})
        
        if isinstance(prompt, str):
            messages.append({"role": "user", "content": prompt}) #
        else: # Asume que es una lista de texto e imágenes
            user_content = "".join([p for p in prompt if isinstance(p, str)]) #
            images_base64 = [image_to_base64(img) for img in prompt if isinstance(img, PILImage)] #
            messages.append({
                "role": "user",
                "content": user_content,
                "images": images_base64
            })
        
        # Usamos self.client.chat para consistencia con LangChain
        response = self.client.chat( #
            model=model_name,
            messages=messages
        )
        return response

def get_ollama_client() -> OllamaClient: #
    """
    Obtiene o crea el cliente Ollama (singleton).
    Asegura que solo haya una instancia del cliente Ollama.
    """
    global _ollama_client_instance
    
    if _ollama_client_instance is None:
        _ollama_client_instance = OllamaClient() #
    
    return _ollama_client_instance

if __name__ == "__main__":
    # Ejemplo de uso (para pruebas locales)
    ollama_client = get_ollama_client()
    print("Modelos disponibles:", ollama_client.list_models())

    # Asegúrate de tener un modelo descargado en Ollama (ej. 'llama2', 'mistral')
    # response = ollama_client.generate_response(model_name="llama2", prompt="Hola, ¿cómo estás?")
    # print("Respuesta:", response['message']['content'])