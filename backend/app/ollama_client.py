# from app.llm_client import LLMClientBase
# import ollama
# from typing import Union, List, Dict, Any
# from PIL.Image import Image as PILImage
# from app.image_utils import image_to_base64

# class OllamaClient:
#     def __init__(self, host="http://localhost:11434"):
#         """Inicializa el cliente de Ollama"""
#         self.client = ollama.Client(host=host) 
#         self.message_history = []

#     def list_models(self) -> List[str]:
#         """Lista todos los modelos disponibles"""
#         try:
#             models_running = self.client.list()['models']
#             available_models = [model["model"] for model in models_running]
#             return available_models
#         except Exception as e:
#             print(f"Error listing models: {e}")
#             return []

#     def chat(self, model_name: str, prompt: str, system_message: str = None) -> str:
#         """Envía un mensaje al modelo y obtiene la respuesta"""
#         messages = []
        
#         if system_message:
#             messages.append({"role": "system", "content": system_message})
        
#         messages.append({"role": "user", "content": prompt})
        
#         response = self.client.chat(
#             model=model_name,
#             messages=messages
#         )
        
#         return response["message"]["content"]

#     def generate_response(self, model_name: str, prompt: Union[str, List[Union[str, PILImage]]]) -> str:
#         """Versión más avanzada que soporta texto e imágenes"""
#         if isinstance(prompt, str):
#             messages = [{"role": "user", "content": prompt}]
#         else:
#             messages = [{
#                 "role": "user",
#                 "content": "".join([p for p in prompt if isinstance(p, str)]),
#                 "images": [image_to_base64(img) for img in prompt if isinstance(img, PILImage)]
#             }]
        
#         response = self.client.chat(
#             model=model_name,
#             messages=messages
#         )
#         return response["message"]["content"]


# if __name__ == "__main__":
#     ollama_client = OllamaClient(model_name="llama2:latest")
#     list_models = OllamaClient.list_models()
#     print(list_models)
    
#     # response = ollama_client.generate_response(prompt="What is Large language Models?")
#     # print(response)

