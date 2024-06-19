
import spacy
from spacy.matcher import Matcher
import re
from patio import Patio
from unidecode import unidecode
from nueva_linea import Linea


# Consulta chatgpt

# Muy bien, ahora necesito que me ayudes exclusivamente con el directorio src/obras_nuevas.
# Mi modulo de obras nuevas actualmente funciona con dos scripts, pero me gustaria modularizarlo aun mas. Por lo tanto, ayudame a tomar decisiones respecto a como debo modularizarlo.

# Primeramente, tenemos que dentro del desarrollo de mi codigo de obras nuevas, tengo la definicion de las clases Proyecto_nva_obra y Patio. Para los objetos de tipo Proyecto_nva_obra, tenemos que dentro de su definicion podrian tener uno o mas patios, donde cada patio guarda sus propias caracteristicas que luego debo consultar y escribir como resumen del proyecto. 

# Primeramente, tengo que mi codigo utiliza librerias para su funcionamiento. Ademas, importa el modulo "funciones_extra", las cuales no tienen que ver con la clase "



nlp = spacy.load("es_core_news_lg")

class Proyecto_nva_obra:
    def __init__(self, texto):
        self.nlp = nlp
        self.doc = self.nlp(texto)
        self.nombre_proyecto = None
        self.nombre = None
        self.tipo = "Nueva S/E"
        self.ubicacion = None
        self.patios = []

        self.decreto = None #Atributo que almacena el decreto de adjudicacion o donde se extrajo la info mas actualizada
        self.info_trafo = None #Este atributo es pensado en los atributos que tienen las S/E en el KML
        self.estado = None #Estados = preliminar, decreto, licitacion, adjudicado, etc.
        self.fecha_actualizacion = None #Propuesta de variable para controlar la ultima actualizacion del mapa

    def __str__(self):
        return f"Nombre: {self.nombre}, Tipo: {self.tipo}, Patios: {self.patios}"
    
    def procesar_descripcion(self):
        self.nombre = f"S/E {self.extraer_nombre()}"
        # self.nombre = f"S/E {self.nombre}"
        # self.tipo = self.extraer_tipo()
        self.patios = self.extraer_patios_original()
        self.ubicacion = self.extraer_ubicacion()

    def resumen_proyecto_por_patio(self, data):
        # Resumen del proyecto
        print(f"---------Resumen proyecto: {self.nombre}:------------------------\n")
        print(f"Nombre del proyecto: {self.nombre}")
        print(f"Tipo de proyecto: {self.tipo}")
        print(f"Número de patios: {len(self.patios)}")
        print("\n")

        # Resumen por patios
        print(f"---------Resumen patios de {self.nombre}:------------------------\n")
        for patio in self.patios:
            print(f"Nombre del patio: {patio.nombre}")
            print(f"Configuración: {patio.configuracion}")
            print(f"Número de posiciones: {patio.numero_posiciones}")


            # Verificar si hay conexiones para este patio
            if hasattr(patio, 'lista_conexiones'):
                print("Conexiones:")
                for conexion in patio.lista_conexiones:
                    print(f"- {conexion.strip()}")  # Eliminar espacios en blanco alrededor de las conexiones
            else:
                print("No se encontraron conexiones para este patio")

            print("\n")

            # Calcular posiciones disponibles del patio
            patio.calcular_posiciones_disponibles()
            print("Posiciones Disponibles: ", patio.posiciones_disponibles, "\n")

        # Agregar los datos a la lista de datos
        data.append([self.nombre, len(self.patios),  patio.posiciones_disponibles])

    def extraer_nombre(self):
        try:
            pattern = r"(?<=nueva subestación, denominada )[^,]+" # Expresión regular para extraer el nombre del proyecto
            match = re.search(pattern, self.doc.text)
            if match:
                return match.group(0)
            else:
                raise ValueError("No se encontró el nombre del proyecto")
            
        except ValueError as e:
            print(f"Error: {e}")
            print("\n")

    def extraer_patios_original(self):

        try:
            
            patios_matcher = Matcher(self.nlp.vocab)

            patron_simple = [{"POS": "DET"}, {"POS": "NOUN"}, {"POS": "ADP"},
                                    {"POS": "NOUN"}, {"POS": "ADP"}, {"POS": "NUM"},
                                    {"POS": {"IN": ["NOUN", "PROPN"]}}]

            pattern_especifico = [{"POS": "NOUN"}, {"POS": "ADP"}, {"POS": "NUM"},
                                {"POS": "NUM"}, {"POS": "ADP"}, {"POS": "NOUN"},
                                {"POS": "NOUN"}, {"POS": "CCONJ"}]

            pattern_patio_adicional = [{"POS": "DET"}, {"POS": "NOUN"}, {"POS": "VERB"}, {"POS": "DET"}, {"POS": "NOUN"}, {"POS": "ADP"}, {"POS": "DET"}, {"POS": "NOUN"}, {"POS": "ADP"}]
            patios_matcher.add("patios", [patron_simple, pattern_especifico, pattern_patio_adicional])


            ##################################################################################
            ##### Vamos a definir 2 listas, las cuales me serviran para almacenar los    #####
            ##### indices de comienzo y termino de los parrafos que describen los patios #####
            ##################################################################################

            l_start_por_patio = []
            l_end_por_patio = []

            ##################################################################################

            matches = patios_matcher(self.doc)
            l_patios = []
            lista_objetos_patios = []
            for match_id, start, end in matches:
                span = self.doc[start:end+45] # Aca extraigo el parrafo del tipo "La config. del patio de X kV ..."
                                                # Por lo tanto, aca podria crear un nuevo objeto Patio y asignarle los atributos correspondientes
                #print(span.text)
                l_configs = ["barra principal seccionada y barra de transferencia", "interruptor y medio", "doble barra principal y barra de transferencia", "doble barra principal y barra de transferencia", "doble barra principal con barra de transferencia", "barra simple"]
                for token in span:
                    if token.text == "patio" and self.doc[token.i+1].text == "de":
                        l_patios.append(self.doc[token.i:token.i+4]) #creo que esto no lo uso finalmente
                        l_start_por_patio.append(token.i-3)
                        nombre_patio = self.doc[token.i:token.i+4]
                        #print("Nombre del patio:", nombre_patio)
                        doc_patio = self.doc[token.i:token.i+4] # Redundante, pero por claridad

                        for config in l_configs:
                            if config in span.text:
                                #print("Configuración del patio:", config)
                                configuracion_patio_actual = config
                                break

                            else:
                                configuracion_patio_actual = "Desconocida"

                        # Crear un objeto Patio
                        patio = Patio(nombre_patio, configuracion_patio_actual, proyecto_padre=self)
                        lista_objetos_patios.append(patio)

            patron_fin = [{"LOWER": "la"}, {"LOWER": "conexión"}, {"LOWER": "de"}, {"LOWER": "nuevos"}, {"LOWER": "proyectos"}, {"LOWER": "en"}, {"LOWER": "la"}, {"LOWER": "zona"}]
            patron_fin_2 = [{"LOWER": "conexión"}, {"LOWER": "de"}, {"LOWER": "un"}, {"LOWER": "nuevo"}, {"LOWER": "proyecto"}, {"LOWER": "en"}, {"LOWER": "la"}, {"LOWER": "zona"}]
            patron_fin_3 = [{"POS": "NOUN"}, {"POS": "ADP"}, {"POS": "NOUN"}, {"POS": "CCONJ"},
                            {"POS": "NOUN"}, {"POS": "ADP"}, {"POS": "DET"}, {"POS": "NOUN"},
                            {"POS": "ADP"}, {"POS": "NUM"}, {"POS": "NOUN"}]

            matcher_fin = Matcher(nlp.vocab)
            matcher_fin.add("FraseClave", [patron_fin, patron_fin_2, patron_fin_3])

            matches = matcher_fin(self.doc)

            if matches:
                for match_id, start, end in matches:
                    span = self.doc[start:end]
                    #print(span.text)

                    if end not in l_end_por_patio:
                        l_end_por_patio.append(end)

                #print("Indices de comienzo de los patios:", l_start_por_patio)
                #print("Indices de fin de los patios:", l_end_por_patio)

            else:
                #vamos a definir el indice de fin como el ultimo punto del parrafo
                doc_aux = self.doc[l_start_por_patio[-1]:]
                for token in doc_aux:
                    if token.text == ".":
                        l_end_por_patio.append(token.i)
                        break


            for i, patio in enumerate(lista_objetos_patios):
                try:
                    patio.set_indices(l_start_por_patio[i], l_end_por_patio[i])
                    #print(patio.indices)

                    patio.parrafo_desc = self.doc[patio.indices[0]:patio.indices[1]].text

                    #print(patio.parrafo_desc)
                    #print("-------------------------------------------------")
                    patio.extraer_numero_posiciones()
                    #print("-------------------------------------------------")
                    patio.extraer_conexiones()
                    #print("-------------------------------------------------")

                except Exception as e:
                    print(f"Error: {e}")
                    continue


            return lista_objetos_patios
    
        except Exception as e:
            print(f"Error: {e}")
            return []

    def extraer_ubicacion(self):
        try:
            # Vamos a extraer la ubicación del proyecto, que se encuentra en la descripción del proyecto
            # Ejemplos de descripción de ubicación de Nuevas S/E:

            # NUEVA S/E VALENTÍN LETELIER: "La subestación se deberá emplazar a aproximadamente 3 km al norte de la S/E Chacahuín siguiendo el trazado de la línea 1x66 kV Chacahuín – Tap Putagán, dentro de un radio de 2 km respecto de ese punto" .

            # Subestación en el este de la subestación Mulchén: "La subestación se deberá emplazar a aproximadamente 8 km hacia el este de la subestación Mulchén, siguiendo el trazado de la línea 2x220 kV Mulchén – Los Notros, dentro de un radio de 3 km respecto de ese punto" .

            # Subestación al norte de la S/E Hualpén: "La subestación se deberá emplazar a aproximadamente 1,5 km al norte de la S/E Hualpén siguiendo el trazado de la línea 2x154 kV Hualpén – San Vicente, dentro de un radio de 1,5 km respecto de ese punto" .

            # Subestación hacia el este de la subestación Villarrica: "La subestación se deberá emplazar a aproximadamente 16 km hacia el este de la subestación Villarrica, siguiendo el trazado de la línea 1x66 kV Villarrica – Pucón, dentro de un radio de 2 km respecto de ese punto" .

            # Subestación al norte de la S/E Chacahuín: "La subestación se deberá emplazar a aproximadamente 3 km al norte de la S/E Chacahuín siguiendo el trazado de la línea 1x66 kV Chacahuín – Tap Putagán, dentro de un radio de 2 km respecto de ese punto" .

            # Subestación hacia el norte de la subestación Cerro Navia: "La subestación se deberá emplazar a aproximadamente 3 km hacia el norte de la subestación Cerro Navia, siguiendo el trazado de la línea 2x220 kV Cerro Navia – Nueva Lampa, dentro de un radio de 2,5 km respecto de ese punto" .

            # Estos ejemplos muestran diferentes formas de describir la ubicación de proyectos de nuevas subestaciones eléctricas en relación con subestaciones existentes y líneas de transmisión cercanas.
                                    
            matcher = Matcher(self.nlp.vocab)

            # Vamos a identificar el inicio buscando el párrafo que contenga "la subestación se deberá emplazar", y se guardará el párrafo desde ese punto hasta el punto final del párrafo
            patron_inicio = [{"LOWER": "la"}, {"LOWER": "subestación"}, {"LOWER": "se"}, {"LOWER": "deberá"}, {"LOWER": "emplazar"}]
            matcher.add("ubicacion", [patron_inicio])

            matches = matcher(self.doc)

            if matches:
                inicio = matches[0][1]
                final = inicio

                # Vamos a buscar el índice de fin, que será el primer punto que se encuentre después del índice de inicio
                for token in self.doc[inicio:]:
                    if token.text == ".":
                        final = token.i
                        break

                ubicacion = self.doc[inicio:final].text
                return ubicacion
            else:
                # Si no se encontraron coincidencias, lanzamos una excepción
                raise Exception("No se encontró la descripción de ubicación en el documento.")

        except Exception as e:
            print("Error al extraer la ubicación:", e)
            return str(e)





class Proyecto:
    def __init__(self, titulo, texto) -> None:
        self.nlp = nlp
        self.doc = self.nlp(texto)
        self.texto = texto
        self.indices = None
        
        self.nombre_proyecto = titulo
        self.nombre_se = None
        self.tipo = "Nueva S/E"
        self.ubicacion = None
        self.patios = []
        self.nuevas_lineas = []

        self.valor_inversion = None
        self.entrada_operacion = None

        self.decreto = "PET Final 2023"
        self.resumen = None

    def __str__(self):
        return f"Nombre: {self.nombre_proyecto}, Tipo: {self.tipo}, Patios: {self.patios}"
    
    def procesar_descripcion(self):
        self.indices = self.encontrar_indices_parrafos()
        self.resumen = self.extraer_resumen()
        self.nombre_se = f"S/E {self.extraer_nombre()}"
        self.entrada_operacion = self.extraer_entrada_operacion()
        self.valor_inversion = self.extraer_valor_inversion()
        self.ubicacion = self.extraer_ubicacion()
        self.extraer_descripcion_patios()
        self.imprimir_resumen()
        #self.extraer_descripcion_nueva_linea() Esta funcion la vamos a ejecutar cuando estemos procesando las nuevas lineas
        pass
        
    def encontrar_indices_parrafos(self):

        """
        La funcion devolverá una lista, donde cada elemento es la posición de inicio de un párrafo en la descripción.
        Se considera que un párrafo inicia con una de las frases de inicio definidas en la lista frases_inicio.

        Se pueden utilizar dichos indices para extraer los parrafos de la descripcion segun se necesite.
        Por ejemplo, para separar los distintos patios, lineas nuevas, etc.
        """



        # Lista de frases de inicio de los párrafos
        frases_inicio = [
            "El proyecto consiste en",
            "A su vez, el proyecto incluye",
            "A su vez, el proyecto considera",
            "A su vez, el proyecto consiste en",
            "A su vez, el proyecto contempla",
            "Por su parte",
            "La configuración del patio",
            "Adicionalmente, el proyecto considera",
            "Adicionalmente, el proyecto contempla",
            "Además, el proyecto contempla",
            "Además, el proyecto considera",
            "La capacidad de barras",
            "La subestación se deberá emplazar",
            "Finalmente, el proyecto"
        ]
    
        # Crear un patrón de expresión regular que busque todas las frases de inicio
        pattern = re.compile('|'.join(re.escape(frase) for frase in frases_inicio))

        # Encontrar todas las posiciones de inicio de las frases
        indices = [match.start() for match in pattern.finditer(self.texto)]
        
        return indices
    
    def encontrar_indices_nuevas_lineas(self):
        # Vamos a buscar las líneas nuevas en el texto
        # Las líneas nuevas se describen en el texto con la frase:
        # "la construcción de una nueva línea de transmisión"

        # Crear un patrón de expresión regular para buscar la frase
        patron = re.compile(r"la construcción de una nueva línea de transmisión", re.IGNORECASE)

        # Buscar todas las coincidencias en el texto
        matches = patron.finditer(self.texto)
        indices = [match.start() for match in matches]

        return indices

    def extraer_descripcion_nueva_linea(self):
        # Vamos a extraer el párrafo que contiene la descripción de la nueva línea de transmisión
        # La descripción de la nueva línea de transmisión se encuentra en el texto con la frase:
        # "la construcción de una nueva línea de transmisión"

        indices = self.encontrar_indices_nuevas_lineas()

        for indice in indices:
            # Extraer el párrafo que contiene la descripción de la nueva línea de transmisión
            if "la construcción de una nueva línea de transmisión" in self.texto[indice:]:
                # Encontrar el índice de fin del párrafo
                print("Nueva linea encontrada!!!")

                indice_fin = self.texto.find(".", indice)
                
                # Extraer el párrafo
                parrafo = self.texto[indice:indice_fin+1]

                linea = Linea(parrafo, self.decreto, self.nombre_proyecto, self.valor_inversion, self.entrada_operacion)
                self.nuevas_lineas.append(linea)
                return linea
            
            else:
                print("No hay nueva linea")
                return None

    def extraer_resumen(self):
        primer_y_segun_parrafo = self.texto[self.indices[0]:self.indices[2]]
        patron_separador = r'\d+—–——–'
        primer_y_segun_parrafo = re.sub(patron_separador, "", primer_y_segun_parrafo)

        return primer_y_segun_parrafo

    def extraer_nombre(self):
        #Quizas este paso esta de mas, ya que el nombre del proyecto esta en el titulo del diccionario
        try:
            pattern = r"(?<=nueva subestación, denominada )[^,]+" # Expresión regular para extraer el nombre del proyecto
            match = re.search(pattern, self.texto) #esto se puede reemplazar por texto
            if match:
                return match.group(0)
            else:
                raise ValueError("No se encontró el nombre del proyecto")
            
        except ValueError as e:
            print(f"Error: {e}")

    def extraer_valor_inversion(self):
        # Patrón de expresión regular para encontrar el valor de inversión
        patron = re.compile(r"(\d{1,3}(?:\.\d{3})*(?:,\d+)?) dólares", re.IGNORECASE)

        # Buscar el valor de inversión en la descripción
        match = patron.search(self.texto)

        if match:
            # Extraer y devolver la frase completa encontrada
            valor_inversion = match.group(0)
            return valor_inversion
        else:
            return None  # Devolver None si no se encuentra el valor de inversión

    def extraer_entrada_operacion(self):
        # patron que identifique la frase: El proyecto deberá ser construido y entrar en operación, a más tardar, dentro de los dd meses siguientes a la fecha de publicación en el Diario Oficial del respectivo decreto

        patron = re.compile(r"a más tardar, dentro de los \d{1,2} meses siguientes a la fecha de publicación en el Diario Oficial del respectivo decreto", re.IGNORECASE)

        match = patron.search(self.texto)

        if match:
            entrada_operacion = match.group(0)
            return entrada_operacion
        else:
            return None # Devolver None si no se encuentra la fecha de entrada en operación

    def extraer_parrafo_v3(self, indice_inicio):
        pattern = re.compile(r'(?<!\d)\.(?!\d)')

        match = pattern.search(self.texto, indice_inicio)
        if match:
            indice_fin = match.start()
            return self.texto[indice_inicio:indice_fin+1]
        
        else:
            return self.texto[indice_inicio:]

    def extraer_descripcion_patios(self):
        frases_patio = ["La configuración del patio", "la configuración del patio", "la construcción de un patio", "un patio de", "La capacidad de barras"]

        for indices in self.indices:
            parrafo = self.extraer_parrafo_v3(indices)
            if any(frase in parrafo for frase in frases_patio):
                # En este caso, el parrafo contiene información sobre los patios
                if ("considerar espacio en barras y plataforma" in parrafo or "considerar espacio en barra y plataforma" in parrafo):
                    # El parrafo contiene información sobre la configuración y posiciones de las barras y la plataforma
                    # Entonces, cada vez que entremos en este condicional, se tratara como un patio normal.
                    patio = Patio(parrafo, patio_paño_alimentador=False, proyecto_padre=self)

                else:
                    #en este caso, no hay informacion sobre el espacio de barras y plataforma, es decir, estamos frente a un patio de paños alimentadores.
                    # Entonces, cada vez que entremos en este condicional, se tratara como un patio de paños alimentadores (Excepto para el caso de tomeco!!)
                    # La unica diferencia entre uno y otro va a ser un booleano que se va a setear en el objeto Patio correspondiente.
                    patio = Patio(parrafo, patio_paño_alimentador=True, proyecto_padre=self)

                patio.procesar_patio()
                self.patios.append(patio)
                    
    def extraer_ubicacion(self):
        try:
            patron_inicio = re.compile(r'\bLa subestación se deberá emplazar\b', re.IGNORECASE)

            match = patron_inicio.search(self.texto)

            if match:
                inicio = match.start()
                final = self.texto.find(".", inicio)

                if final != -1:
                    ubicacion = self.texto[inicio:final]
                    return ubicacion
                
                else:
                    raise Exception("No se encontró el punto final de la ubicación")
                
            else:
                raise Exception("No se encontró la descripción de ubicación en el documento")
            
        except Exception as e:
            print("Error al extraer la ubicación:", e)
            return str(e)

    def imprimir_resumen(self):
        print(f"Nombre del proyecto: {self.nombre_se}")
        print(f"Valor de inversión: {self.valor_inversion}")
        print(f"Fecha de entrada en operación: {self.entrada_operacion}")
        print(f"Ubicación: {self.ubicacion}")
        print("\n")

        print("Resumen de patios:")
        for patio in self.patios:
            print(f"Nombre del patio: {patio.nombre}")
            print(f"Configuración: {patio.configuracion}")
            print(f"Número de posiciones: {patio.posiciones}")
            print(f"Conexiones: {patio.lista_conexiones}")
            print(f"Posiciones disponibles: {patio.posiciones_disponibles}")
            print("\n")

        print("-"*100)

    def extraer_se_referencia(self):
        patron = re.compile(r"de la (S/E|subestación)([^,\.]*?)(?:,|\.| siguiendo)", re.IGNORECASE)
        #Con este patron, logro abarcar 8 casos de 12. Deberia agregar el caso de Tap Off


        match = patron.search(self.ubicacion)

        if match:
            ref = match.group(2).strip()
            ref = ref.replace("subestación", "S/E")
            ref = ref.strip()
            return ref
        
        else:
            return None
            
    def extraer_linea_referencia(self):
        patron = re.compile(r"el trazado de la línea [^,]*", re.IGNORECASE)
        match = patron.search(self.ubicacion)

        if match:
            ref = match.group(0)
            ref = ref.replace("el trazado de la línea ", "")
            ref = ref.strip()
            return ref
        
        else:
            if "tap" in unidecode(self.ubicacion.lower()):
                #buscar indice de la palabra tap
                index = self.ubicacion.lower().find("tap")
                ref = self.ubicacion[index:]
                ref = ref.replace("Tap", "Tap Off")
                print("CASO TAP!")
                return ref
            
            else:
                return None
        
    def extraer_distancia_referencia(self):
        patron = re.compile(r"se deberá emplazar ([^k]*) km", re.IGNORECASE)
        match = patron.search(self.ubicacion)

        if match:
            distancia = match.group(0)
            distancia = distancia.replace("se deberá emplazar a aproximadamente ", "")
            distancia = distancia.replace("se deberá emplazar dentro de un radio de ", "")
            distancia = distancia.replace("se deberá emplazar a ", "")
            distancia = distancia.replace("se deberá emplazar ", "")
            distancia = distancia.replace("a aproximadamente ", "")
            distancia = distancia.strip()
            distancia = distancia.replace(",", ".")
            return distancia
        
        else:
            return None
        
    def extraer_distancia_referencia_v2(self):
        patron = re.compile(r"La subestación se deberá emplazar dentro de un radio de (\d{1,2}) km respecto de la subestación", re.IGNORECASE)
        match = patron.search(self.ubicacion)

        if match:
            distancia = match.group(1)
            distancia = distancia.replace("La subestación se deberá emplazar dentro de un radio de ", "")
            distancia = distancia.replace("respecto de la subestación ", "")
            distancia = distancia.strip()
            distancia = distancia.replace(",", ".")
            return distancia
        
        else:
            return None

    def generar_diccionario_kmz(self):
        # Vamos a generar un diccionario que nos permita exportar la información de la nueva S/E a un archivo KMZ
        # Para eso, tenemos que generar un diccionario que nos permita procesar la informacion clave de la ubicacion de la S/E

        diccionario_kmz = {
            "OBRA": self.nombre_proyecto,
            "DECRETO": "PET 2023",
            "TIPO": self.tipo,
            "V_INV": self.valor_inversion,
            "E_OP": self.entrada_operacion,
            "RESUMEN": self.resumen
        }


        se_referencia = self.extraer_se_referencia()
        #print("S/E de referencia:", se_referencia)
        diccionario_kmz["se_ref"] = se_referencia

        linea_referencia = self.extraer_linea_referencia()
        #print("Línea de referencia:", linea_referencia)
        diccionario_kmz["linea_ref"] = linea_referencia

        if not linea_referencia:
            # Si no se encuentra la línea de referencia, intentamos buscar una referencia
            #print("No se encontró la línea de referencia, este podria ser el caso con solo referencia de distancia respecto una S/E")

            if se_referencia:
                #print("Este caso aplicaré la version 2 de la extracción de distancia")
                #print("proyecto:", self.nombre_se)
                distancia_referencia_2 = self.extraer_distancia_referencia_v2()
                #print("Distancia de referencia 2:", distancia_referencia_2)
                diccionario_kmz["distancia_ref"] = distancia_referencia_2

            else:
                distancia_referencia = self.extraer_distancia_referencia()
                #print("Distancia de referencia:", distancia_referencia)
                diccionario_kmz["distancia_ref"] = distancia_referencia

        else:
            distancia_referencia = self.extraer_distancia_referencia()
            #print("Distancia de referencia:", distancia_referencia)
            diccionario_kmz["distancia_ref"] = distancia_referencia
            print("\n")
            

        #VAMOS A REALIZAR UN CICLO PARA AGREGAR LOS DATOS DE LOS PATIOS AL DICCIONARIO
        i = 0
        for patio in self.patios:
            diccionario_kmz[f"PATIO_{i}"] = {
                f"TENSION": patio.tension,
                f"CONFIG": patio.configuracion,
                f"CONEXIONES": patio.lista_conexiones,
                f"POSDISP": patio.posiciones_disponibles,
            }

            i += 1


        return diccionario_kmz

    def generar_diccionario_kmz_v2(self):
        diccionario_kmz = {
            "OBRA": self.nombre_proyecto,
            "DECRETO": "PET 2023",
            "TIPO": self.tipo,
            "V_INV": self.valor_inversion,
            "E_OP": self.entrada_operacion,
            "RESUMEN": self.resumen
        }


        # Corroborar que todas las funciones tengan el caso None, para asi diferenciar caso a caso
        se_referencia = self.extraer_se_referencia()
        linea_referencia = self.extraer_linea_referencia()
        distancia_referencia = None

        if se_referencia and not linea_referencia:
            distancia_referencia = self.extraer_distancia_referencia_v2()
        
        else:
            distancia_referencia = self.extraer_distancia_referencia()


        diccionario_kmz["se_ref"] = se_referencia
        diccionario_kmz["linea_ref"] = linea_referencia
        diccionario_kmz["distancia_ref"] = distancia_referencia


        #VAMOS A REALIZAR UN CICLO PARA AGREGAR LOS DATOS DE LOS PATIOS AL DICCIONARIO
        i = 0
        for patio in self.patios:
            diccionario_kmz[f"PATIO_{i}"] = {
                f"TENSION": patio.tension,
                f"CONFIG": patio.configuracion,
                f"CONEXIONES": patio.lista_conexiones,
                f"POSDISP": patio.posiciones_disponibles,
            }

            i += 1

        return diccionario_kmz



if __name__ == "__main__":
    texto = """
            El proyecto consiste en la construcción de una nueva subestación, denominada Alto Molle, con patios de 110 kV y 13,8 kV. A su vez, el proyecto considera la instalación de un transformador 110/13,8 kV de, al menos, 30 MVA de capacidad, con Cambiador de Derivación Bajo Carga (CDBC) y sus respectivos paños de conexión en ambos niveles de tensión.
La configuración del patio de 110 kV de la subestación Alto Molle corresponderá a barra principal seccionada y barra de transferencia, con capacidad de barras de, al menos, 500 MVA con 75°C en el conductor y 35°C temperatura ambiente con sol, y deberá considerar espacio en barras y plataforma para nueve posiciones, de manera de permitir la conexión del transformador de poder 110/13,8 kV, la conexión de la nueva línea 2x110 kV Alto Molle – Cóndores, la conexión de la obra “Nueva S/E Huayquique y nueva línea 2x110 kV Huayquique – Alto Molle”, la construcción de un paño acoplador, la construcción de un paño seccionador de barras y la conexión de nuevos proyectos en la zona. En caso de definirse el desarrollo de este patio en tecnología encapsulada y aislada en gas del tipo GIS o equivalente, se deberán considerar los paños contenidos en esta descripción y el espacio en plataforma definido anteriormente para la conexión de nuevos proyectos.
Además, el proyecto considera la construcción de un patio de 13,8 kV, en configuración barra simple, contemplándose la construcción de, al menos, cuatro paños para alimentadores, el paño de conexión para el transformador de poder 110/13,8 kV antes mencionado y espacio en barra y plataforma para la construcción de dos paños futuros. En caso de definirse el desarrollo de este patio como una sala de celdas, se deberán considerar los paños contenidos en esta descripción junto con la construcción de una celda para equipos de medida, la construcción de una celda para servicios auxiliares y el espacio en la sala para la conexión de posiciones futuras definidas anteriormente.
La subestación se deberá emplazar dentro de un radio de 3 km respecto de la subestación Cóndores, considerando únicamente el semicírculo generado al sur de dicho punto. Adicionalmente, la ubicación de la instalación deberá garantizar el cumplimiento del propósito esencial de la obra, posibilitando el debido acceso y la conexión por parte de alimentadores de los sistemas de distribución de la zona.
Adicionalmente, el proyecto contempla la construcción de una nueva línea de transmisión de doble circuito en 110 kV y, al menos, 90 MVA de capacidad por circuito a 35°C con sol, entre la nueva subestación Alto Molle y la subestación Cóndores, con sus respectivos paños de conexión en cada subestación de llegada.     """
    
    
    proyecto = Proyecto("NUEVA S/E ALTO MOLLE", texto)
    proyecto.procesar_descripcion()
    diccionario_kmz = proyecto.generar_diccionario_kmz_v2()
    print(diccionario_kmz)
    pass


