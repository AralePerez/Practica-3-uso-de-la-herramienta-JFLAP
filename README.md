# Simulador de Autómatas Finitos (AFD, AFND y AFN-λ)

## Descripción

Este proyecto consiste en el desarrollo de una aplicación con interfaz gráfica para la creación, simulación, análisis, transformación y optimización de autómatas finitos. La herramienta fue diseñada con fines académicos para apoyar el aprendizaje práctico de los conceptos vistos en la teoría de lenguajes formales y autómatas.

La aplicación permite trabajar con tres tipos de autómatas:

- **AFD** (Autómata Finito Determinista)
- **AFND** (Autómata Finito No Determinista)
- **AFN-λ** (Autómata Finito No Determinista con transiciones lambda)

Por medio de esta herramienta, el usuario puede definir estados, alfabeto y transiciones, simular cadenas paso a paso, calcular λ-clausuras, convertir autómatas entre distintos tipos, minimizar autómatas deterministas y validar múltiples cadenas desde archivo. Además, se contempla la importación y exportación en formatos comunes utilizados en prácticas de autómatas, como `.jff`, `.json` y `.xml`.


## Objetivos 

- Permitir la definición de autómatas deterministas y no deterministas.
- Simular el comportamiento de cadenas de entrada sobre distintos tipos de autómatas.
- Mostrar el proceso de validación paso a paso.
- Calcular λ-clausuras de estados o conjuntos de estados.
- Convertir un AFND o AFN-λ a un AFD equivalente.
- Eliminar transiciones lambda para obtener un AFND equivalente.
- Minimizar autómatas deterministas.
- Validar múltiples cadenas a la vez a partir de un archivo de texto.
- Importar y exportar autómatas en distintos formatos.

---

## Funcionalidades Principales

### 1. Definición de Autómatas

La aplicación permite construir un autómata desde la interfaz gráfica especificando los siguientes elementos:

- Conjunto de estados
- Alfabeto de entrada
- Estado inicial
- Conjunto de estados de aceptación
- Tabla de transiciones

Según el tipo de autómata, la definición se adapta de la siguiente forma:

#### AFD
- Solo se permite una transición por cada par estado-símbolo.

#### AFND
- Se permiten múltiples transiciones para un mismo par estado-símbolo.
- Se manejan varios caminos posibles durante el procesamiento de una cadena.

#### AFN-λ
- Se permite el uso de transiciones lambda como símbolo especial.
- Las transiciones lambda pueden representarse con `λ`, `lambda`, `epsilon` o una cadena vacía según la implementación del sistema.

---

### 2. Simulación de Cadenas

La aplicación permite ingresar una cadena y observar si el autómata la acepta o la rechaza.

<img width="1600" height="960" alt="image" src="https://github.com/user-attachments/assets/108beb67-c238-4906-ac0b-3544778a7ffb" />


### 3. Visualización del Proceso

El programa permite visualizar el comportamiento del autómata durante la simulación, mostrando información como:

- Estados activos en cada paso
- Símbolo que se está procesando
- Transiciones utilizadas
- Ramificaciones en AFND y AFN-λ
- Resultado final de aceptación o rechazo

En el caso de AFN-λ, también se puede mostrar el efecto de las transiciones lambda durante el procesamiento.

---

### 4. Cálculo de λ-Clausura

La aplicación implementa el cálculo de λ-clausura para uno o varios estados.

La λ-clausura de un estado consiste en el conjunto de estados que se pueden alcanzar partiendo de ese estado usando únicamente transiciones lambda, sin consumir símbolos de entrada.

Esta funcionalidad permite:

- Calcular la λ-clausura de un estado seleccionado
- Calcular la λ-clausura de un conjunto de estados
- Mostrar visualmente los estados involucrados en la clausura
- Usar la λ-clausura durante la simulación de AFN-λ y en procesos de conversión


### 5. Conversión entre Tipos de Autómatas

 -Conversión de AFND a AFD
 -Conversión de AFN-λ a AFND
 -Conversión de AFN-λ a AFD
También puede realizarse una determinización considerando primero las λ-clausuras y después aplicando el algoritmo de subconjuntos.

### 6. Minimización de AFD

La aplicación incluye el proceso de minimización de autómatas finitos deterministas.

La minimización tiene como objetivo reducir el número de estados del autómata sin alterar el lenguaje que reconoce.

El proceso incluye:

- Eliminación de estados inaccesibles
- Identificación de estados equivalentes o indistinguibles
- Fusión de estados equivalentes
- Construcción del AFD mínimo resultante

Además, la herramienta puede mostrar:

- Número de estados del AFD original
- Número de estados del AFD minimizado
- Cantidad de estados eliminados
- Grupos de estados equivalentes fusionados
- Comparación funcional entre el autómata original y el minimizado



### 7. Importación y Exportación

La aplicación permite importar y exportar autómatas en distintos formatos para facilitar su reutilización y compatibilidad con otras herramientas.

#### Importación
- `.jff` (JFLAP)
- `.json`
- `.xml`

#### Exportación
- `.jff`
- `.json`
- `.xml`

Esto permite guardar autómatas diseñados dentro del programa o abrir autómatas previamente construidos en otras herramientas.

## Tipos de Autómatas Soportados

### AFD
### AFND
### AFN-λ
## Estructura del Proyecto
### `main.py`
Archivo principal del programa. Se encarga de iniciar la aplicación y cargar la interfaz gráfica.

### `gui.py`
Contiene la interfaz gráfica desarrollada con Tkinter. Desde este módulo el usuario puede crear autómatas, ejecutar simulaciones, realizar conversiones y utilizar las herramientas adicionales del sistema.

### `automaton.py`
Incluye la lógica principal de los autómatas, como la representación de estados y transiciones, simulación, cálculo de λ-clausura y validación de cadenas.

### `converter.py`
Contiene los algoritmos necesarios para realizar conversiones entre tipos de autómatas, por ejemplo:
- AFND a AFD
- AFN-λ a AFND
- AFN-λ a AFD

### `io_utils.py`
Módulo encargado de la importación y exportación de archivos en formatos como `.jff`, `.json` y `.xml`.

### `test_cases.py`
Se utiliza para el manejo de pruebas múltiples y validación masiva de cadenas.

---

## Requisitos del Sistema

Para ejecutar este programa se necesita lo siguiente:

- **Python 3.8 o superior**
- Sistema operativo compatible con Python
- Librerías estándar de Python

### Librerías utilizadas
- `tkinter`
- `json`
- `xml`
- `os`
- `collections`
- `itertools`


## Cómo Ejecutar el Programa (Importante)

### Opción 1: Desde terminal o consola

1. Descargar o descomprimir la carpeta del proyecto.
2. Abrir una terminal dentro de la carpeta principal del proyecto.
3. Ejecutar el siguiente comando:

```bash
python main.py
```

Si tu sistema usa `python3`, entonces ejecuta:

```bash
python3 main.py
```

### Opción 2: Desde un entorno de desarrollo

También es posible abrir el proyecto en un editor o IDE como:

- Visual Studio Code
- PyCharm
- IDLE

Después, solo se debe abrir el archivo `main.py` y ejecutarlo.

---

## Funcionamiento General del Programa

Una vez abierta la aplicación, el usuario puede:

1. Seleccionar el tipo de autómata que desea trabajar.
2. Definir los estados y el alfabeto.
3. Especificar el estado inicial y los estados de aceptación.
4. Capturar las transiciones en la tabla correspondiente.
5. Ingresar una cadena para simular.
6. Observar el resultado de aceptación o rechazo.
7. Utilizar funciones extra como:
   - λ-clausura
   - determinización
   - eliminación de lambda
   - minimización
   - pruebas múltiples
   - importación y exportación

---

## Flujo Básico de Uso

### Para crear y simular un autómata

1. Abrir el programa.
2. Elegir el tipo de autómata: AFD, AFND o AFN-λ.
3. Registrar los estados.
4. Definir el alfabeto.
5. Indicar el estado inicial.
6. Seleccionar los estados finales.
7. Agregar las transiciones.
8. Escribir una cadena de entrada.
9. Ejecutar la simulación.
10. Revisar el resultado y el proceso paso a paso.

### Para convertir un autómata

1. Crear o cargar un AFND o AFN-λ.
2. Seleccionar la opción de conversión.
3. Ejecutar el algoritmo correspondiente.
4. Revisar el autómata generado y su tabla de transiciones.

### Para minimizar un AFD

1. Cargar o crear un AFD.
2. Seleccionar la opción de minimización.
3. Ejecutar el proceso.
4. Comparar el número de estados del autómata original y del autómata


## Conclusión

Este proyecto representa una implementación práctica de los conceptos fundamentales de autómatas finitos. La aplicación no solo permite construir y simular AFD, AFND y AFN-λ, sino también analizar su comportamiento interno, calcular λ-clausuras, convertir autómatas entre diferentes modelos, minimizar AFD y validar múltiples cadenas de entrada.

Gracias a su interfaz gráfica y a la integración de algoritmos teóricos importantes, el programa funciona como una herramienta útil para el aprendizaje, la experimentación y la comprobación de resultados dentro del área de lenguajes formales y autómatas.


## Autor

Este proyecto fue desarrollado con fines académicos como parte de una práctica de implementación y extensión de simuladores de autómatas finitos.
-Perez Flores Arale
-Juarez Hipolito Marco Antonio
- Ivan

  
## Cómo Ejecutar el Programa 
Opción usando Visual Studio Code

1. Abre Visual Studio Code.

2. Da clic en **File > Open Folder** (Archivo > Abrir carpeta).

3. Selecciona la carpeta donde está tu proyecto.

4. Una vez abierta la carpeta, busca el archivo llamado:

   main.py

5. Dale clic a ese archivo para abrirlo.

6. Ahora, en la parte superior derecha, da clic en el botón que dice:

   Run Python File (o el símbolo de "play")

   También puedes hacer clic derecho dentro del archivo y seleccionar:

   Run Python File in Terminal

7. Se abrirá una terminal abajo automáticamente y el programa iniciará.



### Opción usando la terminal (forma sencilla)

1. Abre la carpeta del proyecto.

2. Presiona clic derecho dentro de la carpeta y selecciona:

   Open in Terminal (Abrir en terminal)

3. Escribe este comando y presiona Enter:

```bash
python main.py
```

Si ese comando no funciona, prueba este:

```bash
python3 main.py
```


### Opción usando la terminal con comandos (paso a paso con cd)

1. Abre la terminal (puede ser CMD, PowerShell o la terminal de VS Code).

2. Usa el comando **cd** para moverte a la carpeta donde está tu proyecto.

Ejemplo:

Si tu proyecto está en Escritorio:

```bash
cd Desktop
```

Si está dentro de una carpeta:

```bash
cd Desktop/nombre_de_tu_carpeta
```

En Windows también puede ser:

```bash
cd C:\Users\TuUsuario\Desktop\nombre_de_tu_carpeta
```

3. Una vez dentro de la carpeta correcta, ejecuta el programa con:

```bash
python main.py
```

o si no funciona:

```bash
python3 main.py
```

4. Presiona Enter y el programa se abrirá.

```bash
dir
```

(Windows)

o

```bash
ls
```

(Mac/Linux)

para ver los archivos y confirmar que aparece **main.py**.

6. Liga y archivo practica en LATEX
   https://es.overleaf.com/read/rhrrtznqvfdd#bb4d3b

   

Nota:
La visualización gráfica fue mejorada para resaltar estados activos y dibujar las transiciones lambda con estilo diferenciado.
