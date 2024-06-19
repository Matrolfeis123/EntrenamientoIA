import re
import numpy as np
import pdfplumber
import spacy
from spacy.matcher import Matcher
import os
from openpyxl import Workbook
import xml.etree.ElementTree as ET
from geopy.distance import geodesic
from difflib import get_close_matches
from unidecode import unidecode
import simplekml
import time



def generar_diccionario_proyectos_v2(file):
    diccionario_obras_nuevas = {}
    diccionario_lineas_nuevas = {}
    paginas = [1,2]
    lista_titulos_largos = []

    with pdfplumber.open(file) as pdf:
        text = ""
        for i in paginas:
            text += pdf.pages[i].extract_text()

        matches = re.finditer(r'(Nueva (S/E|línea|líneas).*?)(?=\n\S)', text, re.DOTALL)
        for match in matches:
            line = match.group(0)
            if not re.match(r".*[0-9]{2}$", line):
                lista_titulos_largos.append(line)
                print("Título largo: ", line)
                titulo = input("Ingrese el título del proyecto según el índice del pdf: ")
                pag_inicio = int(input("Ingrese la página de inicio del proyecto según el índice del pdf: ")) - 1
                pag_final = pag_inicio + 3
##############################################################################################
                if "s/e" in titulo.lower() and "nuevas líneas" in titulo.lower():
                    # Por lo tanto, el proyecto se compone de una nueva s/e y nuevas lineas. 
                    # Por lo tanto, separaremos el titulo para almacenar cada titulo en un diccionario
                    # EJ: Nueva S/E Caracoles, nuevas líneas 2x220 kV Caracoles – Liqcau y 2x110 kV Guardiamarina – Caracoles
                    # Se almacenará en el diccionario de la siguiente manera:
                    aux = titulo.split(", nuevas líneas")

                    if len(aux) > 1:
                        
                        titulo_se_nva = aux[0].strip()
                        titulo_lineas_nvas = aux[1].split(" y ")

                    else:
                        aux = titulo.split(" y nuevas líneas")

                        if len(aux) > 1:
                            titulo_se_nva = aux[0].strip()
                            titulo_lineas_nvas = aux[1].split(" y ")

                        else:
                            print("No se pudo clasificar el proyecto: ", titulo)
                            continue

                    
                    
                    diccionario_obras_nuevas[titulo_se_nva] = (pag_inicio, pag_final)
                    for linea in titulo_lineas_nvas:
                        diccionario_lineas_nuevas[linea.strip()] = (pag_inicio, pag_final)

                elif "nueva línea" in titulo.lower() and "s/e" in titulo.lower():
                    print(f"El proyecto es una línea nueva y una subestación nueva: {titulo}")
                    # Por lo tanto, el proyecto se compone de una nueva s/e y una nueva linea.
                    # Por lo tanto, separaremos el titulo para almacenar cada titulo en un diccionario
                    # EJ: Nueva S/E Alto Molle y nueva línea 2x110 kV Alto Molle – Cóndores

                    aux = titulo.split(" y nueva línea")
                    titulo_se_nva = aux[0].strip()
                    titulo_linea_nva = aux[1].strip()

                    diccionario_obras_nuevas[titulo_se_nva] = (pag_inicio, pag_final)
                    diccionario_lineas_nuevas[titulo_linea_nva] = (pag_inicio, pag_final)

                elif "nueva línea" in titulo.lower():
                    # Por lo tanto, el proyecto se compone de una nueva linea.
                    # Por lo tanto, almacenaremos el titulo en el diccionario de lineas nuevas
                    titulo = titulo.replace("Nueva línea", "").strip()
                    diccionario_lineas_nuevas[titulo] = (pag_inicio, pag_final)

                elif "s/e" in titulo.lower():
                    # Por lo tanto, el proyecto se compone de una nueva s/e.
                    # Por lo tanto, almacenaremos el titulo en el diccionario de obras nuevas
                    diccionario_obras_nuevas[titulo.strip()] = (pag_inicio, pag_final)

                else:
                    print(f"No se pudo clasificar el proyecto: {titulo}")

##############################################################################################
            else:
                match = re.match(r'^(.*?)\s+(\d+)$', line)
                if match:
                    titulo = match.group(1).replace(".", "")
                    pag_inicio = int(match.group(2)) - 1
                    pag_final = pag_inicio + 3

                    if "s/e" in titulo.lower() and "nuevas líneas" in titulo.lower():
                        # Por lo tanto, el proyecto se compone de una nueva s/e y nuevas lineas. 
                        # Por lo tanto, separaremos el titulo para almacenar cada titulo en un diccionario
                        # EJ: Nueva S/E Caracoles, nuevas líneas 2x220 kV Caracoles – Liqcau y 2x110 kV Guardiamarina – Caracoles
                        # Se almacenará en el diccionario de la siguiente manera:
                        aux = titulo.split(", nuevas líneas")
                        titulo_se_nva = aux[0]
                        titulo_lineas_nvas = aux[1].split(" y ")

                        diccionario_obras_nuevas[titulo_se_nva] = (pag_inicio, pag_final)
                        for linea in titulo_lineas_nvas:
                            diccionario_lineas_nuevas[linea] = (pag_inicio, pag_final)

                    elif "nueva línea" in titulo.lower() and "s/e" in titulo.lower():
                        print(f"El proyecto es una línea nueva y una subestación nueva: {titulo}")
                        # Por lo tanto, el proyecto se compone de una nueva s/e y una nueva linea.
                        # Por lo tanto, separaremos el titulo para almacenar cada titulo en un diccionario
                        # EJ: Nueva S/E Alto Molle y nueva línea 2x110 kV Alto Molle – Cóndores

                        aux = titulo.split(" y nueva línea")
                        titulo_se_nva = aux[0]
                        titulo_linea_nva = aux[1]

                        diccionario_obras_nuevas[titulo_se_nva] = (pag_inicio, pag_final)
                        diccionario_lineas_nuevas[titulo_linea_nva] = (pag_inicio, pag_final)

                    elif "nueva línea" in titulo.lower():
                        # Por lo tanto, el proyecto se compone de una nueva linea.
                        # Por lo tanto, almacenaremos el titulo en el diccionario de lineas nuevas
                        titulo = titulo.replace("Nueva línea", "")
                        diccionario_lineas_nuevas[titulo] = (pag_inicio, pag_final)

                    elif "s/e" in titulo.lower():
                        # Por lo tanto, el proyecto se compone de una nueva s/e.
                        # Por lo tanto, almacenaremos el titulo en el diccionario de obras nuevas
                        diccionario_obras_nuevas[titulo] = (pag_inicio, pag_final)

                    else:
                        print(f"No se pudo clasificar el proyecto: {titulo}")

                else:
                    print(f"No se pudo clasificar el proyecto: {line}")


        patron_final = r"El C.O.M.A"
        for diccionario in [diccionario_obras_nuevas, diccionario_lineas_nuevas]:
            for titulo, paginas in diccionario.items():
                for i in range(paginas[0], paginas[1]):
                    text = pdf.pages[i].extract_text()
                    if re.search(patron_final, text, re.DOTALL):
                        diccionario[titulo] = (paginas[0], i)


        print("Obras nuevas: ")
        for titulo, paginas in diccionario_obras_nuevas.items():
            print(f"{titulo}: {paginas}")

        print("Lineas nuevas: ")
        for titulo, paginas in diccionario_lineas_nuevas.items():
            print(f"{titulo}: {paginas}")

        return diccionario_obras_nuevas, diccionario_lineas_nuevas

def extraer_texto_entre_delimitadores_v2(texto, delimitador_inicial, delimitador_final):
    pattern = re.compile(f"{delimitador_inicial}(.*?{delimitador_final}.*?)\.", re.DOTALL)
    match = pattern.search(texto)
    return match.group(0) if match else "ERROR EXTRAYENDO TEXTO"

def extraer_descripciones(file, diccionario):
    descripciones = {}
    try:
        with pdfplumber.open(file) as pdf:
            for titulo, paginas in diccionario.items():
                texto = ""
                for i in range(paginas[0], paginas[1] + 1):
                    texto += pdf.pages[i].extract_text()

                texto = texto.replace("\n", " ")
                texto = texto.replace("  ", " ")

                descripcion_definitiva = extraer_texto_entre_delimitadores_v2(texto, "Descripción general y ubicación", "moneda de los Estados Unidos de América")
                descripciones[titulo] = descripcion_definitiva

    except Exception as e:
        print(f"Error en la ejecución del análisis: {e}")

    return descripciones

def extraer_nombre(texto):
    #Quizas este paso esta de mas, ya que el nombre del proyecto esta en el titulo del diccionario
    try:
        pattern = r"(?<=nueva subestación, denominada )[^,]+" # Expresión regular para extraer el nombre del proyecto
        match = re.search(pattern, texto) #esto se puede reemplazar por texto
        if match:
            #imprimir indices de frase
            print(match.group(0))
            return match.group(0)
        else:
            raise ValueError("No se encontró el nombre del proyecto")
        
    except ValueError as e:
        print(f"Error: {e}")



def encontrar_indices_nombre_subestacion(texto):
    nlp = spacy.load("es_core_news_sm")  # Cargar el modelo de idioma español

    # Procesar el texto con SpaCy
    doc = nlp(texto)

    # Definir la frase que contiene el nombre de la subestación
    frase_subestacion = "nueva subestación, denominada"

    # Encontrar el nombre de la subestación dentro del texto
    inicio = texto.find(frase_subestacion)
    print("probamos en texto: ", texto[inicio:inicio+50])
    breakpoint()
    if inicio == -1:
        raise ValueError("No se encontró la frase que contiene el nombre de la subestación nueva")


    fin = texto.find(",", inicio)  # Suponiendo que el nombre de la subestación termina en una coma

    if fin == -1:
        fin = len(texto)

    print(f"Inicio: {inicio}, Fin: {fin}")
    print("probamos en doc: ", doc[inicio:fin])
    
    return inicio, fin

def encontrar_indices_nombre_subestacion_v2(texto):
    nlp = spacy.load("es_core_news_sm")  # Cargar el modelo de idioma español

    # Procesar el texto con SpaCy
    doc = nlp(texto)

    # Definir la frase que contiene el nombre de la subestación
    frase_subestacion = "nueva subestación, denominada"

    # Encontrar el nombre de la subestación dentro del texto con spacy
    matcher = Matcher(nlp.vocab)
    patron = [{"LOWER": "nueva"}, {"LOWER": "subestación"}, {"LOWER": ","}, {"LOWER": "denominada"}, {"IS_ALPHA": True}, {"IS_PUNCT": True}]
    matcher.add("Nombre subestación", [patron])
    matches = matcher(doc)

    if len(matches) == 0:
        raise ValueError("No se encontró la frase que contiene el nombre de la subestación nueva")
    
    match_id, inicio, fin = matches[0]
    print(f"Inicio: {inicio}, Fin: {fin}")

    breakpoint()


def encontrar_indices_nombre_subestacion_v3(texto):
    nlp = spacy.load("es_core_news_sm")  # Cargar el modelo de SpaCy para español
    doc = nlp(texto)

    # Definir el patrón para encontrar el nombre de la subestación
    patron_nombre = [{"LOWER": "nueva"}, {"LOWER": "subestación"}, {"IS_PUNCT": True}, {"LOWER": "denominada"}, {"IS_ALPHA": True}, {"IS_PUNCT": True}]

    # Aplicar los patrones para encontrar los nombres de subestaciones
    matcher = Matcher(nlp.vocab)
    matcher.add("NOMBRE_SUBESTACION", [patron_nombre])

    matches = matcher(doc)

    # Obtener el texto y los índices de los tokens del nombre de la subestación encontrada
    for match_id, start, end in matches:
        span = doc[start:end]
        nombre_subestacion = span.text.split(",")[0].strip()  # Obtener el texto entre "denominada" y ","
        
        # Encontrar el token "denominada" en el span
        for token in span:
            if token.text.lower() == "denominada":
                start_token = token.i + 1  # El token siguiente a "denominada"
                breakpoint()
                break

        #vamos a extraer los indices de los caracteres que corresponden al nombre de la subestacion
        #y al token siguiente a "denominada"
        inicio_nombre_subestacion = span[0].idx
        fin_nombre_subestacion = span[-1].idx + len(span[-1].text)
        
        nombre_subestacion = start_token


        print(f"Nombre de la subestación: {nombre_subestacion}")
        print(f"Indices del nombre de la subestación: {inicio_nombre_subestacion}, {fin_nombre_subestacion}")
        
        breakpoint()

        return nombre_subestacion, start_token

    raise ValueError("No se encontró el nombre de la subestación")

if __name__ == "__main__":
    file = "plan_expansion_final_2023.pdf"
    diccionario_obras_nuevas, diccionario_lineas_nuevas = generar_diccionario_proyectos_v2(file)

    descripciones_obras_nuevas = extraer_descripciones(file, diccionario_obras_nuevas)

    train_data = []

    for titulo, descripcion in descripciones_obras_nuevas.items():
        print(f"{titulo}: {descripcion}")
        print("Nombre del proyecto: ", extraer_nombre(descripcion))
        encontrar_indices_nombre_subestacion_v3(descripcion)

