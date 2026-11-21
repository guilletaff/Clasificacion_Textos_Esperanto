import os
import re
import ast
import json
import pandas as pd
from esperantilo import WikiPage

# 1. Temáticas y artículos de Wikipedia
# La lista CATEGORIAS no se repite aquí: se lee del cuaderno, que es donde está definida, para que
# los dos generen siempre el dataset con los mismos artículos.
RUTA_CUADERNO = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "..", "notebooks", "clasificacion_esperanto.ipynb")


def leer_categorias_del_cuaderno(ruta=RUTA_CUADERNO):
    """Busca en el cuaderno la celda 'CATEGORIAS = {...}' y devuelve ese diccionario.

    Se usa ast.literal_eval, que solo interpreta el diccionario y no ejecuta código del cuaderno.
    """
    with open(ruta, encoding="utf-8") as f:
        cuaderno = json.load(f)
    for celda in cuaderno["cells"]:
        codigo = "".join(celda["source"])
        if celda["cell_type"] == "code" and codigo.startswith("CATEGORIAS = "):
            return ast.literal_eval(codigo.split("=", 1)[1].strip())
    raise ValueError(f"No se encontró CATEGORIAS en {ruta}")


CATEGORIAS = leer_categorias_del_cuaderno()

def limpiar_parrafo(parrafo: str) -> str:
    """
    Limpia el texto conforme al contrato de datos:
    - Elimina saltos de línea y espacios redundantes.
    - Reemplaza el carácter ';' para evitar corromper el CSV.
    - Elimina cabeceras de sección tipo == Historio ==.
    """
    texto = re.sub(r"==+.*?==+", "", parrafo)
    texto = texto.replace(";", ",")
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto

def construir_dataset():
    filas = []
    
    print("Iniciando la recopilación de artículos de Wikipedia en Esperanto...\n")
    
    for categoria, articulos in CATEGORIAS.items():
        print(f"--- Procesando categoría: {categoria} ---")
        parrafos_clase = 0
        
        for titulo in articulos:
            try:
                # any_language=False: no aceptar artículos de otros idiomas si el título
                # no existe en esperanto (evita que se cuele texto en español)
                page = WikiPage.look_up(titulo, language="eo", any_language=False)
                if getattr(page, "language", "eo") != "eo":
                    raise ValueError(f"solo existe en '{page.language}', no en esperanto")
                texto_completo = page.full_text()
                
                # Segmentar por párrafos
                parrafos = texto_completo.split("\n")
                
                for p in parrafos:
                    p_limpio = limpiar_parrafo(p)
                    # Filtramos fragmentos muy cortos (< 40 caracteres)
                    if len(p_limpio) >= 40:
                        filas.append({"text": p_limpio, "class": categoria})
                        parrafos_clase += 1
                        
                print(f"  [OK] {titulo} - párrafos acumulados en la clase: {parrafos_clase}")
            except Exception as e:
                print(f"  [Error] No se pudo obtener '{titulo}': {e}")
        print()

    df = pd.DataFrame(filas)
    
    print("Distribución de párrafos por categoría:")
    print(df["class"].value_counts())
    print(f"\nTotal de párrafos recopilados: {len(df)}")
    
    carpeta_actual = os.path.dirname(os.path.abspath(__file__))
    
    ruta_salida = os.path.join(carpeta_actual, "dataset_esperanto.csv")
    df.to_csv(ruta_salida, sep=";", index=False, encoding="utf-8")
    print(f"\nDataset generado correctamente en: {ruta_salida}")
if __name__ == "__main__":
    construir_dataset()