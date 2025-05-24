import streamlit as st
import nest_asyncio
import asyncio
import os
import httpx
import json
import time
from uuid import uuid4

BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://127.0.0.1:8080")
API_URL = f"{BACKEND_BASE_URL}/predict"
API_MODELS = f"{BACKEND_BASE_URL}/models"
API_RAG = f"{BACKEND_BASE_URL}/rag"

# API_URL = os.getenv("API_URL", "http://127.0.0.1:8080/predict")
# API_MODELS = os.getenv("API_MODELS", "http://127.0.0.1:8080/models")




# Carga íconos personalizados (locales)
icon_user = ""
icon_assistant = "public/favicon.png"
icon_loading = ""
show_think = False

def render_typing_animation(text, area):
    words = text.split()
    displayed = ""
    for word in words:
        displayed += word + " "
        area.markdown(displayed + "▌")
        time.sleep(0.05)
    area.markdown(displayed.strip())

async def list_models():
    if "cached_models" in st.session_state:
        return st.session_state.cached_models
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(API_MODELS)
            response.raise_for_status()
            models = response.json().get("models", [])
            # st.session_state.cached_models = models  # Almacenar en caché
            return models
        except Exception as e:
            st.error(f"Error obteniendo modelos: {str(e)}")
            return []


@st.dialog("Error")
def alert_dialog():
    st.write(f"Por favor adjunta un PDF de ficha tecnica")
    if st.button("Entiendo"):
        st.rerun()
    
@st.dialog("Información")
def success_dialog():
    st.write(f"PDF añadido exitosamente")
    if st.button("Ok"):
        st.rerun()


# Paso 2: Función para limpiar el uploader
def limpiar_uploader():
    st.session_state.reset_uploader = True

st.set_page_config(page_title="Asistente de Motores", layout="centered")
st.image("public/logo_dark.png", use_container_width=True) 
# st.title('Ollama Chatbot')
st.write('Estoy para ayudarte en tus consultas sobre motores')

# # Initialization
# Get models once
if "cached_models" not in st.session_state:
    st.session_state.cached_models = asyncio.run(list_models())

if 'historial' not in st.session_state:
    st.session_state.historial = []

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid4())

# Paso 1: Inicializamos las claves
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = str(uuid4())
if "reset_uploader" not in st.session_state:
    st.session_state.reset_uploader = False

# Paso 3: Lógica para cambiar la key (trigger visual)
if st.session_state.reset_uploader:
    st.session_state.uploader_key = str(uuid4())
    st.session_state.reset_uploader = False

# Sidebar con controles
with st.sidebar:
    st.write('## Model Selection')
    st.session_state.model_selection = st.selectbox(
        'Select a model',
        options=st.session_state.cached_models,
        index=0
    )

    st.write('## DB Selection')
    st.session_state.db_selection = st.selectbox(
        'Select a Vector Data Base',
        options=['Milvus', 'FAISS', 'Chroma', 'Qdrant'],
        index=0
    )


    uploaded_pdf = st.file_uploader("Adjunta una ficha técnica", accept_multiple_files=False, key=st.session_state.uploader_key)
    if st.button("Añadir PDF", use_container_width=True):
        try:
            if uploaded_pdf:
                with httpx.Client() as client:
                    response = client.post(
                    API_RAG, # Use client.post for file uploads typically
                    files={"file": (uploaded_pdf.name, uploaded_pdf.getvalue(), "application/pdf")},
                    data={"data_base_name": str(st.session_state.db_selection)}
                )
                response.raise_for_status() # Raises an HTTPStatusError for bad responses (4xx or 5xx)
                success_dialog()
                limpiar_uploader()
            else:
                alert_dialog()

        except Exception as e:
            st.error(f"Error al Cargar PDF: {str(e)}")
    
    st.session_state.temperature = st.slider(
        'Temperatura',
        min_value=0.0,
        max_value=1.0,
        value=0.7,
        step=0.1
    )
    
    st.session_state.top_p = st.slider(
        'Top P',
        min_value=0.0,
        max_value=1.0,
        value=0.9,
        step=0.1
    )
    
    st.session_state.top_k = st.slider(
        'Top K',
        min_value=0,
        max_value=100,
        value=40,
        step=1
    )
    
    st.session_state.max_tokens = st.slider(
        'Max Tokens',
        min_value=1,
        max_value=4096,
        value=256,
        step=1
    )

async def fetch_response(user_input: str, model: str, temperature: float):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            API_URL,
            json={
                "input_text": user_input,
                "model": model,
                "temperature": temperature
            }
        )
        return response


# Mostrar historial (excepto temporales)
for mensaje in st.session_state.historial:
    if mensaje.get("temporal"):
        continue

    if mensaje["role"] == "user":
        with st.chat_message(mensaje["role"]):
            st.markdown(mensaje["content"])
    else:
        with st.chat_message(mensaje["role"], avatar=icon_assistant):
            st.empty()
            st.markdown(mensaje["content"])

# Campo de entrada de usuario
user_input = st.chat_input('Haz tu pregunta:')

if user_input:
    # Guardar primero el mensaje del usuario en historial
    st.session_state.historial.append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("user"):
        # st.write(user_input)
        st.markdown(user_input)
        print(f"Input del usuario: {user_input}")  # Debug 1

    nest_asyncio.apply()

    try:
        with st.chat_message("assistant", avatar=icon_assistant):
            with st.spinner("🧠 El modelo está pensando..."):
                st.session_state.show_think = False
                response_area_think = st.empty()  # Área para pensamientos
                response_area_content = st.empty()  # Área para contenido principal

                # Mostrar spinner solo si hay contenido de pensamiento
                if st.session_state.show_think:
                    with st.spinner("🧠 El modelo está pensando..."):
                        pass
                
                print("Asistente inicializado")  # Debug 2

                # Usamos un diccionario para almacenar el estado
                st.session_state.historial.append({
                    "role": "assistant",
                    "content": "",
                    "temporal": True
                })

                # Declaramos la variable dentro del contexto correcto
                response_state = {
                    "full_response": "",
                    "thinking":"",
                    "metadata": {}
                }

                async def fetch_and_stream():
                    print("Iniciando fetch_and_stream")  # Debug 3
                    st.session_state.show_think = False  # Resetear estado

                    async with httpx.AsyncClient(timeout=400.0) as client:
                        print(f"Enviando POST a: {API_URL}")  # Debug 4
                        response = await client.post(
                            API_URL,
                            #files={"file": (uploaded_pdf.name, uploaded_pdf, "application/pdf")},
                            data={
                                "input_text": user_input,
                                "model": st.session_state.model_selection,
                                "temperature": str(st.session_state.temperature),
                                "top_p": str(st.session_state.top_p),
                                "top_k": str(st.session_state.top_k),
                                "max_tokens": str(st.session_state.max_tokens),
                                "db": str(st.session_state.db_selection),
                                "session_id": str(st.session_state.session_id),
                            }
                        )
                        print(f"Respuesta HTTP recibida. Status: {response.status_code}")  # Debug 5

                        async for line in response.aiter_lines():
                            # line = line.rstrip('\n') #line.strip()
                            if not line:
                                continue

                            try:
                                chunk = json.loads(line)
                            except json.JSONDecodeError as e:
                                print(f"Error parseando línea: {line} - {e}")
                                continue
                            
                            # Manejar contenido de pensamiento
                            if "think" in chunk and chunk["think"]:
                                response_state["thinking"] += chunk["think"]
                                st.session_state.show_think = True
                                response_area_think.markdown(response_state["thinking"] + "▌")

                            # Manejar contenido principal
                            if "content" in chunk and chunk["content"]:
                                response_state["full_response"] += chunk["content"]
                                response_area_content.markdown(response_state["full_response"] + "▌")

                            if "metadata" in chunk and chunk["metadata"]:
                                response_state["metadata"] = chunk["metadata"]
                                # Metadata will be displayed once after the full response is received

                        #For not Stream
                        # async for line in response.aiter_lines():
                        #     print(f"Línea recibida: {line}")  # Debug 6 (crítico)
                        #     line = line.strip()
                        #     if not line:
                        #         continue  # Ignora líneas vacías

                        #     try:
                        #         chunk = json.loads(line)
                        #         print(f"Chunk procesado: {chunk}") # Debug 7
                        #     except json.JSONDecodeError as e:
                        #         print(f"Error parseando línea: {line} - {e}")
                        #         continue


                        #     # if "think" in chunk and chunk["think"]:
                        #     #     full_think += chunk["think"]
                        #     #     placeholder_think.markdown(f"🧠 Pensando...\n\n{full_think}▌")

                        #     if "content" in chunk and chunk["content"]:
                        #         response_state["full_response"] += chunk["content"]
                        #         response_area.markdown(response_state["full_response"] + "▌")

                        #     if "metadata" in chunk:
                        #         response_state["metadata"] = chunk["metadata"]
                            
                        #         with st.expander("📊 Metadatos de la respuesta"):
                        #             metadata = response_state["metadata"]
                        #             if metadata:
                        #                 st.write({
                        #                     "Modelo": metadata.get("model", ""),
                        #                     "Tokens del prompt": metadata.get("prompt_eval_count", 0),
                        #                     "Tokens generados": metadata.get("eval_count", 0),
                        #                     "Duración total (s)": round(metadata.get("total_duration", 0) / 1e9, 3),
                        #                     "Razón de finalización": metadata.get("done_reason", ""),
                        #                     "Creado en": metadata.get("created_at", ""),
                        #                 })
                        #             else:
                        #                 st.info("No se recibieron metadatos del modelo.")

                            # if line:
                            #     chunk = json.loads(line)
                            #     print(f"Chunk procesado: {chunk}")  # Debug 7
                            #     if "content" in chunk:
                            #         response_state["full_response"] += chunk["content"]
                            #         render_typing_animation(response_state["full_response"], response_area)
                            #         # response_area.markdown(response_state["full_response"] + "▌")
                                
                            #     # if chunk.get("done"):
                            #     #     response_state["metadata"] = {
                            #     #         "model": chunk.get("model", ""),
                            #     #         "eval_count": chunk.get("eval_count", 0),
                            #     #         "total_duration": chunk.get("total_duration", 0)
                            #     #     }
                            print("Stream completado")  # Debug 8


                # Ejecutar la corrutina asincrónica con compatibilidad para Streamlit
                loop = asyncio.get_event_loop()
                loop.run_until_complete(fetch_and_stream())

                # asyncio.run(fetch_and_stream())
                print(f"Respuesta final: {response_state['full_response']}")  # Debug 9

                # Ocultar área de think si no hubo contenido
                if not st.session_state.show_think:
                    response_area_think.empty()
                else:
                    response_area_think.markdown(response_state["thinking"].strip()) # Remove final cursor


                # Final update and display metadata after the stream completes
                response_area_content.markdown(response_state["full_response"].strip()) # Remove final cursor

                # Update historical with the full response
                st.session_state.historial[-1] = {
                    "role": "assistant",
                    "content": response_state["full_response"].strip()
                }

                if response_state["metadata"]:
                    with st.expander("📊 Metadatos de la respuesta"):
                        metadata = response_state["metadata"]
                        st.write({
                            "Modelo": metadata.get("model", ""),
                            "Tokens del prompt": metadata.get("prompt_eval_count", 0),
                            "Tokens generados": metadata.get("eval_count", 0),
                            "Duración total (s)": round(metadata.get("total_duration", 0) / 1e9, 3),
                            "Razón de finalización": metadata.get("done_reason", ""),
                            "Creado en": metadata.get("created_at", ""),
                        })
                else:
                    st.info("No se recibieron metadatos del modelo.")

                ###For Streaming
                # # Actualizar UI final
                # response_area.markdown(response_state["full_response"])
                
                # #Add Historical for Assistant
                # st.session_state.historial[-1] = {
                #     "role": "assistant",
                #     "content": response_state["full_response"]
                # }

                # if response_state["metadata"]:
                #     # ###Add Historical for Assistant
                #     # st.session_state.historial.append({
                #     #     "role": "assistant",
                #     #     "content": response_state["full_response"]
                #     #     # "model": response_state["metadata"]["model"],
                #     #     # "tokens": response_state["metadata"]["eval_count"],
                #     #     # "tiempo": response_state["metadata"]["total_duration"] / 1e9
                #     # })


                #     # Mostrar metadata
                #     st.caption(
                #         f"Modelo: {response_state['metadata']['model']} | "
                #         f"Tokens: {response_state['metadata']['eval_count']} | "
                #         f"Tiempo: {response_state['metadata']['total_duration'] / 1e9:.2f}s"
                #     )

    except Exception as e:
        print(f"ERROR: {str(e)}")  # Debug 10 (importante)
        st.error(f"Error en la comunicación: {str(e)}")
