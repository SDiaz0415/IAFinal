# Usa Python 3.11 como base
FROM python:3.11

# Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Copia solo los archivos necesarios para instalar dependencias
COPY pyproject.toml uv.lock /app/

# Instala UV
RUN pip install uv

# Crea el entorno virtual y sincroniza dependencias
RUN uv venv && uv pip install -e . && uv sync

# Copia el resto del código (incluyendo todas las carpetas necesarias)
COPY . /app

# Expone el puerto del backend
EXPOSE 8080

# Comando para correr el backend con Uvicorn
CMD ["uv", "run", "uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8080"]
