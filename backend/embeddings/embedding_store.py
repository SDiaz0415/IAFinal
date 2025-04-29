import os
import json
from datetime import datetime
import weaviate 
from weaviate.classes.init import Auth 
from weaviate.classes.config import Property, DataType, Configure
from weaviate.classes.query import Filter, MetadataQuery, HybridFusion
# from dotenv import load_dotenv
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from datetime import datetime
import re
from transformers import AutoTokenizer, T5Tokenizer, AutoModelForSeq2SeqLM, pipeline, MT5ForConditionalGeneration
import torch 
# from sentence_transformers import SentenceTransformer, util

# Configuración inicial
# load_dotenv()
# WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")
# WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY", "")
WEAVIATE_URL="lf7q3y8tzotv3z7utntlq.c0.us-west3.gcp.weaviate.cloud"
WEAVIATE_API_KEY="vzhBZ5BPvedzthoiY3eZ3XIn3KFJp3KJDZBz"
INPUT_FOLDER = str(Path(__file__).resolve().parent.parent / "data")
OUTPUT_FOLDER = str(Path(__file__).resolve().parent.parent / "data" / "informes_transformados")
CLASS_NAME = 'InformesMotores'
STOPWORDS = {"se", "de", "la", "el", "en", "del", "una", "un", "lo", "al", "que", "tipo", "con", "archivos"}
PROPIEDADES = {
    "marca": {"tipo": "texto", "claves": ["marca", "fabricante"]},
    "tipoFalla": {"tipo": "texto", "claves": ["falla", "problema", "avería"]},
    "tipoServicio": {"tipo": "texto", "claves": ["servicio", "mantenimiento"]},
    "cliente": {"tipo": "texto", "claves": ["cliente", "empresa"]},
    "estadoReparacion": {"tipo": "texto", "claves": ["estado", "reparación"]},
    "potencia": {"tipo": "unidad", "claves": ["potencia"]},
    "tension": {"tipo": "unidad", "claves": ["tensión", "voltaje"]},
    "fechaInicio": {"tipo": "fecha", "claves": ["fecha", "inicio", "fechaInicio"]},
}
VALORES_INVALIDOS = {"motor", "equipo", "máquina", "sistema"}
UNIDADES = {
    "potencia": {"hp", "kw", "kilowatts", "caballos"},
    "tension": {"v", "voltios", "voltaje"}
}

# Configuración del cliente Weaviate
client = weaviate.connect_to_weaviate_cloud(
    cluster_url=WEAVIATE_URL,                     # Weaviate URL: "REST Endpoint" in Weaviate Cloud console
    auth_credentials=Auth.api_key(WEAVIATE_API_KEY),  # Weaviate API key: "ADMIN" API key in Weaviate Cloud console
)

# Carga un modelo especializado para reformular queries
model_name = "unicamp-dl/mmarco-mMiniLMv2-L6-H384-v1" #'BeIR/query-gen-multilingual-t5-base'
tokenizer  =  AutoTokenizer.from_pretrained(model_name)
model      = MT5ForConditionalGeneration.from_pretrained(model_name)
# tokenizer = AutoTokenizer.from_pretrained("unicamp-dl/mt5-base-mmarco-pt-msmarco")
# model = AutoModelForSeq2SeqLM.from_pretrained("unicamp-dl/mt5-base-mmarco-pt-msmarco")
# tokenizer = AutoTokenizer.from_pretrained("BeIR/query-gen-msmarco-t5-base-v1", use_fast=False)
# model = AutoModelForSeq2SeqLM.from_pretrained("BeIR/query-gen-msmarco-t5-base-v1")


generator = pipeline("text2text-generation", model=model, tokenizer=tokenizer)

def crear_esquema_weaviate():
    try:
        # Obtener la lista de colecciones existentes
        existing_collections = client.collections.list_all()

        # Verificar si la colección ya existe
        if CLASS_NAME in existing_collections:
            print("ℹ️ Esquema ya existe en Weaviate")
        else:
            # Crear la colección
            client.collections.create(
                name=CLASS_NAME,
                properties=[
                    Property(name="archivo", data_type=DataType.TEXT),
                    Property(name="marca", data_type=DataType.TEXT, index_inverted=True),
                    Property(name="potencia", data_type=DataType.TEXT, index_inverted=True),
                    Property(name="tension", data_type=DataType.TEXT, index_inverted=True),
                    Property(name="corriente", data_type=DataType.TEXT, index_inverted=True),
                    
                    # Servicio
                    Property(name="tipoServicio", data_type=DataType.TEXT, index_inverted=True),
                    Property(name="descripcionServicio", data_type=DataType.TEXT),
                    Property(name="procedimientosServicio", data_type=DataType.TEXT_ARRAY),  # Para búsqueda híbrida (ej: por paso)

                    # Pruebas
                    # Property(name="resultadoPruebasElectricas", data_type=DataType.TEXT),
                    # Property(name="resultadoPruebasMecanicas", data_type=DataType.TEXT),
                    # Property(name="temperaturaOperacion", data_type=DataType.TEXT),
                    # Property(name="datosSensores", data_type=DataType.TEXT),

                    # Recomendaciones
                    Property(name="recomendacionesGenerales", data_type=DataType.TEXT_ARRAY),
                    Property(name="recomendacionesEspecificas", data_type=DataType.TEXT_ARRAY),

                    # Otros metadatos
                    Property(name="cliente", data_type=DataType.TEXT, index_inverted=True),
                    Property(name="tipoFalla", data_type=DataType.TEXT, index_inverted=True),
                    Property(name="estadoReparacion", data_type=DataType.TEXT, index_inverted=True),
                    Property(name="fechaInicio", data_type=DataType.DATE, index_inverted=True),
                    Property(name="fechaFin", data_type=DataType.DATE, index_inverted=True),
                    Property(name="normativas", data_type=DataType.TEXT_ARRAY),
                    # Property(name="repuestos", data_type=DataType.TEXT_ARRAY),

                    # Campo para recuperación semántica integral
                    Property(name="textoCompleto", data_type=DataType.TEXT)


                    # Property(name="archivo", data_type=DataType.TEXT),
                    # Property(
                    #     name="datosTecnicos",
                    #     data_type=DataType.OBJECT,
                    #     nested_properties=[
                    #         Property(name="potencia", data_type=DataType.TEXT),
                    #         Property(name="voltaje", data_type=DataType.TEXT),
                    #         Property(name="corriente", data_type=DataType.TEXT)
                    #     ]
                    # ),
                    # Property(
                    #     name="servicio",
                    #     data_type=DataType.OBJECT,
                    #     nested_properties=[
                    #         Property(name="tipo", data_type=DataType.TEXT),
                    #         Property(name="descripcion", data_type=DataType.TEXT)
                    #     ]
                    # ),
                    # Property(
                    #     name="pruebas",
                    #     data_type=DataType.OBJECT,
                    #     nested_properties=[
                    #         Property(name="nombre", data_type=DataType.TEXT),
                    #         Property(name="resultado", data_type=DataType.TEXT)
                    #     ]
                    # ),
                    # Property(
                    #     name="repuestos",
                    #     data_type=DataType.OBJECT_ARRAY,
                    #     nested_properties=[
                    #         Property(name="nombre", data_type=DataType.TEXT),
                    #         Property(name="cantidad", data_type=DataType.NUMBER)
                    #     ]
                    # ),
                    # Property(
                    #     name="fechasClave",
                    #     data_type=DataType.OBJECT,
                    #     nested_properties=[
                    #         Property(name="inicio", data_type=DataType.DATE),
                    #         Property(name="fin", data_type=DataType.DATE)
                    #     ]
                    # ),
                    # Property(
                    #     name="recomendaciones",
                    #     data_type=DataType.OBJECT,
                    #     nested_properties=[
                    #         Property(name="generales", data_type=DataType.TEXT_ARRAY),
                    #         Property(name="especificas", data_type=DataType.TEXT_ARRAY)
                    #     ]
                    # ),
                    # Property(name="normativas", data_type=DataType.TEXT_ARRAY, index_inverted=True),
                    # Property(name="cliente", data_type=DataType.TEXT, index_inverted=True),
                    # Property(name="tipoFalla", data_type=DataType.TEXT, index_inverted=True),
                    # Property(name="estadoReparacion", data_type=DataType.TEXT, index_inverted=True),
                    # Property(name="textoCompleto", data_type=DataType.TEXT)
                ],
                vectorizer_config=[
                    Configure.NamedVectors.text2vec_weaviate(
                        name="textoCompleto_vector",
                        source_properties=[
                            "archivo"
                            "marca"
                            "potencia"
                            "tension"
                            "corriente"
                            "tipoServicio"
                            "descripcionServicio"
                            "procedimientosServicio"
                            "recomendacionesGenerales"
                            "recomendacionesEspecificas"
                            "cliente"
                            "tipoFalla"
                            "estadoReparacion"
                            "fechaInicio"
                            "fechaFin"
                            "normativas"
                            "textoCompleto"
                        ],
                        model="Snowflake/snowflake-arctic-embed-l-v2.0"
                    )
                ]
            )

            print("✅ Esquema creado en Weaviate")
    except Exception as e:
        client.close()
        print(f"❌ Error: {e}")



def estandarizar_fecha(fecha_str: str) -> Optional[str]:
    """Convierte diferentes formatos de fecha a ISO 8601"""
    if not fecha_str:
        return None
    
    try:
        # Formato "12 de Diciembre de 2023"
        if "de" in fecha_str:
            meses = {
                'Enero': '01', 'Febrero': '02', 'Marzo': '03', 'Abril': '04',
                'Mayo': '05', 'Junio': '06', 'Julio': '07', 'Agosto': '08',
                'Septiembre': '09', 'Octubre': '10', 'Noviembre': '11', 'Diciembre': '12'
            }
            partes = [p.strip() for p in fecha_str.split("de")]
            if len(partes) == 3:
                dia, mes, anio = partes
                mes_num = meses.get(mes.capitalize(), '01')
                return f"{anio}-{mes_num}-{dia.zfill(2)}"
        
        # Formato "04/12/23"
        elif "/" in fecha_str and len(fecha_str.split("/")[2]) == 2:
            dia, mes, anio = fecha_str.split("/")
            return f"20{anio}-{mes.zfill(2)}-{dia.zfill(2)}"
        
        # Formato ISO básico
        return datetime.strptime(fecha_str, "%Y-%m-%d").date().isoformat()
    except:
        return None

def extraer_datos_tecnicos(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Extrae y estandariza los datos técnicos del motor"""
    datos_placa = doc.get("datos_placa", {})
    electricas = datos_placa.get("caracteristicas_electricas", {})
    mecanicas = datos_placa.get("caracteristicas_mecanicas", {})
    info_general = doc.get("informacion_general", {})
    lv_potencia = lv_equipo = lv_id_equipo = lv_modelo = ""
    lv_id_maquina = ""

    """Extrae la potencia"""
    if isinstance(datos_placa.get("potencia"), dict):
        lv_potencia = f"{datos_placa['potencia'].get('valor', '')} {datos_placa['potencia'].get('unidad', '')}".strip()
    elif isinstance(datos_placa.get("potencia"), str):
        lv_potencia = f"{datos_placa.get('potencia', '')}".strip() 
    
    """Extrae el equipo"""
    if isinstance(info_general.get("equipo"), dict):
        lv_equipo = info_general.get('equipo', {}).get('tipo', '').strip()
        lv_id_equipo = info_general.get("equipo", {}).get("identificacion", "")
    elif isinstance(info_general.get("equipo"), str):
        lv_equipo = info_general.get('equipo', '').strip()
    elif isinstance(info_general.get("tipo_equipo"), str):
        lv_equipo = info_general.get('tipo_equipo', '').strip()
    
    """Extrae Id de la placa"""
    if isinstance(datos_placa.get("identificacion"), dict):
        lv_modelo = datos_placa.get("identificacion", {}).get("serie", "No especificado").strip()
        lv_id_maquina = datos_placa.get("identificacion", {}).get("maquina_asociada", "").strip()
    elif isinstance(datos_placa.get("identificacion"), str):
        lv_modelo = datos_placa.get("identificacion", '').strip() 
    elif isinstance(datos_placa.get("maquina_asociada"), str):
        lv_id_maquina = datos_placa.get("maquina_asociada", '').strip()

        
    
    return {
        "marca": datos_placa.get("marca", "No informado"),
        "modelo": lv_modelo, #datos_placa.get("identificacion", {}).get("serie", "No especificado"),
        "potencia": lv_potencia,
        "tension": electricas.get("tension", datos_placa.get("tension", "")),
        "corriente": electricas.get("corriente", datos_placa.get("corriente", "")),
        "frecuencia": electricas.get("frecuencia", datos_placa.get("frecuencia", "")),
        "fases": electricas.get("fases", datos_placa.get("fases", "")),
        "rpm": mecanicas.get("rpm", datos_placa.get("rpm", "")),
        "frame": mecanicas.get("frame", datos_placa.get("frame", "")),
        "proteccion": mecanicas.get("proteccion", datos_placa.get("grado_proteccion", "")),
        "claseAislamiento": electricas.get("clase_aislamiento", datos_placa.get("clase_aislamiento", "")),
        # "tempMaxima": electricas.get("temperatura_maxima", ""),
        "maquinaAsociada": lv_id_maquina, #datos_placa.get("identificacion", {}).get("maquina_asociada", ""),
        "tipoEquipo": lv_equipo, #info_general.get("equipo", {}).get("tipo", ""),
        "identificacionEquipo": lv_id_equipo
    }

def transformar_servicio(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Transforma la información del servicio realizado"""
    servicio = doc.get("servicio", {})
    diagnostico = servicio.get("diagnostico_falla", {})
    
    
    return {
        "tipo": servicio.get("tipo", ""),
        "descripcion": servicio.get("descripcion", ""),
        "procedimientos": servicio.get("procedimientos", servicio.get("trabajos_realizados", [])), #servicio.get("procedimientos" || "trabajos_realizados", []),
        "diagnostico": {
            "tipoFalla": diagnostico.get("tipo", servicio.get("tipo_falla", '')),
            "descripcionFalla": diagnostico.get("descripcion", ""),
            "causaRaiz": doc.get("analisis_falla", {}).get("causa_raiz", "")  # Extrae de análisis_falla si existe
        }
    }

def transformar_pruebas(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Transforma los resultados de las pruebas"""
    pruebas = doc.get("pruebas", {})
    electricas = pruebas.get("electricas", {})
    mecanicas = pruebas.get("mecanicas", {})
    
    # Procesar prueba de vacío
    prueba_vacio = electricas.get("vacio", {})
    parametros_vacio = prueba_vacio.get("parametros", [])
    tensiones = [f"{p['tension']}V" for p in parametros_vacio if isinstance(p, dict)]
    corrientes = [f"{p['corriente']}A" for p in parametros_vacio if isinstance(p, dict)]
    
    return {
        "electricas": {
            "aislamientoTierra": f"{electricas.get('aislamiento_tierra', {}).get('resistencia', '')} (Mínimo: {electricas.get('aislamiento_tierra', {}).get('estandar', {}).get('alambre_redondo', '')})",
            "altaTension": f"{electricas.get('alta_tension', {}).get('resultado', '')} ({electricas.get('alta_tension', {}).get('tension_prueba', '')})",
            "impulso": "OK" if all(r == "OK" for r in electricas.get('impulso', {}).get('resultados', {}).values()) else "Fallo",
            "pruebaVacio": f"Tensión: {', '.join(tensiones)}, Corriente: {', '.join(corrientes)}"
        },
        "mecanicas": {
            "vibracion": "Ajustes dentro de rango" if all(
                p.get("ajuste_final", "") != "-" 
                for p in mecanicas.get("vibracion", {}).get("parametros", [])
            ) else "Ajustes requeridos",
            "temperatura": {
                "rodamientoLC": mecanicas.get("temperatura", {}).get("lecturas", {}).get("rodamiento_LC", ""),
                "carcasa": mecanicas.get("temperatura", {}).get("lecturas", {}).get("carcasa", ""),
                "cumpleLimites": True  # Asumimos que cumple si no hay observaciones
            }
        },
        "equiposUtilizados": list(set([
            electricas.get("aislamiento_tierra", {}).get("equipo", ""),
            electricas.get("alta_tension", {}).get("equipo", ""),
            mecanicas.get("vibracion", {}).get("equipo", ""),
            mecanicas.get("temperatura", {}).get("equipo", "")
        ]))
    }
def transformar_repuestos(doc: Dict[str, Any]) -> Dict[str, Any]:
    repuestos_raw = doc.get("repuestos", [])
    repuestos_normalizados = []
    
    if isinstance(repuestos_raw, dict):  # Caso de diccionario con "descripcion"
        repuestos_raw = [repuestos_raw.get("descripcion", "")]  # Convertir a lista
    
    if isinstance(repuestos_raw, list):
        for r in repuestos_raw:
            if isinstance(r, str):  # Caso de lista de cadenas
                repuestos_normalizados.append({
                    "tipo": "",
                    "referencia": r,
                    "marca": "",
                    "cantidad": 1,
                    "codigoStandard": r.replace(" ", "-")
                })
            elif isinstance(r, dict):  # Caso de lista de diccionarios
                repuestos_normalizados.append({
                    "tipo": r.get("tipo", ""),
                    "referencia": r.get("referencia", ""),
                    "marca": r.get("marca", ""),
                    "cantidad": r.get("cantidad", 1),
                    "codigoStandard": f"{r.get('marca', '')}-{r.get('referencia', '').replace(' ', '-')}"
                })
    
    return repuestos_normalizados

def transformar_clientes(doc: Dict[str, Any]) -> Dict[str, Any]:
    cliente = ""
    
    if isinstance(doc.get("informacion_general", {}).get("cliente"), dict):
        cliente = doc["informacion_general"]["cliente"].get("nombre", "")
    elif isinstance(doc.get("informacion_general", {}).get("cliente"), str):
        cliente = doc["informacion_general"]["cliente"]
    elif "empresa_cliente" in doc.get("informacion_general", {}):
        cliente = doc["informacion_general"].get("empresa_cliente", "")
    elif "informacion_cliente" in doc:
        cliente = doc["informacion_cliente"].get("empresa", "")
    
    return cliente

def transformar_fallas(doc: Dict[str, Any]) -> Dict[str, Any]:
    servicio = doc.get("servicio")
    fallas = ""
    
    if isinstance(servicio.get("diagnostico_falla"), dict):
        fallas = servicio.get("diagnostico_falla", {}).get("tipo", "")
    elif isinstance(servicio.get("tipo_falla"), str):
        fallas = servicio.get("tipo_falla", '')
    
    return fallas

def transformar_estado_reparacion(doc):
    estado = "Verificado"  # Valor por defecto
    
    if isinstance(doc.get("verificacion_placa"), dict):
        estado = doc["verificacion_placa"].get("resultado", "Verificado")
    elif isinstance(doc.get("verificacion_placa"), str):
        estado = doc["verificacion_placa"]
    
    return estado

def transformar_recomendaciones(doc):
    """
    Extrae las recomendaciones en el formato requerido por Weaviate.
    Retorna un diccionario con 'especificas' y 'generales'.
    """
    recomendaciones = doc.get("recomendaciones", {})
    
    # Manejo flexible para específicas (acepta string o lista)
    especificas = recomendaciones.get("especificas", [])
    if isinstance(especificas, str):
        especificas = [especificas]  # Convertir string a lista de un elemento
    elif not isinstance(especificas, list):
        especificas = []  # Por si acaso viene otro tipo de dato
    
    # Generales deben ser una lista con todas las recomendaciones generales
    generales = []
    generales_data = recomendaciones.get("generales", doc.get('recomendaciones_generales', {})) 
    
    for categoria, valor in generales_data.items():
        if isinstance(valor, list):
            generales.extend(valor)
        elif isinstance(valor, str):
            generales.append(valor)
    
    return {
        "especificas": especificas,
        "generales": generales
    }


def generar_texto_completo(doc: Dict[str, Any], doc_transformado: Dict[str, Any]) -> str:
    """Genera el texto optimizado para Snowflake Arctic Embed"""
    datos = doc_transformado.get("datosTecnicos", {})
    servicio = doc_transformado.get("servicio", {})
    recomendaciones = doc_transformado.get("recomendaciones", {})
    fechas = doc_transformado.get("fechasClave", {})
    diagnostico = servicio.get("diagnostico", {})
    normativas = doc_transformado.get("normativas", [])
    recomendaciones_texto = (
        f"especificas - {'; '.join(recomendaciones.get('especificas', []))}; "
        f"generales - {'; '.join(recomendaciones.get('generales', ''))}"
    )

    # generales = []
    # generales_raw = recomendaciones.get("generales", {})
    # for v in generales_raw.values():
    #     if isinstance(v, list):
    #         generales.extend(v)
    #     elif isinstance(v, str):
    #         generales.append(v)

    # recomendaciones_texto = (
    #     f"especificas - {recomendaciones.get('especificas', '').strip()}; "
    #     f"generales - {'; '.join(generales)}"
    # )
    
    partes_texto = [
        f"Motor marca: {datos.get('marca', '')}, potencia: {datos.get('potencia', '')}, tension: {datos.get('tension', '')}, corriente: {datos.get('corriente', '')}",
        f"Servicio: {servicio.get('tipo', '')} - {servicio.get('descripcion', '')}",
        f"Procedimientos: {'; '.join(servicio.get('procedimientos', []))}",
        f"Recomendaciones: {recomendaciones_texto}",
        f"Falla: {diagnostico.get('tipoFalla', '')} - {diagnostico.get('descripcionFalla', '')}",
        f"Estado reparación: {doc_transformado.get('estadoReparacion', '')}",
        f"Fechas: inicio - {fechas.get('ingreso', '')}, fin - {fechas.get('entrega', '')}",
        f"Normativas: {'; '.join(normativas)}",
        f"Cliente: {doc_transformado.get('cliente', '')}"
    




        # f"Motor {datos['tipoEquipo']} {datos['marca']} {datos['potencia']}",
        # f"Operación: {datos['rpm']} RPM, {datos['tension']}, {datos['fases']} fases",
        # f"Ubicación: {datos['maquinaAsociada']}",
        # f"Falla: {servicio['diagnostico']['tipoFalla']} - {servicio['diagnostico']['descripcionFalla']}",
        # # f"Causa raíz: {servicio['diagnostico']['causaRaiz']}" if servicio['diagnostico']['causaRaiz'] else "",
        # f"Servicio: {servicio['tipo']}",
        # f"Procedimientos: {'; '.join(servicio['procedimientos'][:3])}",
        # f"Pruebas: Aislamiento {pruebas['electricas']['aislamientoTierra'].split(' ')[0]}; ",
        # f"Alta tensión: {pruebas['electricas']['altaTension'].split(' ')[0]}",
        # f"Repuestos: {len(doc_transformado['repuestos'])} ítems ({', '.join([r['referencia'] for r in doc_transformado['repuestos'][:2]])})",
        # f"Resultado: {doc_transformado.get('estadoReparacion', 'Verificado')}",
        # f"Recomendaciones: {recomendaciones_texto}"
        # # f"Documentación: {'Fotos disponibles' if doc_transformado.get('documentacionAdjunta', {}).get('fotosAntes', False) else 'Sin fotos'}"
    ]
    
    return ". ".join([p for p in partes_texto if p]) + "."

def transformar_documento(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Transforma un documento JSON a la estructura estandarizada"""

    doc_transformado = {
        "archivo": doc.get("archivo", ""),
        "datosTecnicos": extraer_datos_tecnicos(doc),
        "servicio": transformar_servicio(doc),
        "pruebas": transformar_pruebas(doc),
        "repuestos": transformar_repuestos(doc),
        # "repuestos": [
        #     {
        #         "tipo": r.get("tipo", ""),
        #         "referencia": r.get("referencia", ""),
        #         "marca": r.get("marca", ""),
        #         "cantidad": r.get("cantidad", 0),
        #         "codigoStandard": f"{r.get('marca', '')}-{r.get('referencia', '').replace(' ', '-')}"
        #     } for r in doc.get("repuestos", [])
        # ],
        "fechasClave": {
            "ingreso": estandarizar_fecha(doc.get("informacion_general", {}).get("fecha_ingreso", "")),
            "informe": estandarizar_fecha(doc.get("informacion_general", {}).get("fecha_informe", "")),
            "entrega": estandarizar_fecha(doc.get("informacion_general", {}).get("fecha_entrega", "")),
            "firma": estandarizar_fecha(doc.get("firmas", {}).get("fecha_firma", ""))
        },
        "recomendaciones": transformar_recomendaciones(doc),
        "normativas": [
            f"{n.get('codigo', '')}:{n.get('version', '')}" 
            for n in doc.get("normativas", [])
        ],
        "cliente": transformar_clientes(doc), #doc.get("informacion_general", {}).get("cliente", {}).get("nombre", "")
        "tipoFalla": transformar_fallas(doc), #doc.get("servicio", {}).get("diagnostico_falla", {}).get("tipo", ""),
        "estadoReparacion": transformar_estado_reparacion(doc) #doc.get("verificacion_placa", {}).get("resultado", "Verificado")
        # "documentacionAdjunta": {
        #     "fotosAntes": doc.get("observaciones", {}).get("fotos", {}).get("antes", "") == "Disponible",
        #     "fotosDespues": doc.get("observaciones", {}).get("fotos", {}).get("despues", "") == "Disponible",
        #     "diagramas": False
        # }
    }
    
    doc_transformado["textoCompleto"] = generar_texto_completo(doc, doc_transformado)
    return doc_transformado


def convertir_fecha(fecha_str):
    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
        return fecha.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception as e:
        print(f"Error al convertir fecha: {fecha_str} -> {e}")
        return None


def cargar_a_weaviate(doc: Dict[str, Any]) -> bool:
    """Carga un documento transformado a Weaviate"""
    try:
        data_object = {
            "archivo": doc["archivo"],
            "marca": doc["datosTecnicos"]["marca"],
            "potencia": doc["datosTecnicos"]["potencia"],
            "tension": doc["datosTecnicos"]["tension"],
            "corriente":doc["datosTecnicos"]["corriente"],
            "tipoServicio":doc["servicio"]["tipo"],
            "descripcionServicio":doc["servicio"]["descripcion"],
            "procedimientosServicio": doc["servicio"]["procedimientos"],
            "recomendacionesGenerales": doc["recomendaciones"]["generales"],
            "recomendacionesEspecificas": doc["recomendaciones"]["especificas"],
            "cliente": doc["cliente"],
            "tipoFalla":doc["tipoFalla"],
            "estadoReparacion":doc["estadoReparacion"],
            "fechaInicio": convertir_fecha(doc["fechasClave"]["ingreso"]),
            "fechaFin": convertir_fecha(doc["fechasClave"]["entrega"]),
            "normativas":doc["normativas"],
            "textoCompleto": doc["textoCompleto"]

            # "archivo": doc["archivo"],
            # "datosTecnicos": doc["datosTecnicos"],
            # "servicio": doc["servicio"],
            # "pruebas": doc["pruebas"],
            # "repuestos": doc["repuestos"],
            # "fechasClave": doc["fechasClave"],
            # "normativas": doc["normativas"],
            # "recomendaciones": doc["recomendaciones"],
            # "cliente": doc["cliente"],
            # "tipoFalla": doc["tipoFalla"],
            # "estadoReparacion": doc["estadoReparacion"],
            # "textoCompleto": doc["textoCompleto"]
            # # "documentacionAdjunta": doc.get("documentacionAdjunta", {})
        }
        
        client.collections.get(CLASS_NAME).data.insert(data_object)

        return True
    except Exception as e:
        print(f"Error al cargar documento: {str(e)}")
        return False

def procesar_objeto_json(objeto: Dict[str, Any], filename: str, index: int) -> Optional[Dict[str, Any]]:
    """Transforma un objeto JSON individual a la estructura estandarizada"""
    try:
        # Asegurarnos que el objeto tenga un campo 'archivo' único
        if 'archivo' not in objeto:
            base_name = os.path.splitext(filename)[0]
            objeto['archivo'] = f"{base_name}_{index+1}.pdf"
        
        return transformar_documento(objeto)
    except Exception as e:
        print(f"❌ Error procesando objeto {index+1} en {filename}: {str(e)}")
        return None

def procesar_archivo_json(filepath: str) -> tuple[int, int]:
    """Procesa un archivo JSON que puede contener un objeto o un array de objetos"""
    filename = os.path.basename(filepath)
    exitos = 0
    errores = 0
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Determinar si es un array o un objeto individual
        if isinstance(data, list):
            print(f"📂 Procesando archivo {filename} con {len(data)} objetos...")
            objetos = data
            es_array = True
        else:
            print(f"📄 Procesando archivo {filename} con 1 objeto...")
            objetos = [data]
            es_array = False
        
        transformados = []
        
        for i, obj in enumerate(objetos):
            transformado = procesar_objeto_json(obj, filename, i)
            if transformado:
                # exitos += 1
                # transformados.append(transformado)
                if cargar_a_weaviate(transformado):
                    transformados.append(transformado)
                    exitos += 1
                else:
                    errores += 1
            else:
                errores += 1
        
        # Guardar archivo transformado
        if transformados:
            try:
                output_filename = f"transformado_{filename}"
                output_path = os.path.join(OUTPUT_FOLDER, output_filename)

                with open(output_path, 'w', encoding='utf-8') as f:
                    if es_array:
                        json.dump(transformados, f, ensure_ascii=False, indent=2)
                    else:
                        json.dump(transformados[0] if transformados else {}, f, ensure_ascii=False, indent=2)

                print(f"✅ Archivo guardado correctamente en {output_path}")

            except Exception as e:
                print(f"❌ Error al guardar el archivo: {e}")

        return exitos, errores
    
    except json.JSONDecodeError:
        print(f"❌ Error: Archivo {filename} no es un JSON válido")
        return 0, 1
    except Exception as e:
        print(f"❌ Error procesando archivo {filename}: {str(e)}")
        return 0, 1

def procesar_todos_los_archivos():
    """Procesa todos los archivos JSON en la carpeta de entrada"""
    # if not os.path.exists(INPUT_FOLDER):
    #     os.makedirs(INPUT_FOLDER)
    #     print(f"📁 Se creó la carpeta de entrada: {INPUT_FOLDER}")
    
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
        print(f"📁 Se creó la carpeta de salida: {OUTPUT_FOLDER}")
    
    crear_esquema_weaviate()
    total_exitos = 0
    total_errores = 0
    
    print(f"\n🔍 Buscando archivos JSON en {INPUT_FOLDER}...")
    
    for filename in sorted(os.listdir(INPUT_FOLDER)):
        if filename.endswith(".json"):
            filepath = os.path.join(INPUT_FOLDER, filename)
            
            exitos, errores = procesar_archivo_json(filepath)
            total_exitos += exitos
            total_errores += errores
            
            print(f"   ✅ Objetos exitosos: {exitos}")
            print(f"   ❌ Errores: {errores}")
            print("   ──────────────────────────")
    
    print(f"\n🏁 Proceso completado:")
    print(f"- Total de documentos procesados exitosamente: {total_exitos}")
    print(f"- Total de errores: {total_errores}")
    print(f"- Archivos transformados guardados en: {os.path.abspath(OUTPUT_FOLDER)}")
    print(f"- Documentos cargados en Weaviate en la clase 'InformesMotores'")
    print(f"- Cerrando conexion a Weaviate'")
    client.close()

def rewrite_query(user_question: str) -> str:
    inputs = tokenizer(user_question, return_tensors="pt")
    with torch.no_grad():
        outputs = model.generate(**inputs)
    # outputs = model.generate(**inputs)
    print(outputs)
    reformulated = tokenizer.decode(outputs[0], skip_special_tokens=True)

    return reformulated
    # prompt = f"Generate a search query: {user_question}"
    # result = generator(prompt, max_length=64, do_sample=False)
    # return result[0]["generated_text"]

# # Define las propiedades esperadas, su tipo y sinónimos
# def construir_query_usuario(texto_usuario: str) -> dict:
#     texto_limpio = re.sub(r"[^\w\s\-]", "", texto_usuario.lower())
#     palabras = texto_limpio.split()
#     filtros = []

#     for prop, config in PROPIEDADES.items():
#         for clave in config["claves"]:
#             if clave in palabras:
#                 # Extraer el valor según el tipo de dato
#                 if config["tipo"] == "unidad":
#                     valor = extraer_valor_con_unidad(palabras, clave, prop)
#                 else:
#                     valor = extraer_valor_despues_de_clave(palabras, clave)

#                 if not valor:
#                     continue

#                 # Agregar el filtro según el tipo
#                 if config["tipo"] in ["texto", "unidad"]:
#                     filtros.append(Filter.by_property(prop.strip()).equal(valor))
#                 elif config["tipo"] == "fecha":
#                     try:
#                         fecha_obj = datetime.strptime(valor, "%Y-%m-%d").date()
#                         filtros.append(Filter.by_property(prop.strip()).equal(fecha_obj))
#                     except ValueError:
#                         pass  # Ignorar si no es una fecha válida


#     filtro_final = None
#     if filtros:
#         filtro_final = filtros[0]
#         for f in filtros[1:]:
#             filtro_final = filtro_final & f

#     return {
#         "query": texto_usuario,
#         "filters": filtro_final
#     }

# def extraer_valor_despues_de_clave(palabras: list[str], clave: str) -> str | None:
#     if clave in palabras:
#         idx = palabras.index(clave)
#         for i in range(idx + 1, len(palabras)):
#             palabra = palabras[i].strip().lower()
#             if palabra in STOPWORDS:
#                 continue
#             if palabra in VALORES_INVALIDOS:
#                 return None
#             if re.match(r"^[a-zA-Z0-9\-]+$", palabra):
#                 return palabra.upper()
#             else:
#                 break
#     return None


# def extraer_valor_con_unidad(palabras: list[str], clave: str, tipo_prop: str) -> str | None:
#     if clave in palabras:
#         idx = palabras.index(clave)
#         for i in range(idx + 1, len(palabras) - 1):
#             palabra_actual = palabras[i]
#             palabra_siguiente = palabras[i + 1]
#             if palabra_actual.isdigit():
#                 unidad = palabra_siguiente
#                 if unidad in UNIDADES.get(tipo_prop, set()):
#                     return f"{palabra_actual} {unidad.upper()}"
#     return None





if __name__ == "__main__":
    # print("🚀 Iniciando procesamiento de múltiples archivos JSON")
    # print(f"🔗 Conexión a Weaviate: {WEAVIATE_URL}")
    # print(f"🤖 Modelo de embeddings: snowflake-arctic-embed-l-v2.0\n")
    
    # procesar_todos_los_archivos()
    # client.close()


    # def preparar_query_para_weaviate(pregunta: str) -> str:
    #     # Busca potencia como número
    #     match = re.search(r'(\d+\.?\d*)\s*HP', pregunta, re.IGNORECASE)
    #     if match:
    #         potencia = match.group(1)
    #         return f"motor con potencia {potencia} HP"
    #     return pregunta  # fallback si no encuentra patrón
    # def preparar_query_para_weaviate(pregunta: str) -> str:
    #     if "cliente" in pregunta.lower() and "servicio" in pregunta.lower():
    #         match = re.search(r'cliente\s+(.+?)[\?\.]?', pregunta, re.IGNORECASE)
    #         if match:
    #             cliente = match.group(1).strip()
    #             return f"servicios realizados al cliente {cliente}"
    #     return pregunta  # fallback

    

    try:
        collection = client.collections.get(CLASS_NAME)

        

        query_para_weaviate = "¿Que archivos tiene motor de marca WEG?"
        # query_para_weaviate = f"archivos con fecha inicio 2024-03-27"
        # query_para_weaviate = f"¿Qué tipo de falla se presentó en el motor de la marca WEG?"
        print(f"esta es la pregunta: {query_para_weaviate}")
       

        
        # query_llm = "¿Que tipo de servicios le hice al cliente ALIMENTOS CARNICOS S A S?"
        # query_para_weaviate = preparar_query_para_weaviate(query_para_weaviate)
        # query_para_weaviate = "servicios realizados al cliente ALIMENTOS CARNICOS S A S"
        better_query = rewrite_query(query_para_weaviate)



        print(f"Esta es la pregunta reformulada: {better_query}")


        print("🚀 Iniciando Query")
        # query_info = construir_query_usuario(query_para_weaviate)
        # print("📦 Query enviada a Weaviate:", query_info["query"])
        # print("🧪 Filtros aplicados:", vars(query_info["filters"]))

        # results = collection.query.hybrid(
        #     query=query_para_weaviate,  # Texto del usuario
        #     limit=5,
        #     alpha=0.75,
        #     fusion_type=HybridFusion.RELATIVE_SCORE,  # ✅ Correcto
        #     # filters=query_info["filters"],  # ✅ Debe ser un objeto tipo Filter
        #     target_vector="textoCompleto_vector",  # ✅ Nombre del vector
        #     return_metadata=MetadataQuery(score=True, explain_score=True),  # ✅ Para debugging
        #     return_properties=[
        #         "marca", "tipoFalla", "recomendacionesEspecificas",
        #         "tipoServicio", "procedimientosServicio", "potencia"
        #     ]  # ✅ Atributos que quieres retornar
        # )


        # # results = collection.query.hybrid(
        # #     query=query_info["query"],  # Texto del usuario
        # #     limit=5,
        # #     alpha=0.1,
        # #     fusion_type=HybridFusion.RELATIVE_SCORE,  # ✅ Correcto
        # #     filters=query_info["filters"],  # ✅ Debe ser un objeto tipo Filter
        # #     target_vector="textoCompleto_vector",  # ✅ Nombre del vector
        # #     return_metadata=MetadataQuery(score=True, explain_score=True),  # ✅ Para debugging
        # #     return_properties=[
        # #         "marca", "tipoFalla", "recomendacionesEspecificas",
        # #         "tipoServicio", "procedimientosServicio", "potencia"
        # #     ]  # ✅ Atributos que quieres retornar
        # # )

        # # results = collection.query.hybrid(
        # #     query=query_para_weaviate,  # tu texto de búsqueda
        # #     limit=5,
        # #     alpha=0.80,
        # #     # query_properties=["fechaInicio"], 
        # #     target_vector="textoCompleto_vector",
        # #     filters=Filter.by_property("fechaInicio").equal(convertir_fecha('2024-03-27')),
        # #     return_metadata=MetadataQuery(score=True, explain_score=True)
        # #     # target_vector="textoCompleto_vector",
        # #     # filters=Filter.by_property("potencia").equal("20 HP")
        # # )

        # # results = collection.query.near_text(
        # #     query=query_para_weaviate,
        # #     limit=2,
        # #     target_vector="textoCompleto_vector",
        # #     return_metadata=MetadataQuery(distance=True)
        # # )

        # print(f"🔗 Imprimiendo resultados - semantic search con near_text o hybrid")
        # print(len(results.objects))
        # for obj in results.objects:
        #     # if  obj.metadata.score >= 0.90:
        #     props = obj.properties
        #     texto = f"""
        #         **🔧 Score:** {obj.metadata.score}
        #         **🔧 Marca:** {props.get("marca")}
        #         **🔧 Potencia:** {props.get("potencia")}
        #         **⚡ Tipo de Falla:** {props.get("tipoFalla")}
        #         **🧰 Servicio:** {props.get("tipoServicio")}
        #         **📋 Procedimientos:** {', '.join(props.get("procedimientosServicio", [])) if props.get("procedimientosServicio") else 'N/A'}
        #         **✅ Recomendaciones:** {', '.join(props.get("recomendacionesEspecificas", [])) if props.get("recomendacionesEspecificas") else 'N/A'}
        #         """
        #     print(texto)
                
                # print(f"Texto: {obj.properties['textoCompleto']}")

        # embed_model = SentenceTransformer("snowflake/snowflake-arctic-embed-l-v2.0")  # o el modelo que uses

        # query_embedding = embed_model.encode("¿Cuál es la marca del motor con potencia 20 HP?", convert_to_tensor=True)

        # # Supón que results.objects[i].properties['textoCompleto'] contiene el texto
        # docs = [
        #     {
        #         "text": obj.properties["textoCompleto"],
        #         "embedding": obj.vector,  # si usas `.with_vector()` en el query
        #         "score": util.cos_sim(query_embedding, obj.vector).item()
        #     }
        #     for obj in results.objects
        # ]

        # # Ordena por score y selecciona el mejor
        # docs = sorted(docs, key=lambda d: d["score"], reverse=True)
        # mejor_contexto = docs[0]["text"]
            


        # print("🚀 Iniciando Query II")
        # results = collection.query.fetch_objects(
        #     filters=Filter.by_property("cliente").equal("AMCOR FLEXIBLES CALI SAS"),
        #     limit=10
        # )
        # print(f"🔗 Imprimiendo resultados - propiedades (where)")
        # for obj in results.objects:
        #     print(obj.properties["archivo"], obj.properties["cliente"])

        # print("🚀 Iniciando Query III")
        # results = collection.query.hybrid(
        #     query="Hola como estas?",
        #     limit=5,
        #     filters=Filter.by_property("cliente").equal("FAMILIA DEL PACIFICO SAS")
        # )
        # print(f"🔗 Imprimiendo resultados - Combinar búsqueda semántica y filtros ")
        # print(results)


        print(f"🤖 Cerrando la conexion")
        client.close()
    except Exception as e:
        print(str(e))
        print(f"🤖 Cerrando la conexion")
        client.close()