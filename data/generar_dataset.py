"""Genera data/dataset_esperanto.csv descargando los artículos de Wikipedia en esperanto.

Hace lo mismo que el cuaderno con GENERAR_DATASET = True, pero sin abrir el cuaderno.
No repite código: la lista CATEGORIAS y las funciones descargar_articulo, limpiar_parrafo y
construir_dataset se leen de notebooks/clasificacion_esperanto.ipynb, para que los dos generen
siempre el mismo CSV.

Uso: python data/generar_dataset.py
"""
import os
import re
import ast
import json
import time
import pandas as pd

CARPETA = os.path.dirname(os.path.abspath(__file__))
RUTA_CUADERNO = os.path.join(CARPETA, "..", "notebooks", "clasificacion_esperanto.ipynb")
RUTA_SALIDA = os.path.join(CARPETA, "dataset_esperanto.csv")

# Lo que se toma del cuaderno
NOMBRES = ["CATEGORIAS", "descargar_articulo", "limpiar_parrafo", "construir_dataset"]


def leer_del_cuaderno(ruta=RUTA_CUADERNO):
    """Busca en el cuaderno las definiciones de NOMBRES y las devuelve en un diccionario.

    De cada celda solo se ejecutan las definiciones (def y asignaciones de esos nombres), no el resto
    del código, para no lanzar descargas ni gráficos al leerlo.
    """
    with open(ruta, encoding="utf-8") as f:
        cuaderno = json.load(f)

    espacio = {"re": re, "time": time, "pd": pd}
    for celda in cuaderno["cells"]:
        if celda["cell_type"] != "code":
            continue
        codigo = "".join(celda["source"])
        try:
            arbol = ast.parse(codigo)
        except SyntaxError:        # celdas con %pip u otras órdenes de Jupyter
            continue
        for nodo in arbol.body:
            es_funcion = isinstance(nodo, ast.FunctionDef) and nodo.name in NOMBRES
            es_variable = (isinstance(nodo, ast.Assign) and len(nodo.targets) == 1
                           and getattr(nodo.targets[0], "id", None) in NOMBRES)
            if es_funcion or es_variable:
                exec(compile(ast.Module([nodo], []), ruta, "exec"), espacio)

    faltan = [n for n in NOMBRES if n not in espacio]
    if faltan:
        raise ValueError(f"No se encontró {', '.join(faltan)} en {ruta}")
    return espacio


if __name__ == "__main__":
    cuaderno = leer_del_cuaderno()
    print("Iniciando la recopilación de artículos de Wikipedia en Esperanto...\n")
    df = cuaderno["construir_dataset"]()

    print("\nDistribución de párrafos por categoría:")
    print(df["class"].value_counts())
    print(f"\nTotal de párrafos: {len(df)}")

    # Se guarda sin filtrar, igual que el cuaderno: el filtro de ruido se aplica al cargarlo
    df.to_csv(RUTA_SALIDA, sep=";", index=False, encoding="utf-8")
    print(f"\nDataset guardado en: {RUTA_SALIDA}")
