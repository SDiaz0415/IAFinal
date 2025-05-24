# import pinecone  # pip install pinecone-client
from typing import List, Dict, Any, Optional
from app.embeddings.service import VectorDBConnection 

####DB connection
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from langchain_ollama import OllamaEmbeddings
# from pymilvus import MilvusClient
# from pymilvus import DataType


class QdrantConnection(VectorDBConnection):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(**config)
        self.api_key = config.get("api_key")
        self.end_point = config.get("end_point")
        self.collection_name = config.get("collection_name")
        self.embeddings = OllamaEmbeddings(model=config.get("embeddings"))

    def connect(self):
        try:            
            ####Strat langchain client milvus
            client = QdrantClient(
                url=self.end_point, 
                api_key=self.api_key,
            )

            # Crear colección si no existe
            # Calcular dimensión del embedding dinámicamente
            embedding_dim = len(self.embeddings.embed_query("test"))

            collection_name = self.collection_name
            existing_collections = [c.name for c in client.get_collections().collections]
            if collection_name not in existing_collections:
                client.recreate_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=embedding_dim, distance=Distance.COSINE)
                )

            self._vector_store = QdrantVectorStore(
                client=client,
                collection_name=self.collection_name,
                embedding=self.embeddings,
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

        except Exception as e:
            print(f"Error durante la consulta de vectores: {e}")
            raise

    def create_index(self, index_name: str, dimension: int, metric: str = "cosine"):
        if not self._is_connected:
            raise ConnectionError("No conectado a Pinecone. Llama a .connect() primero.")
        try:
            pass

        except Exception as e:
            print(f"Error al crear índice en Pinecone: {e}")
            raise

    def delete_index(self, index_name: str):
        if not self._is_connected:
            raise ConnectionError("No conectado a Pinecone. Llama a .connect() primero.")
        try:
            pass

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
 
        except Exception as e:
            print(f"Error al describir índice en Pinecone: {e}")
            raise
    
    