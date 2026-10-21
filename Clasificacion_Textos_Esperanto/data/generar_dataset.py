import os
import re
import pandas as pd
from esperantilo import WikiPage

# 1. Definición de temáticas y artículos clave en Esperanto
# CATEGORIAS: Variable de tipo diccionario (dict) que define las clases objetivo y sus fuentes de Wikipedia.
# { ... }: Sintaxis de diccionario en Python, estructurado como pares de 'clave: valor'.
CATEGORIAS = {
    # "fervojo": 'Ferrocarril'.
    "fervojo": [
        "Fervojo",            # 'Ferrocarril'
        "Lokomotivo",         # 'Locomotora' 
        "Metroo",             # 'Metro' 
        "Tramo",              # 'Tranvía' 
        "Rapidtrajno",        # 'Tren de alta velocidad' 
        "Vagono",             # 'Vagón' 
        "Fervoja stacio",     # 'Estación de ferrocarril'.
        "Elektra lokomotivo", # 'Locomotora eléctrica'.
        "Dizel-lokomotivo",   # 'Locomotora diésel'.
        "Maglevo"             # 'Tren de levitación magnética' 
    ],
    
    # "automobilo": 'automóvil'
    "automobilo": [
        "Aŭtomobilo",         # 'Automóvil'
        "Kamiono",            # 'Camión' 
        "Aŭtobuso",           # 'Autobús' 
        "Elektra aŭtomobilo", # 'Automóvil eléctrico'.
        "Motociklo",          # 'Motocicleta' 
        "Eksplodmotoro",      # 'Motor de combustión interna' 
        "Taksio",             # 'Taxi' 
        "Aŭtovojo",           # 'Autopista' / 'autovía' 
        "Sportaŭto",          # 'Coche deportivo'
        "Karoserio"           # 'Carrocería'
    ],
    
    # "aviado": aviación
    "aviado": [
        "Aviadilo",           # 'Avión' 
        "Aviado",             # 'Aviación' 
        "Flughaveno",         # 'Aeropuerto'
        "Helikoptero",        # 'Helicóptero' 
        "Jetmotoro",          # 'Motor a reacción' 
        "Komerca aviado",     # 'Aviación comercial' 
        "Boeing 747",         
        "Supersona aviadilo", # 'Avión supersónico' 
        "Flugkompanio",       # 'Aerolínea' 
        "Aeronaŭtiko"         # 'Aeronáutica' 
    ]
}

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
                page = WikiPage.look_up(titulo, language="eo")
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