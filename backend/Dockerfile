# Usa Python 3.11 como base
FROM python:3.11

# Establece variables de entorno para una mejor gestión de dependencias y optimización
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Instala UV
RUN pip install uv

# Copia solo los archivos necesarios para instalar dependencias
# pyproject.toml y uv.lock para uv, o requirements.txt para pip
COPY pyproject.toml uv.lock /app/

# Crea el entorno virtual y sincroniza dependencias
# No uses -e . para un despliegue de producción. -e . es para desarrollo de paquetes.
# Simplemente instala las dependencias.
# Asegúrate de que todas las dependencias estén en uv.lock (o pyproject.toml si generas el lock en build)
RUN uv venv --system-site-packages && uv pip install --system-site-packages && uv sync --system-site-packages

# Copia el resto del código de tu aplicación
# Ignorará lo definido en .dockerignore
COPY . /app

# Expone el puerto del backend
EXPOSE 8080

# Comando para correr el backend con Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
