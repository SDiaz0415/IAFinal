from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class VectorDBConnection(ABC):
    """
    Clase base abstracta para conexiones a bases de datos vectoriales
    (e.g., Pinecone, Weaviate, Milvus).

    Define una interfaz común para operaciones como conexión, inserción,
    consulta y desconexión.
    """

    def __init__(self, **kwargs): #, config: Dict[str, Any]
        """
        Inicializa la conexión con una configuración específica.
        La configuración variará según la base de datos.
        """
        self.config = kwargs
        self._vector_store = None
        self._is_connected = False

    @abstractmethod
    def connect(self):
        """
        Establece la conexión con la base de datos vectorial.
        Debe ser implementado por las subclases.
        """
        self._is_connected = True
        pass

    @abstractmethod
    def disconnect(self):
        """
        Cierra la conexión con la base de datos vectorial.
        Debe ser implementado por las subclases.
        """
        self._is_connected = False
        pass

    @abstractmethod
    def insert_vectors(self, index_name: str, vectors: List[Dict[str, Any]]):
        """
        Inserta vectores en un índice específico de la base de datos.

        Args:
            index_name (str): El nombre del índice donde se insertarán los vectores.
            vectors (List[Dict[str, Any]]): Una lista de diccionarios, donde cada diccionario
                                            representa un vector con sus metadatos.
                                            Ej: [{"id": "vec1", "values": [0.1, 0.2, ...], "metadata": {"key": "value"}}]
        """
        pass

    @abstractmethod
    def query_vectors(self, index_name: Optional[str] = None, user_query: str= "", top_k: int = 2, 
                      filter_criteria: Optional[Dict[str, Any]] = None) -> str:
        """
        Realiza una consulta de similitud de vectores en un índice específico.

        Args:
            index_name (str): El nombre del índice a consultar.
            query_vector (List[float]): El vector de consulta.
            top_k (int): El número de resultados más similares a retornar.
            filter_criteria (Optional[Dict[str, Any]]): Criterios de filtrado para los resultados.
                                                        (Ej: {"genre": "fantasy"})

        Returns:
            List[Dict[str, Any]]: Una lista de resultados, donde cada resultado es un diccionario
                                  con el id del vector, los valores (opcional) y los metadatos.
        """
        pass

    @abstractmethod
    def create_index(self, index_name: str, dimension: int, metric: str = "cosine"):
        """
        Crea un nuevo índice en la base de datos vectorial.

        Args:
            index_name (str): El nombre del índice a crear.
            dimension (int): La dimensión de los vectores en el índice.
            metric (str): La métrica de distancia a usar (e.g., "cosine", "euclidean", "dot_product").
        """
        pass

    @abstractmethod
    def delete_index(self, index_name: str):
        """
        Elimina un índice existente de la base de datos vectorial.

        Args:
            index_name (str): El nombre del índice a eliminar.
        """
        pass

    @abstractmethod
    def describe_index(self, index_name: str) -> Dict[str, Any]:
        """
        Obtiene una descripción del índice, incluyendo su estado, dimensión, etc.

        Args:
            index_name (str): El nombre del índice a describir.

        Returns:
            Dict[str, Any]: Un diccionario con la descripción del índice.
        """
        pass

    def __enter__(self):
        """Permite usar la clase con la declaración 'with'."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Asegura que la conexión se cierre al salir de la declaración 'with'."""
        self.disconnect()

    @property
    def is_connected(self) -> bool:
        """Indica si la conexión está activa."""
        return self._is_connected
    
    @property
    def get_vector_store(self):
        """Indica si la conexión está activa."""
        return self._vector_store 
    