import spacy
from spacy.matcher import Matcher
import pdfplumber
import re
from spacy.tokens import DocBin


def encontrar_indices_nombre_subestacion_v3(texto):
    nlp = spacy.load("es_core_news_sm")  # Cargar el modelo de SpaCy para español
    doc = nlp(texto)

    # Definir el patrón para encontrar el nombre de la subestación
    patron_nombre = [{"LOWER": "nueva"}, {"LOWER": "subestación"}, {"LOWER": "seccionadora", "OP": "*"}, {"IS_PUNCT": True}, {"LOWER": "denominada"}, {"IS_ALPHA": True, "OP": "+"}, {"IS_PUNCT": True}]

    # Aplicar los patrones para encontrar los nombres de subestaciones
    matcher = Matcher(nlp.vocab)
    matcher.add("NOMBRE_SUBESTACION", [patron_nombre])

    matches = matcher(doc)

    # Obtener el texto y los índices de los tokens del nombre de la subestación encontrada
    for match_id, start, end in matches:
        span = doc[start:end]
        
        # Encontrar el token "denominada" en el span
        for token in span:
            if token.text.lower() == "denominada":
                start_token = token.i + 1  # El token siguiente a "denominada"
                break

        # Encontrar el token siguiente al nombre de la subestación
        end_token = start_token
        while end_token < len(doc) and doc[end_token].text != ',':
            end_token += 1

        # Obtener el texto del nombre de la subestación
        nombre_subestacion = doc[start_token:end_token].text.strip(',')
        
        # Obtener los índices de caracteres
        inicio_nombre_subestacion = doc[start_token].idx
        fin_nombre_subestacion = doc[end_token - 1].idx + len(doc[end_token - 1].text)

        print(f"Nombre de la subestación: {nombre_subestacion}")
        print(f"Indices del nombre de la subestación: {inicio_nombre_subestacion}, {fin_nombre_subestacion}")

        return nombre_subestacion, inicio_nombre_subestacion, fin_nombre_subestacion

    raise ValueError("No se encontró el nombre de la subestación")


def crear_datos_entrenamiento(textos, nlp, datos_entrenamiento):
    for texto in textos:
        try:
            nombre, inicio, fin = encontrar_indices_nombre_subestacion_v3(texto)
            entities = [(inicio, fin, "NOMBRE_SUBESTACION")]
            datos_entrenamiento.append((texto, {"entities": entities}))

        except ValueError:
            print("error")
            continue
    return datos_entrenamiento



def generar_diccionario_proyectos_v2(file):
    diccionario_obras_nuevas = {}
    diccionario_lineas_nuevas = {}
    paginas = [1,2]
    lista_titulos_largos = []

    with pdfplumber.open(file) as pdf:
        text = ""
        for i in paginas:
            text += pdf.pages[i].extract_text()

        matches = re.finditer(r'(Nueva (S/E|S/E Seccionadora|línea|líneas|Línea|Líneas).*?)(?=\n\S)', text, re.DOTALL)
        try:
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

        except Exception as e:
            print(f"Error en la ejecución del análisis: {e}")


        try:
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

        except Exception as e:
            print(f"Error en la ejecución del análisis: {e}")
            


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

def extraer_texto_entre_delimitadores_v2(texto, delimitador_inicial, delimitador_final):
    pattern = re.compile(f"{delimitador_inicial}(.*?{delimitador_final}.*?)\.", re.DOTALL)
    match = pattern.search(texto)
    return match.group(0) if match else "ERROR EXTRAYENDO TEXTO"



def crear_docbin(datos_entrenamiento, nlp):
    doc_bin = DocBin()
    for texto, annot in datos_entrenamiento:
        doc = nlp.make_doc(texto)
        ents = []
        for start, end, label in annot["entities"]:
            span = doc.char_span(start, end, label=label)
            if span is None:
                continue
            ents.append(span)
        doc.ents = ents
        doc_bin.add(doc)
    return doc_bin





file = "plan_expansion_final_2023.pdf"
nlp = spacy.load("es_core_news_lg")
diccionario_obras_nuevas, diccionario_lineas_nuevas = generar_diccionario_proyectos_v2(file)


descripciones_obras_nuevas = extraer_descripciones(file, diccionario_obras_nuevas)

textos = []

for titulo, descripcion in descripciones_obras_nuevas.items():
    print(f"Titulo: {titulo}")
    print("\n\n")

    texto = extraer_texto_entre_delimitadores_v2(descripcion, "Descripción general y ubicación", ".")
    print(texto)
    print("\n\n")
    textos.append((str(texto)))

datos_entrenamiento = []
nlp = spacy.load("es_core_news_sm")
datos_entrenamiento = crear_datos_entrenamiento(textos, nlp, datos_entrenamiento)


file2 = "plan_expansion_definitivo_2022.pdf"
diccionario_obras_nuevas2, diccionario_lineas_nuevas2 = generar_diccionario_proyectos_v2(file2)

descripciones_obras_nuevas2 = extraer_descripciones(file2, diccionario_obras_nuevas2)

textos2 = []

for titulo, descripcion in descripciones_obras_nuevas2.items():
    print(f"Titulo: {titulo}")
    print("\n\n")

    texto = extraer_texto_entre_delimitadores_v2(descripcion, "Descripción general y ubicación", ".")
    print(texto)
    print("\n\n")
    textos2.append((str(texto)))


datos_entrenamiento = crear_datos_entrenamiento(textos2, nlp, datos_entrenamiento)
breakpoint()




nlp = spacy.blank("es")
docbin = crear_docbin(datos_entrenamiento, nlp)
docbin.to_disk("datos_entrenamiento.spacy")


#ahora, vamos a crear datos de dev.spacy

file = "plan_expansion_definitivo_2021.pdf"
nlp = spacy.load("es_core_news_lg")
diccionario_obras_nuevas, diccionario_lineas_nuevas = generar_diccionario_proyectos_v2(file)

descripciones_obras_nuevas3 = extraer_descripciones(file, diccionario_obras_nuevas)

textos3 = []

for titulo, descripcion in descripciones_obras_nuevas3.items():
    print(f"Titulo: {titulo}")
    print("\n\n")

    texto = extraer_texto_entre_delimitadores_v2(descripcion, "Descripción general y ubicación", ".")
    print(texto)
    print("\n\n")
    textos3.append((str(texto)))

datos_dev = []

nlp = spacy.load("es_core_news_sm")
datos_dev = crear_datos_entrenamiento(textos3, nlp, datos_dev)
breakpoint()

nlp = spacy.blank("es")
docbin = crear_docbin(datos_dev, nlp)
docbin.to_disk("datos_dev.spacy")




