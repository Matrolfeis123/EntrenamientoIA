import spacy
from spacy.matcher import Matcher
import pdfplumber
import re
from spacy.tokens import DocBin


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


#vamos a cargar el modelo entrenado, que se encuentra en la carpeta output

nlp = spacy.load("output/model-best")

texto = "El proyecto incluye la construcción de una nueva subestación, denominada Tomeco, trol,feis madness."
texto2 = "4.2.1.1 Descripción general y ubicación de la obra El proyecto consiste en la construcción de una nueva subestación seccionadora, denominada Linderos, mediante el seccionamiento de las líneas 2x154 kV Alto Jahuel – Punta de Cortés y 1x66 kV Fátima – Buin, con sus respectivos paños de línea y patios en 154 kV, 66 kV y 15 kV. A su vez, el proyecto considera la instalación de un transformador de 154/66 kV de 75 MVA de capacidad y un transformador de 66/15 kV de 30 MVA de capacidad, ambos con Cambiador de Derivación Bajo Carga (CDBC) y sus respectivos paños de conexión en sus niveles de tensión correspondientes. Adicionalmente, el proyecto considera la construcción de enlaces para el seccionamiento de las líneas mencionadas en la subestación Linderos, manteniendo, al menos, las características técnicas de la línea que se secciona en 154 kV, mientras que, para la línea que se secciona de 66 kV, el enlace debe poseer un conductor con capacidad de trasmisión de, al menos, 58 MVA a 35°C temperatura ambiente con sol."

doc = nlp(texto2)

print("Entidades encontradas: ")
for ent in doc.ents:
    print(ent.text, ent.label_)