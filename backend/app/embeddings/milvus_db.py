# import pinecone  # pip install pinecone-client
from typing import List, Dict, Any, Optional
from app.embeddings.service import VectorDBConnection 

####DB connection
from langchain_milvus import Milvus
from langchain_ollama import OllamaEmbeddings
from pymilvus import utility, MilvusClient, DataType
# from pymilvus import MilvusClient
# from pymilvus import DataType


class MilvusConnection(VectorDBConnection):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(**config)
        self.api_key = config.get("api_key")
        self.end_point = config.get("end_point")
        self.collection_name = config.get("collection_name")
        self.embeddings = OllamaEmbeddings(model=config.get("embeddings"))

    def connect(self):
        try:
            # MilvusClient(uri=self.end_point, token=self.api_key,)
            
            # ####Create collection
            # ####Get client 
            # client = MilvusClient(uri=self.end_point, token=self.api_key)
            # exists = client.has_collection(self.collection_name)
            # if not exists:
            #     # Create schema
            #     schema = MilvusClient.create_schema(
            #         auto_id=False,
            #         enable_dynamic_field=True,
            #     )

            #     # Add fields to schema
            #     schema.add_field(field_name="id", datatype=DataType.VARCHAR, max_length=36, is_primary=True)
            #     schema.add_field(field_name="vector", datatype=DataType.FLOAT_VECTOR, dim=1536)  # Adjust dimension based on your embeddings
            #     schema.add_field(field_name="metadata", datatype=DataType.JSON, nullable=True,)
            #     schema.add_field(field_name="text", datatype=DataType.VARCHAR, nullable=True, max_length=65535)

            #     # Prepare index parameters
            #     index_params = client.prepare_index_params()
            #     index_params.add_index(
            #         field_name="vector",
            #         index_type="AUTOINDEX",
            #         metric_type="COSINE"
            #     )

            #     # Create collection
            #     client.create_collection(
            #         collection_name=self.collection_name,
            #         schema=schema,
            #         index_params=index_params
            #     )

            
            ####Strat langchain client milvus
            self._vector_store = Milvus(
                embedding_function=self.embeddings,
                collection_name=self.collection_name,
                connection_args={
                    "uri": self.end_point,
                    "token": self.api_key,
                },
                drop_old=False,  # Drop the old Milvus collection if it exists
            )
            self._is_connected = True

  

            print(f"Connected to DB: successfully")
        except Exception as e:
            print(f"Error al conectar a Milvus: {e}")
            self._is_connected = False
            raise

    def disconnect(self):
        # Milvus client doesn't have a direct 'disconnect' method in its SDK,
        # but you might want to clear resources or set connection status.
        # For simplicity, we just mark as disconnected.
        self._is_connected = False
        self._vector_store = None
        print("Desconectado de Milvus (lógicamente) y borrar instancia.")

    def insert_vectors(self, index_name: str, vectors: List[Dict[str, Any]]):
        if not self._is_connected:
            raise ConnectionError("No conectado a Milvus. Llama a .connect() primero.")
        try:
            pass
            # index = pinecone.Index(index_name)
            # # Pinecone's upsert expects a list of (id, vector_values, metadata) tuples
            # formatted_vectors = [(v["id"], v["values"], v.get("metadata", {})) for v in vectors]
            # index.upsert(vectors=formatted_vectors)
            # print(f"Insertados {len(vectors)} vectores en el índice '{index_name}' de Pinecone.")
        except Exception as e:
            print(f"Error al insertar vectores en Pinecone: {e}")
            raise

    def query_vectors(self, index_name: Optional[str] = None, user_query: str= "", top_k: int = 2, 
                      filter_criteria: Optional[Dict[str, Any]] = None) -> str:
        if not self._is_connected:
            raise ConnectionError("No conectado a Pinecone. Llama a .connect() primero.")
        try:
            
            retrieved_docs = self._vector_store.similarity_search(user_query, k=top_k)
            serialized = "\n\n".join(
                f"[Página: {doc.metadata.get('page', 'N/A')}]\n{doc.page_content}"
                for doc in retrieved_docs
            )
            print("Query context got it")
            return serialized

            # index = pinecone.Index(index_name)
            # query_results = index.query(
            #     vector=query_vector,
            #     top_k=top_k,
            #     filter=filter_criteria, # Pinecone accepts dictionary for filters
            #     include_values=True, # Include actual vector values in results
            #     include_metadata=True # Include metadata in results
            # )
            # results = []
            # for match in query_results.matches:
            #     results.append({
            #         "id": match.id,
            #         "score": match.score,
            #         "values": match.values,
            #         "metadata": match.metadata
            #     })
            # return results
        except Exception as e:
            print(f"Error durante la consulta de vectores: {e}")
            raise

    def create_index(self, index_name: str, dimension: int, metric: str = "cosine"):
        if not self._is_connected:
            raise ConnectionError("No conectado a Pinecone. Llama a .connect() primero.")
        try:
            pass
            # if index_name not in pinecone.list_indexes():
            #     pinecone.create_index(index_name, dimension=dimension, metric=metric)
            #     print(f"Índice '{index_name}' creado en Pinecone.")
            # else:
            #     print(f"El índice '{index_name}' ya existe en Pinecone.")
        except Exception as e:
            print(f"Error al crear índice en Pinecone: {e}")
            raise

    def delete_index(self, index_name: str):
        if not self._is_connected:
            raise ConnectionError("No conectado a Pinecone. Llama a .connect() primero.")
        try:
            pass
            # if index_name in pinecone.list_indexes():
            #     pinecone.delete_index(index_name)
            #     print(f"Índice '{index_name}' eliminado de Pinecone.")
            # else:
            #     print(f"El índice '{index_name}' no existe en Pinecone.")
        except Exception as e:
            print(f"Error al eliminar índice en Pinecone: {e}")
            raise

    def describe_index(self, index_name: str) -> Dict[str, Any]:
        if not self._is_connected:
            raise ConnectionError("No conectado a Pinecone. Llama a .connect() primero.")
        try:
            # Pinecone does not have a direct describe_index call that returns
            # all metadata in one go from the main client.
            # You might need to query the index stats or use list_indexes to get some info.
            # This is a simplified example.
            pass
            # if index_name in pinecone.list_indexes():
            #     index_stats = pinecone.Index(index_name).describe_index_stats()
            #     return {
            #         "name": index_name,
            #         "dimension": index_stats["dimension"],
            #         "namespaces": index_stats["namespaces"]
            #         # Add more relevant stats as needed
            #     }
            # else:
            #     return {"error": f"El índice '{index_name}' no existe."}
        except Exception as e:
            print(f"Error al describir índice en Pinecone: {e}")
            raise
    
    