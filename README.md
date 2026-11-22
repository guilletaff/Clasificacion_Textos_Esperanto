# Clasificación de textos en esperanto

Práctica de Minería de Textos · CUNEF · Curso 2026/2027

**Autores:** Guillermo Taffouraud, Rodrigo González y Oriol García Miró

Clasificador de párrafos escritos en esperanto en tres temas de transporte:

| Clase | Tema |
|---|---|
| `fervojo` | Ferrocarril |
| `automobilo` | Automóvil |
| `aviado` | Aviación |

Los tres temas comparten bastante vocabulario (`motoro`, `rapido`, `pasaĝero`, `veturilo`...), así que la clasificación no es fácil.

El proyecto tiene tres fases, todas en el cuaderno [`notebooks/clasificacion_esperanto.ipynb`](notebooks/clasificacion_esperanto.ipynb):

1. **Dataset:** párrafos de la Wikipedia en esperanto, limpios y etiquetados por tema.
2. **NLP:** un modelo de procesamiento de lenguaje para el esperanto hecho desde cero, basado en reglas y con una API parecida a la de spaCy.
3. **Clasificación:** vectorización TF-IDF sobre los lemas, comparación de modelos, evaluación y prueba con páginas web reales.

## Resultados principales

| | Resultado |
|---|---|
| Dataset | 1.064 párrafos (389 `fervojo`, 348 `automobilo`, 327 `aviado`) |
| NLP: acierto en categoría gramatical (frases reales) | 95,8 % |
| NLP: acierto en lema (frases reales) | 97,5 % |
| Clasificador: F1 macro en validación cruzada | 0,91 |
| Clasificador: accuracy / F1 macro en test | 0,934 / 0,934 |

## Estructura del repositorio

```
Clasificacion_Textos_Esperanto/
├── data/
│   ├── dataset_esperanto.csv           Dataset limpio y etiquetado (text;class)
│   └── generar_dataset.py              Script para regenerar el dataset desde la Wikipedia
├── notebooks/
│   └── clasificacion_esperanto.ipynb   Cuaderno principal con las tres fases
├── resources/
│   └── vortoj.json                     Lista de stop-words del esperanto (repositorio guía)
├── requirements.txt                    Librerías necesarias
└── README.md
```

## Instalación y ejecución

### En local

Requiere Python 3.11 o superior.

```bash
git clone https://github.com/guilletaff/Clasificacion_Textos_Esperanto.git
cd Clasificacion_Textos_Esperanto

python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
```

Después se abre `notebooks/clasificacion_esperanto.ipynb` y se ejecutan todas las celdas en orden.

### En Google Colab

Basta con abrir el cuaderno y ejecutar todas las celdas. La primera celda instala las dependencias por sí sola: usa el `requirements.txt` local si existe y, si no, lo descarga de GitHub. El cuaderno no necesita GPU y se ejecuta en pocos segundos.

### Librerías

| Uso | Librerías |
|---|---|
| Descarga de datos y web scraping | `requests`, `beautifulsoup4` |
| Datos, aprendizaje automático y gráficas | `pandas`, `numpy`, `scikit-learn`, `matplotlib` |
| Descarga de artículos de Wikipedia | `esperantilo` (repositorio guía, fijado a un commit concreto) |

En `requirements.txt` se indican versiones mínimas (`>=`) en lugar de exactas, para no romper los paquetes que ya trae Colab. Las versiones con las que se ha ejecutado el cuaderno se imprimen en la celda de configuración.

El modelo de NLP **no usa librerías de NLP** (ni spaCy, ni NLTK, ni Stanza): está escrito desde cero con expresiones regulares y reglas. De `esperantilo` solo se usa `WikiPage`, para descargar artículos.

### Configuración

Al principio del cuaderno están los parámetros principales:

- `GENERAR_DATASET = False` (por defecto): se carga el dataset ya generado. Es más rápido y siempre da el mismo resultado.
- `GENERAR_DATASET = True`: se vuelven a descargar los 76 artículos de la Wikipedia (unos dos minutos) y se guarda el nuevo CSV en `data/`.
- `SEMILLA = 42`: semilla aleatoria fija para que los resultados sean reproducibles.

El dataset también se puede regenerar fuera del cuaderno:

```bash
python data/generar_dataset.py
```

El script usa las mismas funciones de descarga, limpieza y filtrado que el cuaderno, así que produce exactamente el mismo CSV.

### Robustez ante fallos de red

El cuaderno no depende de ficheros locales y está preparado para que falle alguna de las webs que usa:

- **Dataset:** se busca primero en `data/`, después en GitHub y, si los dos fallan, se regenera desde la Wikipedia. Si no se consigue de ninguna forma, el cuaderno se para con un mensaje que explica qué ha fallado.
- **Stop-words:** se leen de `resources/vortoj.json`, después de GitHub y, si los dos fallan, de una copia escrita en el propio cuaderno.
- **Wikipedia y páginas web:** si un artículo o una página no responde, se avisa y se sigue con los demás.

## Fase 1: Dataset

- **Fuente:** 76 artículos de la Wikipedia en esperanto elegidos a mano (28 de ferrocarril, 25 de automóvil y 23 de aviación), por ejemplo *Lokomotivo*, *Aŭtobuso* o *Flughaveno*.
- **Solo esperanto:** se desactivan los idiomas de respaldo de `WikiPage` y se comprueba el idioma de cada página.
- **Segmentación:** cada párrafo del artículo es una fila y hereda la etiqueta de su artículo.
- **Limpieza:** se quitan títulos de sección (`== Historio ==`), referencias (`[1]`), enlaces y el carácter `;`.
- **Filtrado del ruido:** se descartan líneas cortas, bibliografía, texto en otros idiomas, elementos de lista y duplicados.

Más de la mitad de las líneas que devuelve la Wikipedia no son párrafos útiles. De 2.354 líneas se quedan 1.064:

| Motivo del descarte | Líneas |
|---|---|
| Muy corto (títulos de sección, elementos sueltos, pies de imagen...) | 887 |
| Elemento de lista | 286 |
| Bibliografía | 101 |
| Otro idioma | 14 |
| Duplicado | 2 |

**Formato del CSV** ([`data/dataset_esperanto.csv`](data/dataset_esperanto.csv)): codificación UTF-8, separador `;` y dos columnas, `text` y `class`. El CSV se guarda ya filtrado, sin enlaces, referencias ni bibliografía.

**Ruido de etiquetado:** aunque un párrafo pase los filtros, la etiqueta heredada del artículo no siempre es correcta. Se ha medido con validación cruzada: 6 de los 1.064 párrafos contradicen su etiqueta con claridad y unos 85 (el 8 %) en total. Son sobre todo párrafos genéricos o que hablan de otro tema.

## Fase 2: Modelo de NLP para el esperanto

El esperanto es una lengua muy regular: **la terminación de una palabra indica su categoría gramatical**. El modelo se apoya en eso.

| Terminación | Categoría | Ejemplo |
|---|---|---|
| `-o` | sustantivo | `trajno` (tren) |
| `-a` | adjetivo | `rapida` (rápido) |
| `-e` | adverbio | `rapide` (rápidamente) |
| `-i` | verbo en infinitivo | `veturi` (viajar) |
| `-as` / `-is` / `-os` | presente / pasado / futuro | `veturis` |
| `-us` / `-u` | condicional / volitivo | `veturus` |
| `-j` / `-n` | plural / acusativo | `trajnojn` |
| `-ant-`, `-int-`, `-ont-`, `-at-`, `-it-`, `-ot-` | participios | `konstruita` |

Componentes:

- **Léxico de palabras cerradas:** artículo, pronombres, preposiciones, conjunciones, correlativos, numerales... Son las únicas palabras que no siguen las reglas de terminación.
- **Stop-words:** la lista de `vortoj.json` más los correlativos, el léxico cerrado y los verbos auxiliares.
- **Tokenizador** con expresiones regulares: URLs, números, ordinales como `20-a`, unidades y abreviaturas (`km/h`, `ekz.`), letras `ĉ ĝ ĥ ĵ ŝ ŭ` y palabras compuestas con guion.
- **Análisis de cada palabra:** categoría gramatical (etiquetas universales `NOUN`, `VERB`, `ADJ`...), lema y rasgos (número, caso, tiempo, participio).
- **Reglas de contexto:** nombres propios, correlativos como determinante o pronombre, y `povi`, `devi` y `voli` como verbos auxiliares.

Se usa como spaCy:

```python
nlp = Esperanto()
doc = nlp("La rapidaj elektraj trajnoj veturis inter Parizo kaj Liono.")
for token in doc:
    print(token.text, token.lemma_, token.pos_, token.morph, token.is_stop)
```

**Evaluación:**

| Conjunto | Tamaño | Acierto POS | Acierto lema |
|---|---|---|---|
| Pruebas de casos concretos | 36 casos | 36 / 36 | |
| Frases propias (usadas al desarrollar las reglas) | 109 tokens | 100,0 % | 100,0 % |
| Frases reales del dataset, etiquetadas a mano | 118 tokens | 95,8 % | 97,5 % |

Los errores en frases reales son casos difíciles para un sistema de reglas: nombres propios al inicio de frase (*Harmon*, *Selden*) o palabras que cambian de categoría según el contexto (*ambaŭ*).

Aplicado a todo el dataset (51.154 tokens), solo el 1,3 % de las palabras quedan sin reconocer, y la lematización reduce el vocabulario de 9.501 palabras distintas a 6.848 lemas.

## Fase 3: Clasificación

- Partición **80/20 estratificada**: 851 párrafos de entrenamiento y 213 de test.
- El vectorizador y el modelo van dentro de un `Pipeline` de scikit-learn con `analyzer=lemas_utiles`, así que toda la tokenización y lematización la hace nuestro modelo de NLP.
- Comparación de **Bag of Words** y **TF-IDF** con **Naive Bayes**, **Regresión Logística** y **SVM lineal**, con validación cruzada de 5 particiones sobre el entrenamiento y F1 macro como métrica.

| Vectorizador | Modelo | F1 macro (media) | Desviación |
|---|---|---|---|
| Bag of Words | Naive Bayes | 0,920 | 0,023 |
| TF-IDF | Naive Bayes | 0,914 | 0,011 |
| TF-IDF | SVM lineal | 0,912 | 0,019 |
| TF-IDF | Regresión Logística | 0,911 | 0,020 |
| Bag of Words | Regresión Logística | 0,878 | 0,025 |
| Bag of Words | SVM lineal | 0,866 | 0,041 |

Las cuatro mejores combinaciones quedan entre 0,91 y 0,92, con diferencias menores que la desviación entre particiones, así que el F1 no basta para decidir. Se descarta Bag of Words con Naive Bayes, aunque tenga la media más alta, porque en textos largos (como las páginas web) sus probabilidades se saturan a 1,0 aunque parte del texto sea de otro tema. Entre los modelos con TF-IDF se elige la Regresión Logística (class_weight="balanced"): da probabilidades útiles también en textos largos y sus coeficientes indican qué lemas pesan en cada clase.

**Resultados en test:**

| Clase | Precisión | Recall | F1 |
|---|---|---|---|
| `automobilo` | 0,89 | 0,94 | 0,92 |
| `aviado` | 0,97 | 0,91 | 0,94 |
| `fervojo` | 0,95 | 0,95 | 0,95 |
| **Accuracy** | | | **0,934** |
| **F1 macro** | | | **0,934** |

Lemas con más peso en cada clase:

- `automobilo`: aŭto, aŭtomobilo, eksplodmotoro, aŭtovojo, aŭtobuso, motorciklo, kamiono...
- `aviado`: aviadilo, flugo, paraŝuto, flugi, flughaveno, airbus, aviado...
- `fervojo`: trajno, fervojo, lokomotivo, vagono, metroo, linio, tramo...

**Páginas web reales:** se descargan con `requests`, se extrae el texto de los párrafos (`<p>`) con BeautifulSoup y se clasifican. Ninguna de estas páginas se usó para entrenar.

| Página | Predicción | Probabilidad |
|---|---|---|
| flightschoolusa.com/eo/kiom-gajnas-atc | `aviado` | 0,74 |
| eo.wikipedia.org/wiki/Transsiberia_fervojo | `fervojo` | 0,91 |
| eo.wikipedia.org/wiki/Formulo_1 | `automobilo` | 0,67 |

**Frases escritas por nosotros:** el cuaderno también clasifica cuatro frases propias, que no están en el dataset. Acierta las cuatro, y además funciona sin conexión.

| Frase | Traducción | Predicción | Probabilidad |
|---|---|---|---|
| *La trajno alvenis al la stacidomo kun duonhora malfruo pro problemo en la reloj.* | El tren llegó a la estación con media hora de retraso por un problema en las vías. | `fervojo` | 0,85 |
| *Mia nova elektra aŭto bezonas nur unu horon por ŝargi la baterion.* | Mi nuevo coche eléctrico solo necesita una hora para cargar la batería. | `automobilo` | 0,66 |
| *La piloto anoncis, ke la aviadilo surteriĝos en la flughaveno post dek minutoj.* | El piloto anunció que el avión aterrizará en el aeropuerto en diez minutos. | `aviado` | 0,89 |
| *La ŝoforo de la kamiono ne vidis la buson sur la aŭtovojo.* | El conductor del camión no vio el autobús en la autopista. | `automobilo` | 0,84 |

La frase del coche eléctrico es la más dudosa (un 27 % para `fervojo`), probablemente porque `elektra` aparece casi igual de a menudo en los párrafos de trenes (42) que en los de coches (50).

## Conclusiones

### Dataset

- **La Wikipedia necesita mucha limpieza.** Más de la mitad de las líneas que devuelve no son párrafos útiles: títulos, elementos de listas, pies de imagen y bibliografía. Con unas pocas reglas sencillas (longitud, palabras clave de bibliografía, palabras de otros idiomas, presencia de un verbo conjugado) se quitan casi todas. Cada regla se ajustó revisando lo que dejaba pasar y lo que descartaba por error. Por ejemplo, nombres como *Airbus* o *Julius* se tomaban por verbos, y los párrafos técnicos con unidades (`kg`, `t`) se tomaban por texto en otro idioma.
- **Hacen falta muchos artículos.** Para superar los 300 párrafos por clase después de filtrar hubo que usar entre 23 y 28 artículos por tema, porque muchos artículos en esperanto son cortos.
- **El ruido de etiquetado existe aunque es pequeño.** Cada párrafo hereda la etiqueta de su artículo, y no siempre es correcta. Medido con validación cruzada, solo 6 de los 1.064 párrafos contradicen su etiqueta con claridad, y unos 85 (el 8 %) si se cuentan también los casos dudosos. Son párrafos genéricos, como el de las tiendas de las estaciones, o que hablan de otro tema, como los motores de avión dentro del artículo de motores de combustión.

### Modelo de NLP

- **La regularidad del esperanto hace que un sistema de reglas funcione muy bien.** Sin ninguna librería de NLP, el modelo acierta el 95,8 % de las categorías gramaticales y el 97,5 % de los lemas en frases reales del dataset. En todo el corpus solo deja sin reconocer el 1,3 % de las palabras.
- **La lematización es útil para clasificar.** Reduce el vocabulario de 9.501 palabras distintas a 6.848 lemas (casi un 28 % menos), porque junta formas como `trajno`, `trajnoj`, `trajnon` y `trajnojn`.
- **Lo difícil son los nombres propios y las excepciones.** Los errores que quedan son nombres propios al inicio de frase, palabras que parecen participios sin serlo (`konstanta`, `senpilota`) y palabras cuya categoría depende del contexto (`ambaŭ`). Algunas reglas son un compromiso: para no estropear nombres como *London* o *Washington*, `Konkordon` no pierde el acusativo.
- **Las pruebas evitan romper lo que ya funciona.** Las 36 pruebas de casos concretos detienen el cuaderno si alguna falla, así que cada cambio en las reglas se comprueba al momento.

### Clasificación

- **Los temas se distinguen bien a pesar de compartir vocabulario.** El clasificador consigue un F1 macro de 0,91 en validación cruzada y de 0,934 en test.
- **Los modelos sencillos funcionan igual de bien.** Las cuatro mejores combinaciones quedan entre 0,91 y 0,92, con diferencias menores que la desviación entre particiones. Por eso se eligió la Regresión Logística por motivos prácticos: probabilidades útiles y pesos que se pueden interpretar. Los lemas que más pesan son los que una persona esperaría (`trajno`, `aviadilo`, `aŭto`...).
- **Los errores van sobre todo hacia `automobilo`.** Es la clase con menor precisión (0,89): 8 de los 14 errores en test son párrafos de otra clase que el modelo toma por coches. Tiene sentido, porque comparte con las otras dos clases palabras como `motoro`, `veturilo` o `elektra`.
- **Generaliza fuera de la Wikipedia.** Acierta las tres páginas web, incluida una que no es de la Wikipedia, y las cuatro frases escritas por nosotros, que tienen un estilo menos enciclopédico. La confianza baja en páginas largas que mezclan temas: un 67 % en la de Fórmula 1 frente a un 91 % en la del Transiberiano.

### Limitaciones

- **El resultado en test probablemente sea algo optimista.** Párrafos de un mismo artículo pueden acabar unos en entrenamiento y otros en test, y comparten vocabulario muy concreto. Separar por artículo no es posible porque el contrato de datos solo admite las columnas `text;class`.
- **Las páginas web se clasifican enteras.** El modelo se entrenó con párrafos de unas 30 palabras, pero cada página se clasifica como un único texto de cientos o miles de palabras. Eso explica en parte la menor confianza en las páginas largas.
- **El dataset solo tiene textos de la Wikipedia.** El estilo es enciclopédico, y no se ha probado con textos de otro tipo, como noticias o foros, más allá de unas pocas frases.

### Posibles mejoras

- Guardar internamente el artículo de cada párrafo, sin cambiar el CSV, y usar validación cruzada por artículo (`GroupKFold`) para medir cuánto infla el resultado la fuga entre entrenamiento y test.
- Clasificar las páginas web párrafo a párrafo y promediar las probabilidades, igual que se entrenó el modelo.
- Usar la medida del ruido de etiquetado para revisar a mano, o descartar, los párrafos que contradicen su etiqueta con claridad.
- Ampliar el dataset con más artículos y otras fuentes en esperanto.

## Créditos

- Librería [`nlp-esperantilo`](https://github.com/jparisu/nlp-esperantilo), el repositorio guía de la asignatura. Se usa para descargar artículos de Wikipedia y como fuente de la lista de stop-words.
- Textos de la [Wikipedia en esperanto](https://eo.wikipedia.org).