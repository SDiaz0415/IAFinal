import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
import os

# Importar las rutas de la API
from app.api.routes import router as api_router
from app.core.config import settings

app = FastAPI(
    debug=settings.DEBUG,
    title="Chatbot de Motores API",
    description="API optimizada para chatbot con RAG y extracción de datos de motores.",
    version="1.0.0" # Puedes ajustar la versión
)

# Incluir las rutas de la API
app.include_router(api_router)

@app.get("/")
def home():
    """Endpoint de bienvenida para verificar que la API está funcionando."""
    return {"message": "API ejecutándose 🚀. Visita /docs para la documentación de la API."}

if __name__ == "__main__":
    # Asegurarse de que la carpeta temp_pdfs exista
    # os.makedirs(settings.TEMP_PDFS_DIR, exist_ok=True)
    uvicorn.run(app, host="0.0.0.0", port=8000)