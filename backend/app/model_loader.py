from app.ollama_client import OllamaClient
import os

_ollama_client = None

def get_ollama_client():
    """Obtiene o crea el cliente Ollama (singleton)"""
    global _ollama_client
    
    if _ollama_client is None:
        ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434" ) ##"http://ollama:11434"
        _ollama_client = OllamaClient(host=ollama_host)
    
    return _ollama_client






# import os
# import torch
# from transformers import AutoModelForCausalLM, AutoTokenizer
# from app.ollama_client import OllamaClient
# import os

# ### ✅ Configuración del modelo
# MODEL_REPO = os.getenv("MODEL_REPO", "fcp2207/Modelo_Phi2_fusionado")  
# CACHE_DIR = os.getenv("HF_HOME", "/app/cache")  
# os.makedirs(CACHE_DIR, exist_ok=True)

# ✅ Definir variable global para almacenar el modelo y tokenizer
# _model = None
# _tokenizer = None
# _device = None

# def load_model():
#     """Carga el modelo una sola vez y lo reutiliza"""
#     global _model, _tokenizer, _device
# ######Esto es para prueebas en local
#     # system_instruction = ("Eres un experto en motores electricos con 25 años de experiencia y todas tus respuestas son en español")
    
#     # _model = OllamaClient(model_name='mistral:latest',
#     #                       system_instruction=system_instruction)

# ######Esto es para despliegue en docker
#     # system_instruction = ("Eres un experto en motores electricos con 25 años de experiencia y todas tus respuestas son en español")
#     ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")  # Usa la variable de entorno o localhost por defecto
#     _model = OllamaClient(model_name='mistral:latest',
#                         #   system_instruction=system_instruction,
#                           host=ollama_host)

#     return _model, _tokenizer, _device
# # Variables globales para singleton
# _ollama_client = None


# def load_model():
#     """Inicializa el cliente de Ollama sin modelo específico"""
#     global _ollama_client
    
#     if _ollama_client is None:
#         ollama_host = os.getenv("OLLAMA_HOST", "http://ollama:11434")
#         _ollama_client = OllamaClient(model_name=None, host=ollama_host)
    
#     return _ollama_client, None, None  # Mantenemos la misma interfaz

# def get_ollama_client():
#     """Helper para acceso directo al cliente"""
#     return load_model()[0]

# if __name__ == "__main__":
#     #  ollama_client = OllamaClient(model_name='mistral:latest')
#     list_models = OllamaClient.list_models()
#     print(list_models)

