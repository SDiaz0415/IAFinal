import weaviate
from weaviate.classes.init import Auth
import os
from weaviate.classes.config import Configure

#Read Only
# WEAVIATE_URL="lf7q3y8tzotv3z7utntlq.c0.us-west3.gcp.weaviate.cloud"
# WEAVIATE_API_KEY="sZ7zBZrQ5Zdo48R0mjgRPIJukAunqfWm8rWa"

#Admin
WEAVIATE_URL="lf7q3y8tzotv3z7utntlq.c0.us-west3.gcp.weaviate.cloud"
WEAVIATE_API_KEY="vzhBZ5BPvedzthoiY3eZ3XIn3KFJp3KJDZBz"

wcd_url = WEAVIATE_URL #os.getenv("WEAVIATE_URL")
wcd_key = WEAVIATE_API_KEY #os.getenv("WEAVIATE_API_KEY")

client = weaviate.connect_to_weaviate_cloud(
    cluster_url=wcd_url,                     # Weaviate URL: "REST Endpoint" in Weaviate Cloud console
    auth_credentials=Auth.api_key(wcd_key),  # Weaviate API key: "ADMIN" API key in Weaviate Cloud console
)

print(client.is_ready())  # Should print: `True`


# client.collections.create(
#     "DemoCollection",
#     vectorizer_config=[
#         Configure.NamedVectors.text2vec_weaviate(
#             name="title_vector",
#             source_properties=["title"],
#             model="Snowflake/snowflake-arctic-embed-l-v2.0",
#             # Further options
#             # dimensions=256
#             # base_url="<custom_weaviate_embeddings_url>",
#         )
#     ],
#     # Additional parameters not shown
# )



# source_objects = [
#     {"title": "The Shawshank Redemption", "description": "A wrongfully imprisoned man forms an inspiring friendship while finding hope and redemption in the darkest of places."},
#     {"title": "The Godfather", "description": "A powerful mafia family struggles to balance loyalty, power, and betrayal in this iconic crime saga."},
#     {"title": "The Dark Knight", "description": "Batman faces his greatest challenge as he battles the chaos unleashed by the Joker in Gotham City."},
#     {"title": "Jingle All the Way", "description": "A desperate father goes to hilarious lengths to secure the season's hottest toy for his son on Christmas Eve."},
#     {"title": "A Christmas Carol", "description": "A miserly old man is transformed after being visited by three ghosts on Christmas Eve in this timeless tale of redemption."}
# ]

# collection = client.collections.get("DemoCollection")

# with collection.batch.dynamic() as batch:
#     for src_obj in source_objects:
#         # The model provider integration will automatically vectorize the object
#         batch.add_object(
#             properties={
#                 "title": src_obj["title"],
#                 "description": src_obj["description"],
#             },
#             # vector=vector  # Optionally provide a pre-obtained vector
#         )
#         if batch.number_errors > 10:
#             print("Batch import stopped due to excessive errors.")
#             break

# failed_objects = collection.batch.failed_objects
# if failed_objects:
#     print(f"Number of failed imports: {len(failed_objects)}")
#     print(f"First failed object: {failed_objects[0]}")


collection = client.collections.get("DemoCollection")

response = collection.query.near_text(
    query="a movie with batman?",  # The model provider integration will automatically vectorize the query
    distance=0.6,
    limit=2,
)

for obj in response.objects:
    print(obj.properties["title"])



# Work with Weaviate

client.close()











# import faiss
# import numpy as np
# import json
# import os
# import pickle
# from sentence_transformers import SentenceTransformer
# from collections import defaultdict, Counter
# import re
# from pathlib import Path

# class EmbeddingStore:
#     def __init__(self):

#         # Construir la ruta relativa
#         data_path = str(Path(__file__).resolve().parent.parent / "data" / "data.json")
#         index_path = str(Path(__file__).resolve().parent.parent / "data" / "faiss_index.bin")
#         docs_path = str(Path(__file__).resolve().parent.parent / "data" / "docs.pkl")

#         """Inicializa el almacén de embeddings con la ruta al JSON"""
#         self.model = SentenceTransformer("all-mpnet-base-v2")
#         self.index = None
#         self.docs = []
#         self.technical_terms = set()
#         self.json_path = data_path #json_path
#         self.INDEX_FILE = index_path #"backend/data/faiss_index.bin"
#         self.DOCS_FILE = docs_path #"backend/data/docs.pkl"
#         self.load_or_create_index()

#     def load_or_create_index(self):
#         """Carga o crea el índice FAISS"""
#         if os.path.exists(self.INDEX_FILE) and os.path.exists(self.DOCS_FILE):
#             self.load_index()
#         else:
#             self.create_index()
#             if os.path.exists(self.json_path):
#                 self.load_json_data()

#     def create_index(self):
#         """Crea un nuevo índice FAISS"""
#         d = 768  # Dimensión del embedding
#         self.index = faiss.IndexFlatL2(d)
#         print("Índice FAISS creado exitosamente")

#     def load_index(self):
#         """Carga el índice desde disco"""
#         self.index = faiss.read_index(self.INDEX_FILE)
#         with open(self.DOCS_FILE, "rb") as f:
#             self.docs = pickle.load(f)
#         self._build_technical_vocabulary()
#         print(f"Índice cargado con {len(self.docs)} documentos")

#     def _build_technical_vocabulary(self):
#         """Extrae términos técnicos desde el JSON para mejorar la detección de preguntas técnicas."""
#         if not self.docs:
#             return

#         words = []
#         for doc in self.docs:
#             content = re.sub(r'^[^:]+:', '', doc).lower()
#             words.extend(re.findall(r'\b[a-záéíóúüñ]{4,}\b', content))

#         # Extraer términos desde el JSON procesado
#         json_terms = set()
#         with open(self.json_path, "r", encoding="utf-8") as f:
#             data = json.load(f)
#             def extract_keys(obj, prefix=""):
#                 if isinstance(obj, dict):
#                     for key, value in obj.items():
#                         json_terms.add(key.lower())
#                         extract_keys(value, f"{prefix}{key}_")
#                 elif isinstance(obj, list):
#                     for item in obj:
#                         extract_keys(item, prefix)
#             extract_keys(data)

#         # Agregar términos extraídos al vocabulario técnico
#         word_counts = Counter(words)
#         stopwords = {"verificar", "sistema", "datos", "valor"}
#         self.technical_terms = {
#             word for word, count in word_counts.items()
#             if count >= 2 and word not in stopwords
#         }
#         self.technical_terms.update(json_terms)  # Añadir términos del JSON

#         print(f"📌 Términos técnicos extraídos: {len(self.technical_terms)}")



#     def load_json_data(self):
#         """Carga y procesa los datos del JSON especificado en el constructor"""
#         try:
#             with open(self.json_path, "r", encoding="utf-8") as f:
#                 data = json.load(f)
            
#             fragmentos = self.procesar_json(data)
#             self.add_documents(fragmentos)
#             print(f"✅ Documentos indexados: {len(self.docs)}")
#             return True
            
#         except Exception as e:
#             print(f"❌ Error al cargar JSON: {str(e)}")
#             return False

#     def procesar_json(self, data):
#         """Procesa el JSON para extraer fragmentos técnicos"""
#         fragmentos = []
        
#         def extract_values(obj, path=""):
#             if isinstance(obj, dict):
#                 for k, v in obj.items():
#                     new_path = f"{path}.{k}" if path else k
#                     extract_values(v, new_path)
#             elif isinstance(obj, list):
#                 for item in obj:
#                     extract_values(item, path)
#             elif isinstance(obj, (int, float, str)):
#                 if isinstance(obj, (int, float)) or (str(obj).strip() and len(str(obj).strip()) > 1):
#                     fragmentos.append(f"{path}: {obj}")  # Asegurar que todo se indexe

#         extract_values(data)
#         return fragmentos



#     def add_documents(self, texts):
#         """Añade documentos al índice"""
#         if not texts:
#             return
            
#         embeddings = self.model.encode(texts, convert_to_numpy=True)
#         self.index.add(embeddings.astype('float32'))
#         self.docs.extend(texts)
#         self._build_technical_vocabulary()
#         self.save_index()

#     def save_index(self):
#         """Guarda el índice en disco"""
#         faiss.write_index(self.index, self.INDEX_FILE)
#         with open(self.DOCS_FILE, "wb") as f:
#             pickle.dump(self.docs, f)

#     def is_technical_question(self, question):
#         """Determina si la pregunta es técnica en función de los términos extraídos del JSON."""
#         question = question.lower()
#         question_terms = set(re.findall(r'\b[a-záéíóúüñ]{4,}\b', question))

#         # Verificar si la pregunta contiene términos técnicos extraídos
#         if question_terms & self.technical_terms:
#             return True

#         # Extraer patrones de preguntas técnicas desde las claves del JSON
#         common_patterns = {key.replace("_", " ") for key in self.technical_terms if len(key) > 3}

#         if any(pattern in question for pattern in common_patterns):
#             return True

#         return False

#     def preprocess_query(self, query):
#         """Normaliza y expande la consulta para mejorar la búsqueda."""
#         query = query.lower().strip()

#         # Expansión de sinónimos
#         synonyms = {
#             "potencia": ["kw", "kilovatios", "capacidad"],
#             "corriente": ["amperaje", "amperios"],
#             "tensión": ["voltaje", "v"],
#             "resistencia": ["ohmios", "Ω"],
#             "velocidad": ["rpm"]
#         }

#         expanded_query = []
#         for word in query.split():
#             expanded_query.append(word)
#             if word in synonyms:
#                 expanded_query.extend(synonyms[word])

#         # Corrección de errores ortográficos simples
#         typo_corrections = {
#             "potenzia": "potencia",
#             "voltage": "tensión",
#             "amperage": "corriente"
#         }
#         expanded_query = [typo_corrections.get(word, word) for word in expanded_query]

#         return " ".join(expanded_query)

#     def search(self, question, top_k=5):
#         """
#         Busca en los embeddings solo si es pregunta técnica.
#         Devuelve lista vacía para preguntas generales o consultas sin relación con los datos.
#         """
#         if not self.is_technical_question(question):
#             return []

#         question = self.preprocess_query(question)

#         # 🚨 Filtro semántico antes de buscar
#         if not any(term in question for term in self.technical_terms):
#             return []

#         query_embedding = self.model.encode([question])
#         distances, indices = self.index.search(query_embedding.astype('float32'), top_k)

#         results = [(self.docs[idx], distances[0][i]) for i, idx in enumerate(indices[0]) if idx < len(self.docs)]

#         # Aplicar filtro de relevancia con la consulta como parámetro
#         results = self._apply_relevance_boost(results, question)

#         # 🚨 Excluir `palabras_clave` y `serie` en preguntas generales
#         if not self.is_technical_question(question):
#             results = [
#                 doc for doc in results
#                 if "palabras_clave" not in doc.lower() and "serie" not in doc.lower() and "n.i" not in doc.lower()
#             ]

#         return results


#     def _get_document_weight(self, doc_tuple):
#         """
#         Asigna un peso a cada documento basado en su contenido o metadatos.
#         Puede ajustarse según reglas específicas de negocio.
#         """
#         doc = doc_tuple[0]  # Extrae el documento de la tupla

#         # Caso base: peso por defecto
#         weight = 1.0

#         # Si el documento tiene ciertas palabras clave, aumentar el peso
#         keywords = ["alta tension", "prueba eléctrica", "revisión", "mantenimiento"]
#         if any(keyword in doc.lower() for keyword in keywords):
#             weight = 0.8  # Mayor prioridad a pruebas eléctricas y mantenimiento

#         # Si el documento es una recomendación, reducir su peso (ejemplo)
#         if "recomendaciones_generales" in doc.lower():
#             weight = 1.2  # Se considera menos prioritario que los datos técnicos

#         return weight


#     def _apply_relevance_boost(self, results, query):
#         """Prioriza valores técnicos clave y evita responder preguntas generales."""
#         boosted_results = []

#         FIELD_WEIGHTS = {
#             'potencia_kw': 10.0,  # Aumentar prioridad de la potencia
#             'tensión': 3.0, 'corriente': 3.0,
#             'resistencia': 3.0, 'prueba': 2.0, 'falla': 1.8,
#             'ajuste': 1.8, 'velocidad': 1.5, 'rpm': 1.5,
#             'trabajos_realizados': 0.3
#         }

#         # Lista de términos técnicos válidos en el índice
#         TECHNICAL_TERMS = [
#             "potencia", "kw", "tensión", "corriente", "resistencia",
#             "prueba", "falla", "ajuste", "velocidad", "rpm",
#             "aislamiento", "motor", "ventilador", "tierra", "impulso"
#         ]

#         # 🚨 Si la consulta no contiene términos técnicos, detener la búsqueda
#         if not any(term in query.lower() for term in TECHNICAL_TERMS):
#             return []

#         for doc, score in results:
#             weight = 1.0  

#             # Aplicar pesos según campos técnicos encontrados
#             for field, field_weight in FIELD_WEIGHTS.items():
#                 if field in doc.lower():
#                     weight *= field_weight
#                     break

#             boosted_results.append((doc, score / weight))

#         boosted_results.sort(key=lambda x: x[1])

#         # 🚨 Filtro especial para la pregunta de potencia
#         if "potencia" in query and "kw" in query:
#             filtered_results = [doc for doc, _ in boosted_results if "potencia_kw" in doc.lower()]
#             if filtered_results:
#                 return filtered_results  

#         # Filtrar respuestas débiles (evitar palabras clave sin contexto)
#         filtered_results = [doc for doc, _ in boosted_results if "palabras_clave" not in doc.lower()]

#         return filtered_results if filtered_results else []


#     def display_results(self, question, results):
#         """Muestra los resultados de búsqueda"""
#         if not results:
#             print(f"\n🔍 No se encontraron resultados técnicos para: '{question}'")
#             print("ℹ️ Esta parece ser una pregunta general o no relacionada con los datos técnicos")
#             return
        
#         print(f"\n🔍 Resultados técnicos para: '{question}'\n")
#         for i, doc in enumerate(results, 1):
#             print(f"{i}. {doc}")


# if __name__ == "__main__":
#     # Opción 1 (con JSON por defecto "data.json"):
#     store = EmbeddingStore()  
#     # store.load_json_data()


#     # preguntas_tecnicas = [
#     # "¿Cuál es la potencia en kw del motor?",
#     # "¿Cuáles fueron los trabajos realizados en la reparación?",
#     # "¿Qué pruebas eléctricas se realizaron?",
#     # "¿Cuál fue la resistencia de aislamiento a tierra en GΩ?",
#     # "¿Cuál es la velocidad en RPM del motor en vacío?",
#     # "¿Qué recomendaciones generales se dieron para el mantenimiento del motor?",
#     # "¿Qué pruebas de alta tensión se realizaron?",
#     # "¿Cuál es la tensión de prueba en la prueba de impulso?",
#     # "¿Qué tipo de ajuste se hizo en el ventilador?",
#     # "¿Qué fallas se encontraron en el equipo?"
#     # ]

#     # preguntas_generales = [
#     #     "¿Qué hora es en París?",
#     #     "¿Quién ganó el último mundial de fútbol?",
#     #     "¿Cómo está el clima hoy?",
#     #     "¿Cuál es la capital de Francia?",
#     #     "¿Quién es el presidente de Estados Unidos?",
#     #     "¿Cómo hacer una pizza casera?",
#     #     "¿Cuánto es 2+2?",
#     #     "¿Qué significa la palabra 'resiliencia'?",
#     #     "¿Dónde queda el Monte Everest?",
#     #     "¿Cuál es la mejor serie de Netflix?",
#     #     "como esta el clima en Cali, Colombia?"
#     # ]

#     # # Probar preguntas técnicas
#     # print("\n🔍 **Pruebas con preguntas técnicas**")
#     # for pregunta in preguntas_tecnicas:
#     #     resultados = store.search(pregunta)
#     #     store.display_results(pregunta, resultados)

#     # # Probar preguntas generales
#     # print("\n🔍 **Pruebas con preguntas generales**")
#     # for pregunta in preguntas_generales:
#     #     resultados = store.search(pregunta)
#     #     store.display_results(pregunta, resultados)