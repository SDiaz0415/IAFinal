from PIL import Image
import base64
from io import BytesIO
from PIL import Image as PILImage #

def image_to_base64(image: PILImage) -> str:
    """
    Convierte una imagen PIL a una cadena base64.
    Útil para modelos multimodal que aceptan imágenes en base64.
    """
    with BytesIO() as buffer:
        image.save(buffer, format=image.format or "PNG") #
        return base64.b64encode(buffer.getvalue()).decode("utf-8") #

# Puedes añadir otras funciones de utilidad aquí