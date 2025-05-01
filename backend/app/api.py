# from fastapi import FastAPI, HTTPException
# from fastapi.responses import StreamingResponse
# 
# import torch
# from langchain_ollama import ChatOllama

import sys
import os
from pathlib import Path
import re
import shutil

# Añade la ruta del directorio `app` al PYTHONPATH
# sys.path.append(str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from langchain_ollama import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
##### Custom
from app.model_loader import get_ollama_client
from app.system_prompt import system_prompt_get
from app.extractor_texto import extraer_texto_desde_pdf, extraer_especificaciones

# sys.path.append(os.path.dirname(os.path.abspath(__file__)))


# from model_loader import load_model  # 🔥 Importamos el modelo ya cargado
# from embeddings.embedding_store import EmbeddingStore  # 🔥 Importamos la búsqueda de contexto
# import numpy as np

# ✅ Cargar el modelo desde el módulo sin volver a descargarlo
# model, tokenizer, device = load_model()

# store = EmbeddingStore()


# Configuración de LangChain
# SYSTEM_PROMPT = "Eres un experto en motores eléctricos con 25 años de experiencia. Responde de manera técnica y detallada."


app = FastAPI( debug=True )
# app = FastAPI(title="Chatbot API", description="API optimizada con GPU", version="4.2.0")

# print(torch.__version__)
# print(f"torch cuda aviable {torch.cuda.is_available()}")  # Debe imprimir `False`

class InputData(BaseModel):
    input_text: str
    model: str
    temperature: float
    top_p: float
    top_k: int
    max_tokens: int


# Configuración de LangChain
# SYSTEM_PROMPT = "Eres un experto en motores eléctricos con 25 años de experiencia. Responde de manera técnica y detallada."
# SYSTEM_PROMPT = "Eres un experto en información sobre Colombia. Todas las preguntas que se te hagan las vas a responder utilizando slangs y regionalismos de Colombia en todo agradable y amable"
SYSTEM_PROMPT = system_prompt_get( )


def create_chain(model: str, temperature: float):
    llm = ChatOllama(
        model=model,
        temperature=temperature,
        num_predict=256,
        system=SYSTEM_PROMPT,
        disable_streaming=False,
        metadata={}
        # stream=True
    )
    
    prompt_template = ChatPromptTemplate([
        # ("system", SYSTEM_PROMPT),
        ("human", 
         """Utiliza la siguiente información de referencia para responder:
         [Contexto relevante]
         {context}

         [Pregunta del usuario]
         {input}

         [Instrucciones]
            - Responde como un experto de 25 años en motores.
            - Sé técnico, claro y detallado.
            - No repitas la pregunta ni menciones que estás usando contexto.
            - Si no sabes algo, dilo con honestidad.
         """)
    ])
    return llm, prompt_template
    # return llm | prompt_template | StrOutputParser()


# def es_pregunta_sobre_motores(pregunta):
#     """Determina si la pregunta es sobre motores eléctricos usando palabras clave."""
#     palabras_clave = ["motor", "voltaje", "corriente", "rpm", "bobinado", "tensión", "aislamiento", "falla"]
#     return any(palabra in pregunta.lower() for palabra in palabras_clave)

def es_pregunta_sobre_motores(pregunta):
    """Determina si una pregunta es sobre motores eléctricos aplicando un umbral en FAISS."""
    
    print(f"\n🔍 Pregunta recibida: {pregunta}")

    # results = store.search(pregunta, top_k=3, umbral=0.5, max_top_k=50)  # 🔹 Usa el nuevo `search()` con umbral
    # results = store.search(pregunta)
    results = ''

    if results:
        print(f"✅ FAISS activado. Documentos relevantes: {len(results)}")
        return results
    
    print("❌ No hay documentos relevantes. Clasificando como pregunta general.")
    return []

@app.get("/")
def home():
    return {"message": "API ejecutándose 🚀"}

@app.get("/models")
def list_available_models():
    try:
        ollama_client = get_ollama_client()
        models = ollama_client.list_models()
        return {"models": models}
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error obteniendo modelos: {str(e)}"
        )

@app.post("/predict")
# async def predict(request: InputData):
async def predict(
    file: UploadFile = File(...),
    input_text: str = Form(...),
    model: str = Form(...),
    temperature: float = Form(...),
    top_p: float = Form(...),
    top_k: int = Form(...),
    max_tokens: int = Form(...)
):
    llm_chain, prompt_template = create_chain(
        model= model, #request.model,
        temperature= temperature #request.temperature
    )

    # Guardar PDF temporalmente
    ruta_temp = f"temp_pdfs/{file.filename}" # {file.filename}
    os.makedirs("temp_pdfs", exist_ok=True)
    with open(ruta_temp, "wb") as f_out:
        shutil.copyfileobj(file.file, f_out) #(file.file, f_out)

    # Extraer contexto desde el PDF
    texto = extraer_texto_desde_pdf(ruta_temp)
    contexto = extraer_especificaciones(texto, file.filename)#(texto, file.filename)

    os.remove(ruta_temp)

    # contexto = "Motor marca: REPUBLIC, potencia: 15.00 HP, tension: 230 - 460 V, corriente: 40 - 20 Amp."
    
     # 🔥 Formateamos el prompt ANTES de pasarlo al modelo
    message_prompt = await prompt_template.ainvoke({
        "input": input_text, #request.input_text,
        "context": contexto
    })


    async def generate_stream():
        async for chunk in llm_chain.astream(message_prompt):
            if chunk.content:
            # Separa el <think> del resto
                think_match = re.search(r"<think>(.*?)</think>", chunk.content, re.DOTALL)
                pensamiento = think_match.group(1) if think_match else ""
                respuesta = re.sub(r"<think>.*?</think>", "", chunk.content, flags=re.DOTALL)

                # Puedes ahora yieldear ambos
                yield f"{json.dumps({'think': pensamiento, 'content': respuesta})}\n\n"


            # print(f"imprimiendo chunk: {chunk}")
            # yield f"{json.dumps({'content': chunk.content})}\n\n"
            # # yield f"{json.dumps({'content': chunk})}\n\n"
            # # yield f"data: {json.dumps({'content': chunk})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="application/x-ndjson"
        # media_type="text/event-stream"
    )


# if __name__ == "__main__":
#     #  ollama_client = OllamaClient(model_name='mistral:latest')
#     # list_available_models()
#     predict({"model":"llama3.2:latest", "temperature":"0.7" })



# async def predict(request: InputData):
#     ollama_client = get_ollama_client()
    
#     async def generate_stream():
#         response = ollama_client.ollama_client.generate(
#             model=request.model,
#             prompt=request.input_text,
#             options={
#                 "temperature": request.temperature,
#                 "top_p": request.top_p,
#                 "top_k": request.top_k,
#                 "num_predict": request.max_tokens
#             },
#             stream=True
#         )
        
#         async for chunk in response:
#             yield json.dumps({
#                 "response": chunk.get("response", ""),
#                 "done": chunk.get("done", False),
#                 "model": chunk.get("model", ""),
#                 "eval_count": chunk.get("eval_count", 0),
#                 "total_duration": chunk.get("total_duration", 0)
#             }) + "\n"
    
#     return StreamingResponse(generate_stream(), media_type="application/x-ndjson")



# @app.post("/predict")
# async def predict(data: InputData):

#     print(f"si llego: {data.input_text}")
#     is_motor_question = es_pregunta_sobre_motores(data.input_text)
#     if is_motor_question:
#         cleaned_docs = []
#         print("✅ Recibida solicitud con:", data.input_text)

#         retrieved_docs = is_motor_question

#         if not retrieved_docs:
#             context = "No se encontró información relevante en la base de datos."
#         else:
#             for doc in retrieved_docs:
#                 lines = doc.split("\n")
#                 unique_lines = list(dict.fromkeys(lines))
#                 cleaned_doc = "\n".join(unique_lines[:5])
#                 cleaned_docs.append(cleaned_doc)

#         context = " ".join(cleaned_docs)[:500]
#         prompt = f"""Eres un asistente experto en motores eléctricos con 25 años de experiencia. Usa la siguiente información para responder sin mencionar este contexto en la respuesta.

#         [Contexto relevante]
#         {context}

#         [Instrucciones]
#         Responde de forma clara y concisa basándote en el contexto relevante. No menciones que eres un asistente ni hagas referencia al contexto explícitamente.

#         [Pregunta del usuario]
#         {data.input_text}

#         [Respuesta]"""
#     else:
#         prompt = f"""Eres un asistente general. Responde de manera clara y útil a la siguiente pregunta:

#         Usuario: {data.input_text}
#         Modelo:"""

#     print(f"📝 Prompt generado:\n{prompt}")

#     # 👇 Aquí simplemente devuelves el prompt
#     return {"message": prompt}