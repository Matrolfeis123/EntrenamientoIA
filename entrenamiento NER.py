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



def extraer_texto_entre_delimitadores_v2(texto, delimitador_inicial, delimitador_final):
    pattern = re.compile(f"{delimitador_inicial}(.*?{delimitador_final}.*?)\.", re.DOTALL)
    match = pattern.search(texto)
    return match.group(0) if match else "ERROR EXTRAYENDO TEXTO"


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


def extraer_indices_frase(nlp, texto, frase):
    try:
        doc = nlp(texto)
        t = frase
        frase = nlp(frase)
        for i in range(len(doc)):
            if doc[i].text == frase[0].text:
                if doc[i:i+len(frase)] == t:
                    return doc, i, i + len(frase)
        raise ValueError("Frase no encontrada")

    except ValueError as e:
        print(f"Error: {e}")


def main_v1():
    pdf_file = "plan_expansion_final_2023.pdf"
    diccionario_obras_nuevas, diccionario_lineas_nuevas = generar_diccionario_proyectos_v2(pdf_file)

    print("Extrayendo descripciones de obras nuevas...")
    print(diccionario_obras_nuevas)

    descripciones_obras_nuevas = extraer_descripciones(pdf_file, diccionario_obras_nuevas)
    print("Descripciones de obras nuevas extraídas.")
    print(descripciones_obras_nuevas)



def extraer_nombre_spacy(doc, nlp):
    # Definir una lista de patrones para buscar nombres de subestaciones


    patron_nombre = [{"LOWER": "nueva"}, {"LOWER": "subestación"}, {"IS_PUNCT": True}, {"LOWER": "denominada"}, {"IS_ALPHA": True}, {"IS_PUNCT": True}]


    # Aplicar los patrones para encontrar los nombres de subestaciones
    matcher = Matcher(nlp.vocab)
    matcher.add("NOMBRE_SUBESTACION", [patron_nombre])

    matches = matcher(doc)

    # Obtener los índices de inicio y fin de cada coincidencia
    indices_nombres = []
    for match_id, start, end in matches:
        span = doc[start:end]
        print(span.text, start, end)
        indices_nombres.append((span.start_char, span.end_char))

    return indices_nombres


def extraer_nombre_spacy_v2(doc, nlp):

    # Definir el patrón para encontrar el nombre de la subestación
    patron_nombre = [{"LOWER": "nueva"}, {"LOWER": "subestacion"}, {"IS_PUNCT": True}, {"LOWER": "denominada"}, {"IS_ALPHA": True}, {"IS_PUNCT": True}]

    # Aplicar los patrones para encontrar los nombres de subestaciones
    matcher = Matcher(nlp.vocab)
    matcher.add("NOMBRE_SUBESTACION", [patron_nombre])

    matches = matcher(doc)

    # Obtener el texto y los índices del nombre de la subestación encontrada
    for match_id, start, end in matches:
        span = doc[start:end]
        nombre_subestacion = span.text.split(",")[0].strip()  # Obtener el texto entre "denominada" y ","
        start_char = span.start_char + span.text.find("denominada") + len("denominada") + 1
        end_char = start_char + len(nombre_subestacion)
        return nombre_subestacion, start_char, end_char

    raise ValueError("No se encontró el nombre de la subestación")


def buscador_indices_frase(doc, frase):

    indices = []
    for span in doc.sents:
        if frase in span.text:
            # imprimir indices exactos de la frase
            print(span.text)
            for token in span:
                print(token.text, token.idx)
                if token.text == frase:
                    indices.append((token.idx, token.idx + len(token.text)))




if __name__ == "__main__":
    file = "plan_expansion_final_2023.pdf"
    nlp = spacy.load("es_core_news_lg")
    diccionario_obras_nuevas, diccionario_lineas_nuevas = generar_diccionario_proyectos_v2(file)

    print(diccionario_obras_nuevas)

    descripciones_obras_nuevas = extraer_descripciones(file, diccionario_obras_nuevas)

    for titulo, descripcion in descripciones_obras_nuevas.items():
        print(f"Titulo: {titulo}")
        print(f"Descripción: {descripcion}")
        print("\n\n")
        nombre = extraer_nombre(descripcion)
        print(buscador_indices_frase(nlp(descripcion), nombre))
        breakpoint()









    #     print(f"Titulo: {titulo}")
    #     print(f"Descripción: {descripcion}")
    #     print("\n\n")
    #     doc, inicio, fin = extraer_indices_nombre(nlp, descripcion)
    #     print(doc[inicio:fin])

    #     breakpoint()
    # texto = "Descripción general y ubicación de la obra El proyecto consiste en la construcción de una nueva subestación, denominada Tomeco, mediante el seccionamiento de la línea 2x220 kV Charrúa – Hualqui con sus respectivos paños de línea y un patio de 220 kV en configuración interruptor y medio. Adicionalmente, el proyecto contempla la construcción de los enlaces que corresponda para realizar el seccionamiento de la línea antes mencionada en la subestación Tomeco, los cuales 21—–——– deberán permitir la transmisión de, al menos, 700 MVA por circuito a 35°C temperatura ambiente con sol. La capacidad de barras de la nueva subestación deberá ser de, al menos, 2.000 MVA con 75°C en el conductor y 35°C temperatura ambiente con sol, y deberá considerar espacio en barras y plataforma para cuatro diagonales, de manera de permitir la conexión del seccionamiento de la línea 2x220 kV Charrúa – Hualqui y la conexión de nuevos proyectos en la zona. En caso de definirse el desarrollo de este patio en tecnología encapsulada y aislada en gas del tipo GIS o equivalente, se deberán considerar los paños contenidos en esta descripción y el espacio en plataforma definido anteriormente para la conexión de nuevos proyectos. La subestación se deberá emplazar a aproximadamente 30 km al este de la S/E Hualqui, siguiendo el trazado de la línea 2x220 kV Charrúa – Hualqui, dentro de un radio de 4 km respecto de ese punto. El proyecto incluye también todas las obras, modificaciones y labores necesarias para la ejecución y puesta en servicio de las nuevas instalaciones, tales como adecuaciones en los patios respectivos, adecuación de protecciones, comunicaciones, SCADA, obras civiles, montaje, malla de puesta a tierra y pruebas de los nuevos equipos, entre otras. En las respectivas bases de licitación se podrán definir otros requisitos mínimos que deberán cumplir las instalaciones para el fiel cumplimiento del objetivo del proyecto, tales como espacios disponibles, capacidad térmica, cable de guardia, reservas, equipamientos, entre otros. A su vez, el proyecto contempla todas las tareas, labores y obras necesarias para evitar interrupciones en el suministro a clientes finales, debiendo considerarse para ello una secuencia constructiva que evite o minimice dichas interrupciones. La disposición de los edificios, equipos, estructuras y otros elementos que conformen la subestación deberá permitir que las expansiones futuras se realicen de manera adecuada, haciendo posible el ingreso ordenado y sin interferencias de futuras líneas y circuitos, evitando generar espacios ciegos que impidan la plena utilización de las barras. Será responsabilidad del adjudicatario asegurar la compatibilidad tecnológica de los equipos utilizados en la ejecución del proyecto, de las instalaciones y de la disposición de los equipos en la subestación, de manera tal de posibilitar futuras ampliaciones de la subestación, así también como el cumplimiento de lo dispuesto en la normativa vigente en relación al acceso abierto a las instalaciones de transmisión. Por su parte, será responsabilidad de los propietarios de las diferentes instalaciones de generación y/o transporte coordinarse para efectuar las adecuaciones que se requieran en sus propias instalaciones para efectos de la ejecución del proyecto. 3.2.1.2 Entrada en operación El proyecto deberá ser construido y entrar en operación, a más tardar, dentro de los 54 meses siguientes a la fecha de publicación en el Diario Oficial del respectivo decreto a que hace referencia el artículo 96° de la Ley. 22—–——– 3.2.1.3 Valor de inversión (V.I.) y costo de operación, mantenimiento y administración (C.O.M.A.) referenciales El V.I. referencial del proyecto es de 13.980.034 dólares, moneda de los Estados Unidos de América."
    # texto2 ='Descripción general y ubicación de la obra El proyecto consiste en la construcción de una nueva subestación, denominada Alto Molle, con patios de 110 kV y 13,8 kV. A su vez, el proyecto considera la instalación de un transformador 110/13,8 kV de, al menos, 30 MVA de capacidad, con Cambiador de Derivación Bajo Carga (CDBC) y sus respectivos paños de conexión en ambos niveles de tensión. La configuración del patio de 110 kV de la subestación Alto Molle corresponderá a barra principal seccionada y barra de transferencia, con capacidad de barras de, al menos, 500 MVA con 75°C en el conductor y 35°C temperatura ambiente con sol, y deberá considerar espacio en barras y plataforma para nueve posiciones, de manera de permitir la conexión del transformador de poder 110/13,8 kV, la conexión de la nueva línea 2x110 kV Alto Molle – Cóndores, la conexión de la obra “Nueva S/E Huayquique y nueva línea 2x110 kV Huayquique – Alto Molle”, la construcción de un paño acoplador, la construcción de un paño seccionador de barras y la conexión de nuevos proyectos en la zona. En caso de definirse el desarrollo de este patio en tecnología encapsulada y aislada en gas del tipo GIS o equivalente, se deberán considerar los paños contenidos en esta descripción y el espacio en plataforma definido anteriormente para la conexión de nuevos proyectos. Además, el proyecto considera la construcción de un patio de 13,8 kV, en configuración barra simple, contemplándose la construcción de, al menos, cuatro paños para alimentadores, el paño de conexión para el transformador de poder 110/13,8 kV antes mencionado y espacio en barra y plataforma para la construcción de dos paños futuros. En caso de definirse el desarrollo de este patio como una sala de celdas, se deberán considerar los paños contenidos en esta descripción junto con la construcción de una celda para equipos de medida, la construcción de una celda para servicios auxiliares y el espacio en la sala para la conexión de posiciones futuras definidas anteriormente. La subestación se deberá emplazar dentro de un radio de 3 km respecto de la subestación Cóndores, considerando únicamente el semicírculo generado al sur de dicho punto. Adicionalmente, la ubicación de la instalación deberá garantizar el cumplimiento del propósito esencial de la obra, posibilitando el debido acceso y la conexión por parte de alimentadores de los sistemas de distribución de la zona. Adicionalmente, el proyecto contempla la construcción de una nueva línea de transmisión de doble circuito en 110 kV y, al menos, 90 MVA de capacidad por circuito a 35°C con sol, entre la nueva subestación Alto Molle y la subestación Cóndores, con sus respectivos paños de conexión en cada subestación de llegada. El proyecto incluye también todas las obras, modificaciones y labores necesarias para la ejecución y puesta en servicio de las nuevas instalaciones, tales como adecuaciones en los patios respectivos, adecuación de protecciones, comunicaciones, SCADA, obras civiles, montaje, malla de puesta a tierra y pruebas de los nuevos equipos, entre otras. En las respectivas bases de licitación se podrán definir otros requisitos mínimos que deberán cumplir 51—–——– las instalaciones para el fiel cumplimiento del objetivo del proyecto, tales como espacios disponibles, capacidad térmica, cable de guardia, reservas, equipamientos, entre otros. A su vez, el proyecto contempla todas las tareas, labores y obras necesarias para evitar interrupciones en el suministro a clientes finales, debiendo considerarse para ello una secuencia constructiva que evite o minimice dichas interrupciones. La disposición de los edificios, equipos, estructuras y otros elementos que conformen la subestación deberá permitir que las expansiones futuras se realicen de manera adecuada, haciendo posible el ingreso ordenado y sin interferencias de futuras líneas y circuitos, evitando generar espacios ciegos que impidan la plena utilización de las barras. Será responsabilidad del adjudicatario asegurar la compatibilidad tecnológica de los equipos utilizados en la ejecución del proyecto, de las instalaciones y de la disposición de los equipos en la subestación, de manera tal de posibilitar futuras ampliaciones de la subestación, así también como el cumplimiento de lo dispuesto en la normativa vigente en relación al acceso abierto a las instalaciones de transmisión. Por su parte, será responsabilidad de los propietarios de las diferentes instalaciones de generación y/o transporte coordinarse para efectuar las adecuaciones que se requieran en sus propias instalaciones para efectos de la ejecución del proyecto. 4.2.1.2 Entrada en operación El proyecto deberá ser construido y entrar en operación, a más tardar, dentro de los 54 meses siguientes a la fecha de publicación en el Diario Oficial del respectivo decreto a que hace referencia el artículo 96° de la Ley. 4.2.1.3 Valor de inversión (V.I.) y costo de operación, mantenimiento y administración (C.O.M.A.) referenciales El V.I. referencial del proyecto es de 16.800.105 dólares, moneda de los Estados Unidos de América.'


    # #vamos a printear el texto entre los indices inicio y fin con spacy del texto

    # nlp = spacy.load("es_core_news_lg")
    # doc, inicio, fin = extraer_indices_nombre(nlp, texto)
    # print(doc[inicio:fin])
           