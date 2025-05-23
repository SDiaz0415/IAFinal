class CustomException(Exception):
    """Excepción base para errores personalizados en la aplicación."""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class OllamaConnectionError(CustomException):
    """Excepción para errores de conexión con Ollama."""
    def __init__(self, message: str = "No se pudo conectar con el servicio de Ollama.", status_code: int = 503):
        super().__init__(message, status_code)

class PDFProcessingError(CustomException):
    """Excepción para errores durante el procesamiento de PDFs."""
    def __init__(self, message: str = "Error al procesar el archivo PDF.", status_code: int = 400):
        super().__init__(message, status_code)

# Puedes añadir más excepciones personalizadas según tus necesidades