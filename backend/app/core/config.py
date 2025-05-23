import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Configuración de la aplicación cargada desde variables de entorno.
    """
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    DEBUG: bool
    OLLAMA_HOST: str
    TEMP_PDFS_DIR: str = 'temp_pdfs'
    SAVE_RAW_DOCS_DIR: str = 'app/embeddings/raw_documents'
    GET_RAW_DOCS_DIR: str = 'app\\embeddings\\raw_documents'
    LANGSMITH_TRACING: str
    LANGSMITH_API_KEY: str
    CONVERT_API_HTTP: str
    CONVERT_API_SECRET: str
    MILVUS_END_POINT: str
    MILVUS_API: str

    # DEBUG: bool = True
    # OLLAMA_HOST: str = "http://localhost:11434"
    # TEMP_PDFS_DIR: str = "temp_pdfs"
    # DATA_RAW_DOCS_DIR: str = "app/embeddings/raw_documents"
    # # DATA_TRANSFORMED_DIR: str = "data/transformed_data"

    # Puedes añadir más configuraciones aquí, como umbrales para embeddings
    # EMBEDDING_THRESHOLD: float = 0.5

settings = Settings()