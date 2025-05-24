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

#####Good ONE
    def extraer_especificaciones(self, data_json):
        model_name = data_json["model_name"]
        resultados = []

        for version, detalles in data_json["versions"].items():
            # Try to get specifications from common possible section names
            especificaciones = detalles.get("ESPECIFICACIONES MECÁNICAS Y TÉCNICAS", None)
            if especificaciones is None: # If the first key wasn't found, try the other common key
                especificaciones = detalles.get("ESPECIFICACIONES TECNICAS", {}) # Default to empty dict if not found

            if not especificaciones: # If still no specifications found for this version, skip it
                continue

            especificaciones_texto = []
            for key, value in especificaciones.items():
                # Normalizamos el valor "√" a "sí" y "-" a "no" si aplica
                cleaned_value = value.strip() # Clean the value once
                if cleaned_value == "√":
                    value_to_append = "sí"
                elif cleaned_value == "-":
                    value_to_append = "no"
                else:
                    value_to_append = cleaned_value # Use the cleaned value if not a symbol

                especificaciones_texto.append(f"{key}: {value_to_append}")

            if especificaciones_texto: # Ensure there's something to join
                texto_final = (
                    f"{model_name} {version} "
                    # Determine the correct section title for the output string
                    f"{'ESPECIFICACIONES MECÁNICAS Y TÉCNICAS' if 'ESPECIFICACIONES MECÁNICAS Y TÉCNICAS' in detalles else 'ESPECIFICACIONES TECNICAS'} "
                    + ", ".join(especificaciones_texto) + "."
                )
                resultados.append(texto_final)

        return resultados
   
    # def extraer_especificaciones(self, data_json):
    #     model_name = data_json["model_name"]
    #     resultados = []

    #     for version, detalles in data_json["versions"].items():
    #         especificaciones = detalles.get("ESPECIFICACIONES MECÁNICAS Y TÉCNICAS", {})
    #         if not especificaciones:
    #             continue

    #         especificaciones_texto = []
    #         for key, value in especificaciones.items():
    #             # Normalizamos el valor "√" a "sí" y "-" a "no" si aplica
    #             if value.strip() == "√":
    #                 value = "sí"
    #             elif value.strip() == "-":
    #                 value = "no"
    #             especificaciones_texto.append(f"{key}: {value}")

    #         texto_final = (
    #             f"{model_name} {version} ESPECIFICACIONES MECÁNICAS Y TÉCNICAS "
    #             + ", ".join(especificaciones_texto) + "."
    #         )
    #         resultados.append(texto_final)

    #     return resultados
    
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
    
