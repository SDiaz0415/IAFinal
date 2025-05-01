import streamlit as st
import nest_asyncio
import asyncio
import os
import httpx
import json
import time

API_URL = os.getenv("API_URL", "http://127.0.0.1:8080/predict")
API_MODELS = os.getenv("API_MODELS", "http://127.0.0.1:8080/models")


# Carga íconos personalizados (locales)
icon_user = ""
icon_assistant = "public/favicon.png"
icon_loading = ""

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

# Sidebar con controles
with st.sidebar:
    st.write('## Model Selection')
    st.session_state.model_selection = st.selectbox(
        'Select a model',
        options=st.session_state.cached_models,
        index=0
    )

    uploaded_pdf = st.file_uploader("Añade una ficha técnica", accept_multiple_files=False)
    
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
                response_area = st.empty()

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
                    "metadata": {}
                }

                async def fetch_and_stream():
                    print("Iniciando fetch_and_stream")  # Debug 3
                    async with httpx.AsyncClient(timeout=300.0) as client:
                        print(f"Enviando POST a: {API_URL}")  # Debug 4
                        response = await client.post(
                            API_URL,
                            files={"file": (uploaded_pdf.name, uploaded_pdf, "application/pdf")},
                            data={
                                "input_text": user_input,
                                "model": st.session_state.model_selection,
                                "temperature": str(st.session_state.temperature),
                                "top_p": str(st.session_state.top_p),
                                "top_k": str(st.session_state.top_k),
                                "max_tokens": str(st.session_state.max_tokens)
                            }
                        )
                        print(f"Respuesta HTTP recibida. Status: {response.status_code}")  # Debug 5

                        async for line in response.aiter_lines():
                            print(f"Línea recibida: {line}")  # Debug 6 (crítico)
                            line = line.strip()
                            if not line:
                                continue  # Ignora líneas vacías

                            try:
                                chunk = json.loads(line)
                                print(f"Chunk procesado: {chunk}") # Debug 7
                            except json.JSONDecodeError as e:
                                print(f"Error parseando línea: {line} - {e}")
                                continue


                            # if "think" in chunk and chunk["think"]:
                            #     full_think += chunk["think"]
                            #     placeholder_think.markdown(f"🧠 Pensando...\n\n{full_think}▌")

                            if "content" in chunk and chunk["content"]:
                                response_state["full_response"] += chunk["content"]
                                response_area.markdown(response_state["full_response"] + "▌")

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

                # Actualizar UI final
                response_area.markdown(response_state["full_response"])
                
                #Add Historical for Assistant
                st.session_state.historial[-1] = {
                    "role": "assistant",
                    "content": response_state["full_response"]
                }

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
