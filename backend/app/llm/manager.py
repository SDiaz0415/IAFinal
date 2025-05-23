from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.llm.prompts import get_system_prompt

class LLMManager:
    """
    Clase para gestionar la creación de cadenas LangChain y la orquestación de LLMs.
    """
    def __init__(self):
        self.system_prompt = get_system_prompt()

    def create_rag_chain(self, model: str, temperature: float, max_tokens: int, top_p: float, top_k: int):
        """
        Crea y retorna una cadena LangChain configurada para RAG.
        Adaptado de tu `create_chain` en `api.py`.
        """
        llm = ChatOllama(
            model=model,
            temperature=temperature,
            num_predict=max_tokens,
            system=self.system_prompt,
            disable_streaming=False,
            top_k=top_k,
            top_p=top_p
        )
        
        prompt_template = ChatPromptTemplate([
            ("human", 
             """Utiliza la siguiente información de referencia para responder:
             [Contexto relevante]
             {context}

             [Pregunta del usuario]
             {input}
             """)
        ])
        
        # Retorna el LLM y el prompt template por separado para que el router pueda invocar 'ainvoke'
        return llm, prompt_template

    # TODO: Podrías añadir otros métodos aquí para:
    # - manejar diferentes tipos de cadenas (ej. para chat sin RAG)
    # - seleccionar dinámicamente el LLM (si tienes varios proveedores)
    # - manejar el historial de conversación si no es gestionado por LangChain directamente