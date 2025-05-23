# # Librerías necesarias
# import os  # Para manejo de archivos y directorios
# import fitz  # PyMuPDF, para leer texto desde archivos PDF
# import re   # Expresiones regulares para buscar patrones en el texto

# # Función para extraer texto desde un PDF, página por página
# def extraer_texto_desde_pdf(ruta_pdf: str) -> str:
#     texto = ""
#     with fitz.open(ruta_pdf) as doc:
#         for pagina in doc:
#             texto += pagina.get_text("text")  # Extrae texto en modo legible
#     return texto.lower()  # Retorna todo en minúsculas para facilitar búsquedas

# # Función para extraer los datos técnicos clave del texto del PDF
# def extraer_especificaciones(texto: str, filename: str) -> str:
#     # Diccionario base con valores por defecto
#     resultado = {
#         "potencia_hp": "N/A",
#         "rpm": "N/A",
#         "torque_nm": "N/A",
#         "torque_rpm": "N/A",
#         "transmision": "N/A",
#         "valvulas": "N/A",
#         "turbo": "no",
#         "combustible": "N/A",
#         "cilindrada": "N/A"
#     }

#     # Divide el texto en líneas para procesarlo línea a línea
#     lineas = texto.splitlines()
#     linea_anterior = ""  # Guarda la línea anterior para contexto

#     for linea in lineas:
#         # Busca datos de potencia si la línea anterior contiene la palabra "potencia"
#         if "potencia" in linea_anterior:
#             match = (
#                 re.search(r"(\d{2,4})\s*/\s*[\d.]+\s*@\s*([\d,.-]+)", linea) or  # Formato con slash
#                 re.search(r"(\d{2,4})\s*@\s*([\d,.-]+)", linea)  # Formato simple con @
#             )
#             if match:
#                 resultado["potencia_hp"] = int(match.group(1))
#                 resultado["rpm"] = match.group(2).replace(",", "").replace(".", "").replace(" ", "")

#         # Busca datos de torque si la línea anterior contiene la palabra "torque"
#         elif "torque" in linea_anterior:
#             match = (
#                 re.search(r"(\d{2,4})\s*/\s*[\d.]+\s*@\s*([\d,.\s-]+)", linea) or
#                 re.search(r"(\d{2,4})\s*@\s*([\d,.\s-]+)", linea)
#             )
#             if match:
#                 resultado["torque_nm"] = int(match.group(1))
#                 resultado["torque_rpm"] = match.group(2).replace(",", "").replace(" ", "")

#         linea_anterior = linea  # Actualiza la línea anterior

#     # Busca datos de la transmisión en diferentes formatos posibles
#     transmision_match = (
#         re.search(r"(manual|autom[aá]tica).*?(\d+)\s+velocidades", texto) or  # Formato tipo "automática de 10 velocidades"
#         re.search(r"transmisión\s*/\s*velocidades\s*(mt|at)\s*/\s*(\d+)", texto)  # Formato tipo "transmisión / velocidades mt / 5"
#     )
#     if transmision_match:
#         if transmision_match.lastindex == 2:
#             tipo = transmision_match.group(1)
#             num = transmision_match.group(2)
#         else:
#             tipo = "manual" if transmision_match.group(1) == "mt" else "automática"
#             num = transmision_match.group(2)
#         resultado["transmision"] = f"{tipo} {num} velocidades"

#     # Busca cantidad de válvulas
#     valvulas_match = re.search(r"(\d+)\s+val", texto)
#     if valvulas_match:
#         resultado["valvulas"] = int(valvulas_match.group(1))

#     # Detecta si tiene turbo
#     if "turbo alimentación" in texto or "√" in texto:
#         resultado["turbo"] = "sí"

#     # Detecta tipo de combustible
#     combustible = re.search(r"tipo de combustible\s+([a-z]+)", texto)
#     if combustible:
#         resultado["combustible"] = combustible.group(1)

#     # Busca la cilindrada por método tradicional
#     cilindrada = re.search(r"cilindrada\s*\(litros\)?\s*[:\-]?\s*(\d+[.,]?\d*)", texto)
#     if cilindrada:
#         resultado["cilindrada"] = cilindrada.group(1).replace(",", ".") + " L"
#     else:
#         # Alternativa si viene en formato tipo "5.3 L" sin etiqueta
#         cilindrada_alt = re.search(r"(\d\.\d)\s*l", texto)
#         if cilindrada_alt:
#             resultado["cilindrada"] = cilindrada_alt.group(1) + " L"

#     # Devuelve el resultado formateado como texto legible
#     lineas = [
#         f"Potencia: {resultado['potencia_hp']} hp @ {resultado['rpm']} rpm",
#         f"Torque: {resultado['torque_nm']} Nm @ {resultado['torque_rpm']} rpm",
#         f"Transmisión: {resultado['transmision']}",
#         f"Válvulas: {resultado['valvulas']}",
#         f"Turbo: {resultado['turbo']}",
#         f"Combustible: {resultado['combustible']}",
#         f"Cilindrada: {resultado['cilindrada']}"
#     ]
#     return "\n".join(lineas)

# # Procesa todos los PDFs en una carpeta dada y guarda los resultados
# def procesar_pdfs_en_carpeta(carpeta: str, carpeta_salida: str):
#     if not os.path.exists(carpeta_salida):
#         os.makedirs(carpeta_salida)  # Crea la carpeta de salida si no existe

#     for archivo in os.listdir(carpeta):
#         if archivo.lower().endswith(".pdf"):
#             ruta_pdf = os.path.join(carpeta, archivo)
#             texto = extraer_texto_desde_pdf(ruta_pdf)  # Extrae texto plano del PDF
#             especificaciones = extraer_especificaciones(texto)  # Extrae los datos relevantes

#             nombre_salida = os.path.splitext(archivo)[0] + ".txt"
#             ruta_salida = os.path.join(carpeta_salida, nombre_salida)

#             with open(ruta_salida, "w", encoding="utf-8") as f:
#                 f.write(especificaciones)

#             print(f"✅ Procesado: {archivo} -> {nombre_salida}")

# # Función principal que define las rutas y ejecuta el procesamiento

# def main():
#     carpeta_entrada = r"C:\Users\dddia\Documents\pdfs_entrada"
#     carpeta_salida = r"C:\Users\dddia\Documents\data_pdfs"
#     procesar_pdfs_en_carpeta(carpeta_entrada, carpeta_salida)

# if __name__ == "__main__":
#     main()