from app.embeddings.service import VectorDBConnection 
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from uuid import uuid4

class RAGUtilities:
    def __init__(self, db_Connection: VectorDBConnection):
        self.vector_store = db_Connection.get_vector_store

    def populate_db(self, data_json):
        resultados = self.extraer_especificaciones(data_json)
        chunks = self.documents_create(resultados)
        print(chunks)

        # Generate UUIDs for documents
        uuids = [str(uuid4()) for _ in range(len(chunks))]
        print(uuids)

        self.vector_store.add_documents(documents=chunks, ids=uuids)
    
    def extraer_especificaciones(self, data_json):
        model_name = data_json["model_name"]
        resultados = []

        for version, detalles in data_json["versions"].items():
            especificaciones = detalles.get("ESPECIFICACIONES MECÁNICAS Y TÉCNICAS", {})
            if not especificaciones:
                continue

            especificaciones_texto = []
            for key, value in especificaciones.items():
                # Normalizamos el valor "√" a "sí" y "-" a "no" si aplica
                if value.strip() == "√":
                    value = "sí"
                elif value.strip() == "-":
                    value = "no"
                especificaciones_texto.append(f"{key}: {value}")

            texto_final = (
                f"{model_name} {version} ESPECIFICACIONES MECÁNICAS Y TÉCNICAS "
                + ", ".join(especificaciones_texto) + "."
            )
            resultados.append(texto_final)

        return resultados
    
    def documents_create(self, resultados):

        documents = [
            Document(
                page_content=text,
                metadata={"source": f"list_item_{i}"}  # Add metadata as needed
            ) for i, text in enumerate(resultados)
        ]

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, 
            chunk_overlap=200, 
            add_start_index=True,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        splits = text_splitter.split_documents(documents)

        return splits
    
