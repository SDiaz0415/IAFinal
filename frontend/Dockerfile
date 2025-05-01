# Usa Python 3.11 como base
FROM python:3.11

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia solo los archivos necesarios para instalar dependencias
COPY pyproject.toml uv.lock /app/

# Instala UV
RUN pip install uv

# Crea el entorno virtual y sincroniza dependencias
RUN uv venv && uv pip install -e . && uv sync

# Copia el resto del código del frontend
COPY . /app

# Expone el puerto en el que se ejecuta Chainlit
EXPOSE 8000

# Comando para iniciar Chainlit
CMD ["uv", "run", "streamlit", "run", "main.py", "--host", "0.0.0.0", "--port", "8000"]

