import streamlit as st
import asyncio
import os
import httpx
import json

API_URL = os.getenv("API_URL", "http://127.0.0.1:8080/predict")
API_MODELS = os.getenv("API_MODELS", "http://127.0.0.1:8080/models")

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

# Get models 

st.title('Ollama Chatbot')
st.write('Explora distintos modelos de lenguaje con Interfaz de Streamlit')

# # Inicialización de estado de sesión
# if 'model_selection' not in st.session_state:
#     st.session_state.model_selection = 'mistral:latest'  # Valor por defecto
# Obtener modelos (solo una vez)
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

# Campo de entrada de usuario
user_input = st.chat_input('Haz tu pregunta:')

if user_input:
    with st.chat_message("user"):
        st.write(user_input)
        print(f"Input del usuario: {user_input}")  # Debug 1

    try:
        with st.chat_message("assistant"):
            st.markdown("🧠 Pensando...")
            response_area = st.empty()
            print("Asistente inicializado")  # Debug 2

            # Usamos un diccionario para almacenar el estado
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
                        json={
                            "input_text": user_input,
                            "model": st.session_state.model_selection,
                            "temperature": st.session_state.temperature,
                            "top_p": st.session_state.top_p,
                            "top_k": st.session_state.top_k,
                            "max_tokens": st.session_state.max_tokens
                        }
                    )
                    print(f"Respuesta HTTP recibida. Status: {response.status_code}")  # Debug 5

                    async for line in response.aiter_lines():
                        print(f"Línea recibida: {line}")  # Debug 6 (crítico)
                        if line:
                            chunk = json.loads(line)
                            print(f"Chunk procesado: {chunk}")  # Debug 7
                            if "content" in chunk:
                                response_state["full_response"] += chunk["content"]
                                response_area.markdown(response_state["full_response"] + "▌")
                            
                            # if chunk.get("done"):
                            #     response_state["metadata"] = {
                            #         "model": chunk.get("model", ""),
                            #         "eval_count": chunk.get("eval_count", 0),
                            #         "total_duration": chunk.get("total_duration", 0)
                            #     }
                                print("Stream completado")  # Debug 8

            # Ejecutar la corutina
            asyncio.run(fetch_and_stream())
            print(f"Respuesta final: {response_state['full_response']}")  # Debug 9

            # Actualizar UI final
            response_area.markdown(response_state["full_response"])
            
            # Guardar en historial
            if response_state["metadata"]:
                st.session_state.historial.append({
                    "role": "assistant",
                    "content": response_state["full_response"],
                    "model": response_state["metadata"]["model"],
                    "tokens": response_state["metadata"]["eval_count"],
                    "tiempo": response_state["metadata"]["total_duration"] / 1e9
                })

                # Mostrar metadata
                st.caption(
                    f"Modelo: {response_state['metadata']['model']} | "
                    f"Tokens: {response_state['metadata']['eval_count']} | "
                    f"Tiempo: {response_state['metadata']['total_duration'] / 1e9:.2f}s"
                )

    except Exception as e:
        print(f"ERROR: {str(e)}")  # Debug 10 (importante)
        st.error(f"Error en la comunicación: {str(e)}")


# import streamlit as st
# from langchain_ollama import ChatOllama
# # import ollama
# import asyncio
# import os
# import httpx
# API_URL = os.getenv("API_URL", "http://127.0.0.1:8080/predict")
# API_MODELS = os.getenv("API_MODELS", "http://127.0.0.1:8080/models")

# async def list_models():
#     async with httpx.AsyncClient() as client:
#         response = await client.get(API_MODELS)  # 🔥 Usar variable de entorno
#         return response.json()["models"]  # 🎯 Nueva clave en la respuesta
    
                
#     # models_running = ollama.list()['models']
#     # available_models = [model["model"] for model in models_running]
#     # return available_models

# st.title('Ollama Chatbot')
# st.write('Explora distintos modelos de lenguaje con Interfaz de Streamlit')

# if 'model_selection' not in st.session_state:
#     st.session_state.model_selection = 'gemma3:12b'

# if 'historial' not in st.session_state:
#     st.session_state.historial = []

# with st.sidebar:
#     st.write('## Model Selection')
#     st.session_state.model_selection = st.selectbox(
#         'Select a model',
#         list_models(),
#         index=0
#     )
#     st.session_state.temperature = st.slider(
#         'Temperatura',
#         min_value=0.0,
#         max_value=1.0,
#         value=0.7,
#         step=0.1
#     )
#     st.session_state.top_p = st.slider(
#         'Top P',
#         min_value=0.0,
#         max_value=1.0,
#         value=0.9,
#         step=0.1
#     )
#     st.session_state.top_k = st.slider(
#         'Top K',
#         min_value=0,
#         max_value=100,
#         value=40,
#         step=1
#     )
#     st.session_state.max_tokens = st.slider(
#         'Max Tokens',
#         min_value=1,
#         max_value=4096,
#         value=256,
#         step=1
#     )

# # 🔥 Aquí creamos el LLM para stream
# llm = ChatOllama(
#     model=st.session_state.model_selection,
#     temperature=st.session_state.temperature,
#     num_predict=st.session_state.max_tokens,
#     top_p=st.session_state.top_p,
#     top_k=st.session_state.top_k,
#     disable_streaming=True,   # 🔥 IMPORTANTE: Habilitar streaming!
# )

# user_input = st.chat_input('Haz tu pregunta:')

# if user_input is not None:
#     # Mostrar input inmediatamente
#     with st.chat_message("user"):
#         st.write(user_input)

#     try:
#         # 🔥 Primero pedir el contexto relevante a FastAPI
#         with st.spinner("🔍 Buscando información relevante..."):
#             async def fetch_context():
#                 async with httpx.AsyncClient(timeout=300.0) as client:
#                     response = await client.post(API_URL, json={"input_text": user_input})
#                     response.raise_for_status()
#                     return response.json()["message"]

#             prompt = asyncio.run(fetch_context())

#         with st.chat_message("assistant"):
#             st.markdown("🧠 Pensando...")

#             # 🔥 Ahora stream con langchain-ollama
#             stream = llm.stream([("user", prompt)])

#             response_text = ""
#             response_container = st.empty()  # Contenedor para ir actualizando

#             for chunk in stream:
#                 if chunk.content:  # Solo si viene texto nuevo
#                     response_text += chunk.content
#                     response_container.markdown(response_text)  # Ir mostrando lo que llega

#             # 🔥 Guardar en historial
#             st.session_state.historial.append({
#                 "role": "assistant",
#                 "content": response_text,
#                 "model": stream.response_metadata['model'],
#                 "tokens": stream.response_metadata['eval_count'],
#                 "tiempo": stream.response_metadata['total_duration'] / 1e9
#             })

#             # Mostrar metadata
#             st.caption(
#                 f"Modelo: {stream.response_metadata['model']} | "
#                 f"Tokens: {stream.response_metadata['eval_count']} | "
#                 f"Tiempo: {stream.response_metadata['total_duration'] / 1e9:.2f}s"
#             )

#     except Exception as e:
#         st.error(f"Error: {e}")



# @cl.on_message
# async def on_message(message: cl.Message):
#     # 🔹 Enviar mensaje de carga
#     waiting_msg = cl.Message(content="⏳ Generando respuesta, por favor espera...")
#     await waiting_msg.send()

#     try:
#         ### Enviar pregunta a FastAPI
#         async with httpx.AsyncClient(timeout=300.0) as client:
#             response = await client.post(API_URL, json={"input_text": message.content})

#         # Procesar la respuesta
#         if response.status_code == 200:
#             data = response.json()
#             answer = data.get("message", "Error en la respuesta.")
#         else:
#             answer = "❌ Error al conectar con el modelo."

#         print(f"✅ Respuesta obtenida: {answer}")  # Depuración

#         # 🔹 Eliminar el mensaje de carga antes de enviar la respuesta final
#         await waiting_msg.remove()

#         # 🔹 Enviar la respuesta final correctamente
#         await cl.Message(content=answer).send()

#     except Exception as e:
#         print(f"⚠️ Error en la solicitud: {e}")
#         await waiting_msg.remove()
#         await cl.Message(content="❌ Ocurrió un error al procesar tu solicitud.").send()