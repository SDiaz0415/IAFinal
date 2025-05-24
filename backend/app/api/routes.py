import json
import shutil
import os
import json
import convertapi

from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from fastapi.responses import StreamingResponse
from langchain_core.runnables.history import RunnableWithMessageHistory

from app.llm.manager import LLMManager
from app.llm.clients import get_ollama_client
#########DB Clases
from app.data_processing.text_extractor_txt import TextExtractor
from app.embeddings.milvus_db import MilvusConnection 
from app.embeddings.chroma_db import ChromaConnection 
from app.embeddings.FAISS_db import FAISSConnection   
from app.embeddings.Qdrant_db import QdrantConnection 
from app.core.config import settings
from app.llm.rag import RAGUtilities
from app.llm.historical import get_by_session_id


#Constans
FILE_TYPES = ('txt', 'pdf')

#Variables
thinking_add = False

#DB Configurations
database_config = {}
db_connection = None

#Define Routes
router = APIRouter()

# LLMManager Instance
llm_manager = LLMManager()

#################Local Methods
def get_db_connection(db_name: str):
    # 1. Configuración de conexión (puedes cargarla desde settings)
    db_instance = None
    match db_name:
        case 'Milvus': 
            database_config["api_key"] = settings.MILVUS_API
            database_config["end_point"] = settings.MILVUS_END_POINT
            database_config["collection_name"] = 'motor_collection'
            database_config["embeddings"] = 'nomic-embed-text:latest'
            db_instance = MilvusConnection(database_config)

        case 'FAISS': 
            database_config["api_key"] = ''
            database_config["end_point"] = './FAISS_langchain_db'
            database_config["collection_name"] = ''
            database_config["embeddings"] = 'nomic-embed-text:latest'
            db_instance = FAISSConnection(database_config)
        
        case 'Qdrant': 
            database_config["api_key"] = settings.QDRANT_API
            database_config["end_point"] = settings.QDRANT_END_POINT
            database_config["collection_name"] = 'motor_collection'
            database_config["embeddings"] = 'nomic-embed-text:latest'
            db_instance = QdrantConnection(database_config)

        case 'Chroma': 
            database_config["api_key"] = ''
            database_config["end_point"] = './chroma_langchain_db'
            database_config["collection_name"] = 'motor_collection'
            database_config["embeddings"] = 'nomic-embed-text:latest'
            db_instance = ChromaConnection(database_config)
    
    return db_instance



################Routes Start

@router.get("/models")
async def list_available_models():
    """
    Lista los modelos de Ollama disponibles.
    """
    try:
        ollama_client = get_ollama_client()
        models_running = ollama_client.list_models()
        models = [ model for model in models_running if "nomic" not in model]
        return {"models": models}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo modelos: {str(e)}"
        )

@router.post("/predict")
async def predict(
    # file: UploadFile = File(...),
    input_text: str = Form(...),
    model: str = Form(...),
    temperature: float = Form(...),
    top_p: float = Form(...),
    top_k: int = Form(...),
    db: str = Form(...),
    session_id: str = Form(...),
    max_tokens: int = Form(...)
):
    """
    Genera una respuesta del chatbot, extrayendo contexto de un PDF subido.
    """
    ####Validate if pdf file is uploaded to DB
    ##Check if txt exist, if exists PDF on DB
   
    ######Get DB instance 
    db_connection = get_db_connection(db_name=db)
    
    ######Connect to DB
    db_connection.connect()

    ###########RAG Query
    contexto_final = db_connection.query_vectors(user_query=input_text, top_k=4)
    
    ###########Disconnect DB
    db_connection.disconnect()
   

    ######Create llm and prompt template
    llm_chain, prompt_template = llm_manager.create_rag_chain(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
        top_k=top_k
    )

    #####Create the chain
    chain = prompt_template | llm_chain

    ####### Create model with history
    chain_with_history = RunnableWithMessageHistory(
        chain,
        # Uses the get_by_session_id function defined in the example
        # above.
        get_by_session_id,
        input_messages_key="input",
        history_messages_key="history",
    )

    ####### Define Stream Function
    async def generate_stream():
        global thinking_add
        ### TODO: This is for not stream
        # response = llm_chain.invoke(message_prompt)
        # response = chain_with_history.invoke(
        #     {
        #         "input": input_text,
        #         "context": contexto_final
        #     },
        #     config={"configurable": {"session_id": session_id}}
        # )
        
        # # Parsear el pensamiento y la respuesta
        # think_match = re.search(r"<think>(.*?)</think>", response.content, re.DOTALL)
        # pensamiento = think_match.group(1).strip() if think_match else ""
        # respuesta_limpia = re.sub(r"<think>.*?</think>", "", response.content, flags=re.DOTALL).strip()
        # metadata = response.response_metadata
        # history = get_by_session_id(session_id)
        # history_serialized = [message.model_dump() for message in history.messages]

        # yield f"{json.dumps({'think': pensamiento, 'content': respuesta_limpia, 'metadata': metadata, 'history':history_serialized})}\n\n"

        ######Steaming Way
        async for chunk in chain_with_history.astream(
            {
                "input": input_text,
                "context": contexto_final
            },
            config={"configurable": {"session_id": session_id}}
        ):
            
            if chunk.content:
                contenido = chunk.content
                metadata = chunk.response_metadata

                if "<think>" in contenido or "</think>" in contenido:
                    thinking_add = "<think>" in contenido  # True si abre la etiqueta
                    pensamiento = contenido
                    respuesta_limpia = ""
                else:
                    if thinking_add:
                        pensamiento = contenido
                        respuesta_limpia = ""
                    else:
                        pensamiento = ""
                        respuesta_limpia = contenido

                yield f"{json.dumps({'think': pensamiento, 'content': respuesta_limpia, 'metadata': metadata})}\n\n"
                # history = get_by_session_id(session_id)
                # history_serialized = [message.model_dump() for message in history.messages]
                # yield f"{json.dumps({'think': pensamiento, 'content': respuesta_limpia, 'metadata': metadata, 'history':history_serialized})}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="application/x-ndjson"
    )

@router.post("/rag")
def predict(
    file: UploadFile = File(...),
    data_base_name: str = Form(...)
):
    
    ## 1. Guardar PDF temporalmente
    os.makedirs(settings.TEMP_PDFS_DIR, exist_ok=True)
    temp_pdf_path = os.path.join(settings.TEMP_PDFS_DIR, file.filename)
    try:
        with open(temp_pdf_path, "wb") as f_out:
            shutil.copyfileobj(file.file, f_out)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al guardar el PDF temporalmente: {str(e)}"
        )

    ## 2.Create dir and Send PDF to OCR API to get txt file
    os.makedirs(settings.SAVE_RAW_DOCS_DIR, exist_ok=True)
    convertapi.api_credentials = settings.CONVERT_API_SECRET
    convertapi.convert(FILE_TYPES[0], { 
        'File': temp_pdf_path,
        'OcrLanguage': 'es'
    }, from_format = FILE_TYPES[1]).save_files(settings.SAVE_RAW_DOCS_DIR)

    ###########RAG Creation
    db_connection = get_db_connection(db_name=data_base_name)

    ######Connect to DB
    db_connection.connect()

    #######Extract data from TXT
    base_name = os.path.splitext(file.filename)[0]
    txt_path = os.path.join(settings.GET_RAW_DOCS_DIR, base_name + '.' + FILE_TYPES[0])
    print("Leyendo archivo en:", txt_path)
    extractor = TextExtractor(txt_path)
    results = extractor.get_results()
    print(json.dumps(results, ensure_ascii=False, indent=2))

    # ###########Populate DB
    RAGBuilder = RAGUtilities(db_connection)
    RAGBuilder.populate_db(results)

    ###########Disconnect DB
    db_connection.disconnect()