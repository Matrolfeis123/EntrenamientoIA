# En este script manejaremos todo lo relacionado con la clase patio. 
# Esta clase sera instanciada cada vez que se encuentre un patio en el texto extraido de los PDFs.

import re
from funciones_extra import extraer_texto_entre_delimitadores_v2


class Patio_deprecated:
    def __init__(self, nombre, configuracion, numero_posiciones=None, conexiones=None, proyecto_padre=None):
        #self.nlp = spacy.load("es_core_news_lg") # Esto probablemente no sea necesario y haga que el programa sea mas lento
        self.nombre = nombre # patio de X kV
        self.configuracion = configuracion # interruptor y medio, interruptor y medio, interruptor y medio
        self.posiciones_disponibles = 0
        self.numero_posiciones = numero_posiciones
        self.proyecto_padre = proyecto_padre

        self.parrafo_desc = None # Aca guardare el parrafo que describe al patio, en forma de texto

        ## Quizas podria guardar un doc correspondiente al parrafo que lo describe. Esto podria ser util para futuras referencias
        ## Por otro lado, tambien podria guardar el indice de comienzo y fin del parrafo que lo describe


    def __str__(self):
        return f"{self.nombre} del proyecto {self.proyecto_padre.nombre}, con configuración {self.configuracion}. Número de posiciones: {self.numero_posiciones}"


    def __repr__(self):
        return f"{self.nombre}"


    def set_indices(self, inicio, fin):
        self.indices = (inicio, fin)
        return self.indices


    def extraer_numero_posiciones(self):
        numeros = {
            "uno": 1,
            "dos": 2,
            "tres": 3,
            "cuatro": 4,
            "cinco": 5,
            "seis": 6,
            "siete": 7,
            "ocho": 8,
            "nueve": 9,
            "diez": 10
        }

        # Crear doc para el parrafo que describe al patio
        doc = self.proyecto_padre.nlp(self.parrafo_desc)

        # vamos a iterar sobre los tokens del doc y buscar el token que contenga la palabra "posiciones" o "diagonales"
        for token in doc:
            if (token.text == "posiciones" or token.text == "diagonales") and doc[token.i -1].like_num:
                # Si encontramos la palabra "posiciones" o "diagonales", vamos a buscar el token anterior para ver si contiene un numero
                numero = numeros.get(doc[token.i - 1].text, doc[token.i - 1].text)

                if token.text == "diagonales":
                    self.numero_posiciones = numero * 2
                    #print(f"El patio {self.nombre} tiene {self.numero_posiciones} posiciones")

                elif token.text == "posiciones":
                    self.numero_posiciones = numero
                    #print(f"El patio {self.nombre} tiene {self.numero_posiciones} posiciones")

                else:
                    print("No se encontraron coincidencias")
                    self.numero_posiciones = None

            elif (token.text == "paños") and doc[token.i -1].like_num:
                numero = numeros.get(doc[token.i - 1].text, doc[token.i - 1].text)
                self.numero_posiciones = str(numero)+" paño(s)"



        return ""


    def extraer_conexiones(self):
        try:
            doc = self.proyecto_padre.nlp(self.parrafo_desc)

            matcher = Matcher(self.proyecto_padre.nlp.vocab)

            patron_conexiones_inicio = [{"LOWER": "de"}, {"LOWER": "manera"}, {"LOWER": "de"}, {"LOWER": "permitir"}, {"LOWER": "la"}, {"LOWER": "conexión"}]
        

            matcher.add("conexiones", [patron_conexiones_inicio])

            matches = matcher(doc)

            if matches:
                #vamos a seleccionar el indice end del primer match
                end = matches[0][2]
                #print("Indice de fin del match:", end)
                # vamos a separar el texto desde el indice end hasta el final del doc, aplicando el metodo split tal que separe por comas en una lista
                #primero, vamos a reemplazar las y por comas del texto. Luego, aplicaremos el split
                #ANTES:
                # texto = doc[end:].text.replace(" y ", ",")
                # conexiones = texto.split(",")

                #AHORA: No vamos a reemplazar las y por comas, ya que en algunos casos, las y son necesarias para la correcta interpretacion de las conexiones. Ademas,
                # para el caso "nuevos proyectos en la zona", no es necesario hacer el reemplazo

                conexiones = doc[end:].text.split(",")

                self.lista_conexiones = conexiones

            else:
                # Vamos a tomar todo el texto desde la palabra paños, hasta el punto final del parrafo, con el matcher
                patron_alternativo = [{"LOWER": "paños"}, {"LOWER": "para"}, {"LOWER": {"IN": ["alimentador", "alimentadores"]}}]
                matcher2 = Matcher(self.proyecto_padre.nlp.vocab)
                matcher2.add("conexiones", [patron_alternativo])

                matches = matcher2(doc)

                if matches:
                    end = matches[0][2]
                    conexiones = doc[end:].text.split(",")
                    self.lista_conexiones = conexiones



                else:
                    print("No se encontraron coincidencias")
                    self.lista_conexiones = None

        except Exception as e:
            print(f"Error: {e}")
            self.lista_conexiones = None #Podria manejar un mensaje tipo N/A o None, para manejar el caso en otras funciones

        return ""


    def calcular_posiciones_disponibles(self):

        numeros = {
            "uno": 1,
            "dos": 2,
            "tres": 3,
            "cuatro": 4,
            "cinco": 5,
            "seis": 6,
            "siete": 7,
            "ocho": 8,
            "nueve": 9,
            "diez": 10
        }

        ########## IMPORTANTE: ##########
        ### Aun no me hago cargo de los siguientes casos:
        ### - la conexión de la nueva línea 2x110 kV Olmué – Quillota
        ### - la conexión de la obra “Nueva S/E Rukapillan

        ### Ademas, tengo un problema con:
        ### - Cuando tengo mas de un patio, no se ejecuta el calculo de posiciones disponibles para ambos casos.



        ########### OJO CON LOS SIGUIENTES CASOS: ################
        ### - la conexión de los seccionamientos de las líneas 1x66 kV Arenas Blancas – Coronel
        ### - 1x66 kV Bocamina – Coronel
        ###
        ### EN ESTE CASO, AMBAS LINEAS CORRESPONDEN A SECCIONAMIENTOS, COMO LO DIFERENCIO DE LA CONEXION DE UNA LINEA? QUIZAS NO ES NECESARIO ###

        if isinstance(self.numero_posiciones, str):
            self.posiciones_disponibles = self.numero_posiciones
            return "" 

        else:
            try:
                self.posiciones_disponibles = int(self.numero_posiciones)

                #Esta funcion se ejecuta para cada patio, es decir, si hay mas de un patio, se ejecutara desde el principio para cada uno de ellos

                for conexion in self.lista_conexiones:

                    # Todas estas condiciones podria pasar a lower o lemma con spacy, tal que no tenga que hacer tantas comparaciones(?)

                    if "seccionamiento" in conexion:
                        # En este caso, se debe buscar la configuracion de la linea seccionada, contenida en conexiones con un patron del tipo dxddd, donde nos interesa el digito antes de la x.
                        # Podriamos buscar el patron {"SHAPE": {"IN":["dxddd", "dxdd", "dxd", "ddxd", "ddxdd", "ddxddd", "dddxd", "dddxdd", "dddxddd"]}, "OP": "+"} con el matcher
                        patron = r'\b\d+x\d{2,3}\b'
                        match = re.findall(patron, conexion)
                        ## OJO EN ESTE CASO, TENGO QUE HACER LA DIFERENCIA ENTRE EL SECCIONAMIENTO Y UNA NUEVA LINEA UNICAMENTE??
                        # ES DECIR, ES DISTINTO "EL SECCIONAMIENTO DE ... 2x110 ..." QUE "la conexión de la nueva línea 2x110 "

                        if match:
                            for tension in match:
                                posic_ocup = int(tension[0])*2
                                self.posiciones_disponibles -= posic_ocup

                        else:
                            print("No se encontraron coincidencias")


                    elif ("la conexión de la línea") in conexion:

                        patron = r'\b\d+x\d{2,3}\b'
                        match = re.search(patron, conexion)

                        if match:
                            #print("Configuracion de la linea seccionada:", match.group())
                            posic_ocup = int(match.group()[0])
                            self.posiciones_disponibles -= posic_ocup

                        else:
                            print("No se encontraron coincidencias")

                    elif "la conexión de la nueva línea" in conexion:
                        patron = r'\b\d+x\d{2,3}\b'
                        match = re.search(patron, conexion)

                        if match:
                            #print("Configuracion de la linea seccionada:", match.group())
                            posic_ocup = int(match.group()[0])
                            self.posiciones_disponibles -= posic_ocup

                        else:
                            print("No se encontraron coincidencias")


                    elif "la conexión de las líneas" in conexion:
                        patron = r'\b\d+x\d{2,3}\b'
                        match = re.search(patron, conexion)

                        if match:
                            #print("Configuracion de la linea seccionada:", match.group())
                            posic_ocup = int(match.group()[0])
                            self.posiciones_disponibles -= posic_ocup

                        else:
                            print("No se encontraron coincidencias")

                    elif "la conexión de la obra" in conexion:

                        patron = r'\b\d+x\d{2,3}\b'
                        coincidencias = re.findall(patron, conexion)

                        if coincidencias:
                            for coincidencia in coincidencias:
                                posic_ocup = int(coincidencia[0])
                                self.posiciones_disponibles -= posic_ocup

                        else:
                            print("Problemas posiciones nuevas obras, calculo posiciones.")


                    elif "transformador" in conexion and "banco" not in conexion:
                        # un transformador utiliza una unica posicion
                        self.posiciones_disponibles -= 1



                    elif "paño" in conexion:
                        if "paño acoplador" in conexion and "paño seccionador" in conexion:
                            self.posiciones_disponibles -= 2

                        elif "paño acoplador" in conexion:
                            #print("ACOPLADOR")
                            self.posiciones_disponibles -= 1

                        elif "paño seccionador" in conexion:
                            #print("SECCIONADOR")
                            self.posiciones_disponibles -= 1

                        else:
                            print("Revisar tipo de paño a conectar xdddd")
                            continue


                    else:
                        patron_tension = r'\b\d+x\d{2,3}\b'
                        match = re.findall(patron_tension, conexion)

                        if match:
                            for tension in match:
                                posic_ocup = int(tension[0])
                                self.posiciones_disponibles -= posic_ocup

                        else:
                            if "bancos" in conexion:
                                # vamos a buscar dentro de la descripcion del proyecto padre

                                doc = self.proyecto_padre.doc
                                #vamos a buscar la palabra banco o bancos, y si la palabra anterior a esta es un numero, entonces tomamos ese numero como la cantidad de bancos
                                for token in doc:
                                    if token.text == "bancos" and doc[token.i - 1].like_num:

                                        numero = numeros.get(doc[token.i - 1].text, doc[token.i - 1].text)
                                        posic_ocup = int(numero)
                                        self.posiciones_disponibles -= posic_ocup
                                        #print("FUNCIONO BRODER")
                                        break

                            elif "banco" in conexion:
                                self.posiciones_disponibles -= 1
                                


                            else:
                                #print(f"No se encontraron coincidencias para {conexion}")
                                continue


                return ""
        
            except Exception as e:
                print(f"Error: {e}")
                return ""




class Patio:
    def __init__(self, descripcion: str, patio_paño_alimentador: bool, proyecto_padre=None):
        self.texto = descripcion
        self.patio_paño_alimentador = patio_paño_alimentador
        self.proyecto_padre = proyecto_padre

        self.nombre = None
        self.tension = None
        self.configuracion = None
        self.posiciones = 0
        self.lista_conexiones = None
        self.posiciones_disponibles = 0

    def __str__(self) -> str:
        return f"{self.nombre} de {self.tension} kV, con configuración {self.configuracion}. Número de posiciones: {self.posiciones_disponibles}"
    
    def __repr__(self) -> str:
        return f"{self.nombre}"
    
    def imprimir_resumen_patio(self):
        print(f"Nombre: {self.nombre}")
        print(f"Tensión: {self.tension}")
        print(f"Configuración: {self.configuracion}")
        print(f"Número de posiciones totales: {self.posiciones}")
        print(f"Posiciones disponibles: {self.posiciones_disponibles}")
        print(f"Conexiones: {self.lista_conexiones}")
    
    def procesar_patio(self):
        self.nombre = self.extraer_tension()
        self.tension = self.nombre
        self.configuracion = self.extraer_configuracion()
        self.posiciones = self.extraer_numero_posiciones()
        self.lista_conexiones = self.extraer_conexiones()
        self.calcular_posiciones_disponibles()
    
    def extraer_configuracion(self):
        l_configs = ["barra principal seccionada y barra de transferencia", "interruptor y medio", "doble barra principal y barra de transferencia", "doble barra principal y barra de transferencia", "doble barra principal con barra de transferencia", "barra simple"]

        for config in l_configs:
            if config in self.texto:
                return config
                
        return "No se pudo extraer la configuración"
            
    def extraer_tension(self):
        # vamos a buscar donde diga la frase "patio de X kV"
        pattern = re.compile(r'patio de \d+(?:,\d+)? kV')
        match = pattern.search(self.texto)

        if match:
            return match.group(0)
        
        else:
            return "No se pudo extraer la tensión"

    def extraer_numero_posiciones(self):
        #vAMOS A RETORNAR EL NUMERO DE POSICIONES O DIAGONALES QUE TIENE EL PATIO COMO INT, PARA FACILITAR LUEGO EL CALCULO DE POSICIONES DISPONIBLES
        numeros = {
            "uno": 1,
            "una": 1,
            "dos": 2,
            "tres": 3,
            "cuatro": 4,
            "cinco": 5,
            "seis": 6,
            "siete": 7,
            "ocho": 8,
            "nueve": 9,
            "diez": 10
        }

        # Patrones de búsqueda para posiciones, diagonales y paños
        patron_posiciones_diagonales = re.compile(r'\b(\d+|uno|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez) (posiciones|diagonales)\b', re.IGNORECASE)
        patron_panos = re.compile(r'\b(\d+|uno|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez) (paño|paños)\b', re.IGNORECASE)

        # Buscar coincidencias en el texto
        match_posiciones_diagonales = patron_posiciones_diagonales.search(self.texto)
        match_panos = patron_panos.search(self.texto)

        if match_posiciones_diagonales:
            numero_str, tipo = match_posiciones_diagonales.groups()
            numero = numeros.get(numero_str.lower(), int(numero_str) if numero_str.isdigit() else 0)

            if tipo.lower() == "diagonales":
                return numero * 2
            elif tipo.lower() == "posiciones":
                return numero
            
        elif match_panos:
            numero_str = match_panos.group(1)
            numero = numeros.get(numero_str.lower(), int(numero_str) if numero_str.isdigit() else 0)
            return f"al menos {numero} paño(s)"

        return ""

    def extraer_conexiones(self):

        def limpiar_conexion(conexion):
        # Eliminar artículos y preposiciones iniciales
            conexion = re.sub(r'^(el |la |los |las |del |de |a |en |para |la conexión de |la construcción de |del |un |una |)', '', conexion, flags=re.IGNORECASE).strip()
            return conexion
        
        try:
            patron_conexiones_inicio = re.compile(r'\bde manera de permitir la conexión\b(.*?)(\.\s|$)', re.IGNORECASE | re.DOTALL)
            patron_alternativo = re.compile(r'\bpaños para (alimentador|alimentadores)\b(.*?)(\.\s|$)', re.IGNORECASE | re.DOTALL)




            match_conexiones_inicio = patron_conexiones_inicio.search(self.texto)
            match_alternativo = patron_alternativo.search(self.texto)

            if match_conexiones_inicio:
                
                conexiones = match_conexiones_inicio.group(1).replace("y la", ",").split(",")
                lista_conexiones = [limpiar_conexion(conexion.strip()) for conexion in conexiones]
                return lista_conexiones

            elif match_alternativo:
                conexiones = match_alternativo.group(0).split(",")
                lista_conexiones = [limpiar_conexion(conexion.strip()) for conexion in conexiones]
                return lista_conexiones

            else:
                conexiones = ""
                return []


        except Exception as e:
            print(f"Error extraccion conexiones: {e}")


        return []
    
    def calcular_posiciones_disponibles(self):
        numeros = {
            "uno": 1,
            "una": 1,
            "dos": 2,
            "tres": 3,
            "cuatro": 4,
            "cinco": 5,
            "seis": 6,
            "siete": 7,
            "ocho": 8,
            "nueve": 9,
            "diez": 10
        }

        if isinstance(self.posiciones, str):
            self.posiciones_disponibles = self.posiciones
            return ""
        
        else:
            try:

                self.posiciones_disponibles = int(self.posiciones)

                for conexion in self.lista_conexiones:

                    if "seccionamiento" in conexion:
                        patron = r'\b(\d+)x\d{2,3}\b'
                        match = re.findall(patron, conexion)
                        if match:
                            for tension in match:
                                posic_ocup = int(tension[0])*2 #OJO ACA, pq [0]? 
                                self.posiciones_disponibles -= posic_ocup
                        else:
                            print("No se encontraron coincidencias")


                    elif ("la conexión de la línea") in conexion:
                        patron = r'\b(\d+)x\d{2,3}\b'
                        match = re.search(patron, conexion)
                        if match:
                            posic_ocup = int(match.group()[0]) #Ojo aca tmb
                            self.posiciones_disponibles -= posic_ocup
                        else:
                            print("No se encontraron coincidencias")

                    elif "la conexión de la nueva línea" in conexion:
                        patron = r'\b(\d+)x\d{2,3}\b'
                        match = re.search(patron, conexion)
                        if match:
                            posic_ocup = int(match.group()[0])
                            self.posiciones_disponibles -= posic_ocup
                        else:
                            print("No se encontraron coincidencias")


                    elif "la conexión de las líneas" in conexion:
                        patron = r'\b(\d+)x\d{2,3}\b'
                        match = re.search(patron, conexion)

                        if match:
                            posic_ocup = int(match.group()[0])
                            self.posiciones_disponibles -= posic_ocup
                        else:
                            print("No se encontraron coincidencias")

                    elif "la conexión de la obra" in conexion:
                        patron = r'\b(\d+)x\d{2,3}\b'
                        coincidencias = re.findall(patron, conexion)

                        if coincidencias:
                            for coincidencia in coincidencias:
                                posic_ocup = int(coincidencia[0])
                                self.posiciones_disponibles -= posic_ocup

                        else:
                            print("Problemas posiciones nuevas obras, calculo posiciones.")


                    elif "transformador" in conexion and "banco" not in conexion:
                        self.posiciones_disponibles -= 1



                    elif "paño" in conexion:
                        if "paño acoplador" in conexion and "paño seccionador" in conexion:
                            self.posiciones_disponibles -= 2

                        elif "paño acoplador" in conexion:
                            self.posiciones_disponibles -= 1

                        elif "paño seccionador" in conexion:
                            self.posiciones_disponibles -= 1

                        else:
                            print("Revisar tipo de paño a conectar xdddd")
                            continue

                    else:
                        patron_tension = r'\b(\d+)x\d{2,3}\b'
                        match = re.findall(patron_tension, conexion)
                        if match:
                            for tension in match:
                                posic_ocup = int(tension)
                                self.posiciones_disponibles -= posic_ocup
                        else:
                            ####################################################
                            #### REVISAR ESTA LOGICA!!!! 05/06/2024

                            if "bancos de autotransformadores" in conexion:
                                # Vamos a buscar en la descripcion del texto la palabra bancos y si la palabra anterior a esta es un numero, entonces tomamos ese numero como la cantidad de bancos
                                doc = self.proyecto_padre.doc
                                for token in doc:
                                    if token.text == "bancos" and doc[token.i - 1].like_num:
                                        numero = numeros.get(doc[token.i - 1].text, doc[token.i - 1].text)
                                        posic_ocup = int(numero)
                                        self.posiciones_disponibles -= posic_ocup
                                        break
                            
                            elif "bancos" in conexion:
                                # vamos a buscar dentro de la descripcion del proyecto padre

                                doc = self.proyecto_padre.doc
                                #vamos a buscar la palabra banco o bancos, y si la palabra anterior a esta es un numero, entonces tomamos ese numero como la cantidad de bancos
                                for token in doc:
                                    if token.text == "bancos" and doc[token.i - 1].like_num:

                                        numero = numeros.get(doc[token.i - 1].text, doc[token.i - 1].text)
                                        posic_ocup = int(numero)
                                        self.posiciones_disponibles -= posic_ocup
                                        #print("FUNCIONO BRODER")
                                        break

                            elif "banco" in conexion:
                                self.posiciones_disponibles -= 1
                            else:
                                continue

                            ##################################



            except Exception as e:
                print(f"Error: {e}")
                return ""



if __name__ == "__main__":
    texto = 'Además, el proyecto considera la construcción de un patio de 13,8 kV, en configuración barra simple, contemplándose la construcción de, al menos, cuatro paños para alimentadores, el paño de conexión para el transformador de poder 110/13,8 kV antes mencionado y espacio en barra y plataforma para la construcción de dos paños futuros.'

    patio = Patio(texto, False)
    patio.procesar_patio()
    patio.imprimir_resumen_patio()

