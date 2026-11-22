# Clasificación de textos en Esperanto

**Minería de Textos · CUNEF · 2026/2027**

Clasificador de párrafos escritos en esperanto en tres temas de transporte:

| Clase | Tema |
|---|---|
| `fervojo` | Ferrocarril |
| `automobilo` | Automóvil |
| `aviado` | Aviación |

Los tres temas comparten bastante vocabulario (`motoro`, `rapido`, `pasaĝero`, `veturilo`...), así que la clasificación no es trivial.

El proyecto se divide en tres fases, todas en el cuaderno [notebooks/clasificacion_esperanto.ipynb](notebooks/clasificacion_esperanto.ipynb):

1. **Dataset**: párrafos de la Wikipedia en esperanto etiquetados por tema.
2. **NLP**: un modelo de NLP propio para el esperanto, basado en reglas y con una API parecida a la de spaCy.
3. **Clasificación**: vectorización con TF-IDF sobre los lemas, entrenamiento de un modelo y prueba con páginas web reales.

---

## Estructura del repositorio

```
Clasificacion_Textos_Esperanto/
├── data/
│   ├── dataset_esperanto.csv    # Dataset de párrafos etiquetados (text;class)
│   └── generar_dataset.py       # Script independiente para generar el dataset
├── notebooks/
│   └── clasificacion_esperanto.ipynb   # Cuaderno principal con las tres fases
├── resources/
│   └── vortoj.json              # Lista de stop-words del esperanto (repositorio guía)
├── requirements.txt             # Librerías con versiones fijadas
└── README.md
```

---

## Instalación y ejecución

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

Después se abre [notebooks/clasificacion_esperanto.ipynb](notebooks/clasificacion_esperanto.ipynb) y se ejecutan todas las celdas. La primera celda instala las dependencias por sí sola: usa el `requirements.txt` local si existe y, si no (por ejemplo en Google Colab), lo descarga de GitHub.

### Librerías

| Uso | Librerías |
|---|---|
| Descarga de datos y web scraping | `requests`, `beautifulsoup4` |
| Datos, aprendizaje automático y gráficas | `pandas`, `numpy`, `scikit-learn`, `matplotlib` |
| Descarga de artículos de Wikipedia | `esperantilo` (repositorio guía, fijado a un commit concreto) |

El modelo de NLP **no usa librerías de NLP** (ni spaCy ni NLTK): está escrito desde cero con expresiones regulares.

### Configuración

Al principio del cuaderno está la variable `GENERAR_DATASET`:

- `False` (por defecto): se carga el CSV ya guardado en GitHub. Es más rápido y siempre da el mismo resultado.
- `True`: se vuelven a descargar todos los artículos de la Wikipedia.

La semilla aleatoria está fijada (`SEMILLA = 42`) para que los resultados sean reproducibles.

---

## Fase 1 · Dataset

- **Fuente**: artículos de la Wikipedia en esperanto elegidos a mano para cada tema (por ejemplo *Lokomotivo*, *Aŭtobuso*, *Flughaveno*), descargados con `WikiPage` de la librería `esperantilo`.
- **Solo esperanto**: se desactivan los idiomas de respaldo de `WikiPage` y se comprueba el idioma de la página, porque en una primera versión se colaron párrafos en español.
- **Segmentación**: cada línea del artículo es un párrafo y hereda la etiqueta de su artículo.
- **Limpieza**: se quitan títulos de sección (`== Historio ==`), referencias (`[1]`), URLs y el carácter `;`.
- **Filtrado del ruido**: se descartan párrafos muy cortos, bibliografía, texto en otros idiomas, elementos de lista y duplicados.

**Formato del CSV** ([data/dataset_esperanto.csv](data/dataset_esperanto.csv)): separador `;`, codificación UTF-8 y dos columnas, `text` y `class`.

| | Párrafos |
|---|---|
| Antes de filtrar | 635 |
| Después de filtrar | 418 |
| Tras quitar párrafos con >20% de palabras extranjeras | 416 |

Casi un tercio de las líneas que devuelve la Wikipedia no son párrafos útiles, sobre todo listas y bibliografía.

El dataset también se puede generar fuera del cuaderno con:

```bash
python data/generar_dataset.py
```

---

## Fase 2 · Modelo de NLP para Esperanto

El esperanto es muy regular: **la terminación de una palabra indica su categoría gramatical**. El modelo se apoya en eso.

| Terminación | Categoría | Ejemplo |
|---|---|---|
| `-o` | sustantivo | `trajno` (tren) |
| `-a` | adjetivo | `rapida` (rápido) |
| `-e` | adverbio | `rapide` (rápidamente) |
| `-i` | verbo en infinitivo | `veturi` (viajar) |
| `-as` / `-is` / `-os` | presente / pasado / futuro | `veturis` |
| `-us` / `-u` | condicional / imperativo | `veturus` |
| `-j` / `-n` | plural / acusativo | `trajnojn` |
| `-ant-`, `-int-`, `-ont-`, `-at-`, `-it-`, `-ot-` | participios | `konstruita` |

Componentes:

- **Léxico** de palabras cerradas (artículo, pronombres, preposiciones, conjunciones, correlativos...), que son las únicas que no siguen las reglas de terminación.
- **Stop-words**: la lista de [vortoj.json](resources/vortoj.json) más correlativos, el léxico y los verbos auxiliares.
- **Tokenizador** con expresiones regulares (URLs, números, ordinales como `20-a`, palabras con `ĉ ĝ ĥ ĵ ŝ ŭ` y compuestos con guion).
- **Análisis morfológico**: POS (etiquetas universales `NOUN`, `VERB`, `ADJ`...), lema y rasgos (número, caso, tiempo, participio).
- **Reglas de contexto**: nombres propios, correlativos como determinante o pronombre, y `povi`/`devi`/`voli` como auxiliares.

Funciona como spaCy:

```python
nlp = Esperanto()
doc = nlp("La rapidaj elektraj trajnoj veturis inter Parizo kaj Liono.")
for token in doc:
    print(token.text, token.lemma_, token.pos_, token.morph, token.is_stop)
```

**Evaluación**:

| Conjunto | Tokens | Acierto POS | Acierto lema |
|---|---|---|---|
| Pruebas unitarias | 23 casos | 23/23 | |
| Frases propias (usadas al desarrollar las reglas) | 109 | 100,0% | 100,0% |
| Frases reales del dataset (etiquetadas a mano) | 118 | 95,8% | 97,5% |

La lematización reduce el vocabulario del dataset de 5.088 palabras distintas a 3.835 lemas.

---

## Fase 3 · Clasificación

- División **80/20 estratificada** en entrenamiento (332) y test (84).
- Vectorizador y modelo dentro de un `Pipeline` de scikit-learn, con `analyzer=lemas_utiles`: toda la tokenización y lematización la hace nuestro modelo de NLP.
- Comparación de **Bag of Words** y **TF-IDF** con **Naive Bayes**, **Regresión Logística** y **SVM lineal** mediante validación cruzada de 5 particiones y F1 macro.

| Vectorizador | Modelo | F1 macro (CV) |
|---|---|---|
| Bag of Words | Naive Bayes | 0,915 |
| TF-IDF | SVM lineal | 0,904 |
| TF-IDF | Regresión Logística | 0,896 |
| Bag of Words | Regresión Logística | 0,862 |
| Bag of Words | SVM lineal | 0,844 |
| TF-IDF | Naive Bayes | 0,788 |

Modelo elegido: **TF-IDF + Regresión Logística** (`class_weight="balanced"`), porque además de rendir bien da probabilidades por clase, que se usan para clasificar páginas web.

**Resultados en test**:

| Clase | Precisión | Recall | F1 |
|---|---|---|---|
| `automobilo` | 0,97 | 0,93 | 0,95 |
| `aviado` | 0,96 | 1,00 | 0,98 |
| `fervojo` | 0,86 | 0,90 | 0,88 |
| **Accuracy** | | | **0,940** |
| **F1 macro** | | | **0,935** |

Lemas con más peso por clase:

- `automobilo`: aŭto, aŭtomobilo, eksplodmotoro, aŭtovojo, motorciklo, aŭtobuso, kamiono...
- `aviado`: aviadilo, helikoptero, rotoro, aviado, flughaveno, aero, aerŝipo...
- `fervojo`: lokomotivo, stacidomo, trajno, fervojo, tramo, vagono...

**Páginas web**: se descargan con `requests`, se extrae el texto de los `<p>` con BeautifulSoup y se clasifican.

| Página | Predicción |
|---|---|
| flightschoolusa.com/eo/kiom-gajnas-atc | `aviado` (0,55) |
| eo.wikipedia.org/wiki/Transsiberia_fervojo | `fervojo` (0,75) |
| eo.wikipedia.org/wiki/Formulo_1 | `automobilo` (0,55) |

---

## Conclusiones y limitaciones

- El dataset tiene bastante ruido: casi un tercio de lo que devuelve la Wikipedia son listas, bibliografía o texto en otros idiomas, y se filtra con reglas sencillas.
- El modelo de NLP, solo con reglas, acierta alrededor del 96% de las categorías gramaticales y del 97% de los lemas en frases reales.
- El clasificador consigue un F1 macro en torno a 0,9 en validación cruzada y en test.
- **Limitación**: párrafos de un mismo artículo pueden acabar unos en entrenamiento y otros en test, así que el resultado en test probablemente es algo optimista. Separar por artículo no es posible porque el contrato de datos solo admite las columnas `text;class`.
- Lo que más se podría mejorar es el dataset: más párrafos de trenes y de aviación, y una forma de detectar párrafos genéricos que heredan una etiqueta que no les corresponde.

---

## Créditos

- Librería [`nlp-esperantilo`](https://github.com/jparisu/nlp-esperantilo) (repositorio guía de la asignatura), usada para descargar artículos de Wikipedia y como fuente de la lista de stop-words.
- Textos de la [Wikipedia en esperanto](https://eo.wikipedia.org).
