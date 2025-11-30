import time
import geopandas as gpd
import requests
from io import BytesIO
from constantes import DEPARTAMENTO, GEOMETRY, EPSG_4326, EPSG_3116, AREA_HA

def cargar_geojson(url, max_intentos=3, espera=3):
    intento = 1
    
    while intento <= max_intentos:
        try:
            print(f"Intento #{intento}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            gdf = gpd.read_file(BytesIO(response.content))
            print("Datos cargados exitosamente.")
            return gdf
        except requests.exceptions.RequestException as e:
            print(f"⚠ Error: {e}")
            intento += 1
            if intento <= max_intentos:
                print(f"Reintentando en {espera} segundo(s)...\n")
                time.sleep(espera)
    
    print(f"❌ No se pudo obtener el recurso después de {max_intentos} intentos: {url}")
    return gpd.GeoDataFrame()

def separar_datos(gdf, columna):
    if columna not in gdf.columns:
        return gdf
    
    gdf[columna] = gdf[columna].astype(str)
    gdf[columna] = gdf[columna].str.split(",")
    gdf = gdf.explode(columna)
    gdf[columna] = gdf[columna].str.strip()
    return gdf

def reemplazar_codigo_por_nombre(gdf, df_departamentos):
    """
    Reemplaza la columna DEPARTAMENTO (codigos) por los nombres
    usando la tabla oficial de departamentos (df_departamentos).
    """
    if DEPARTAMENTO not in gdf.columns:
        print("No existe columna DEPARTAMENTO en el GDF")
        return gdf

    gdf[DEPARTAMENTO] = gdf[DEPARTAMENTO].astype(str).str.strip()
    gdf[DEPARTAMENTO] = gdf[DEPARTAMENTO].str.zfill(2)

    df_departamentos["codigo_departamento"] = (
        df_departamentos["codigo_departamento"]
        .astype(str)
        .str.zfill(2)
    )
    map_dict = dict(zip(
        df_departamentos["codigo_departamento"],
        df_departamentos["nombre_departamento"]
    ))
    gdf[DEPARTAMENTO] = gdf[DEPARTAMENTO].map(map_dict)
    return gdf

def normalizar_area(gdf, columnas_posibles, columna_salida):
    """
    Toma una lista de nombres de columnas de área y usa la que exista.
    Luego crea una columna AREA_TOTAL combinando esa área original
    con gdf["area_ha"] si está presente.
    """

    col_original = None
    for col in columnas_posibles:
        if col in gdf.columns:
            col_original = col
            break

    if col_original is None:
        gdf[columna_salida] = gdf.get(AREA_HA, None)
        return gdf

    # Convertir columnas a numéricas limpiamente
    gdf[col_original] = (
        gdf[col_original]
        .astype(str)
        .str.replace(",", ".")
        .astype(float)
    )

    gdf[columna_salida] = gdf[col_original]

    return gdf

def limpiar_columnas_conflictivas(gdf):
    conflictivas = [c for c in gdf.columns if c.endswith("_1")]
    return gdf.drop(columns=conflictivas, errors="ignore")

def deduplicar_por_objectid(gdf):
    """
    Busca columnas que representen el ID original del territorio.
    Ejemplos:
        OBJECTID
        OBJECTID_1
        OBJECTID_2
    """
    cols_id = [c for c in gdf.columns if "OBJECTID" in c]

    if len(cols_id) == 0:   # no hay ID → no deduplicamos
        return gdf

    return gdf.drop_duplicates(subset=cols_id)

def identificar_superposiciones(gdf_zrc, gdf_neg, gdf_ind):
    """
    Retorna un diccionario con GeoDataFrames de las intersecciones.
    """
    resultados = {}

    # Limpiar columnas conflictivas
    gdf_zrc = limpiar_columnas_conflictivas(gdf_zrc)
    gdf_neg = limpiar_columnas_conflictivas(gdf_neg)
    gdf_ind = limpiar_columnas_conflictivas(gdf_ind)

    # Intersecciones binarias
    inter_zrc_neg = gpd.overlay(gdf_zrc, gdf_neg, how="intersection", keep_geom_type=False)
    inter_zrc_neg = deduplicar_por_objectid(inter_zrc_neg)

    inter_zrc_ind = gpd.overlay(gdf_zrc, gdf_ind, how="intersection", keep_geom_type=False)
    inter_zrc_ind = deduplicar_por_objectid(inter_zrc_ind)

    inter_neg_ind = gpd.overlay(gdf_neg, gdf_ind, how="intersection", keep_geom_type=False)
    inter_neg_ind = deduplicar_por_objectid(inter_neg_ind)

    # Intersección triple
    inter_triple = gpd.overlay(inter_zrc_neg, gdf_ind, how="intersection", keep_geom_type=False)
    inter_triple = deduplicar_por_objectid(inter_triple)

    # Guardar resultados
    resultados["ZRC ∩ Consejos"] = inter_zrc_neg
    resultados["ZRC ∩ Resguardos"] = inter_zrc_ind
    resultados["Consejos ∩ Resguardos"] = inter_neg_ind
    resultados["ZRC ∩ Consejos ∩ Resguardos"] = inter_triple

    return resultados

def cargar_geojson_local(path):
    return gpd.read_file(path)

def renombrar_columnas(gdf, mapeo):
    return gdf.rename(columns=mapeo)

def eliminar_duplicados(gdf):
    return gdf.drop_duplicates()

def reparar_geometrias(gdf):
    gdf[GEOMETRY] = gdf[GEOMETRY].buffer(0)
    return gdf

def eliminar_geometrias_nulas(gdf):
    return gdf[~gdf[GEOMETRY].isna()]

def estandarizar_crs(gdf):
    if gdf.crs is None:
        gdf = gdf.set_crs(EPSG_4326)
    else:
        gdf = gdf.to_crs(EPSG_4326)
    return gdf

def calcular_area_hectareas(gdf):
    # Proyección métrica de Colombia
    gdf_proj = gdf.to_crs(EPSG_3116)
    gdf[AREA_HA] = gdf_proj.geometry.area / 10000
    return gdf

def limpiar_gdf(gdf): 
    gdf = eliminar_duplicados(gdf)
    gdf = reparar_geometrias(gdf)
    gdf = eliminar_geometrias_nulas(gdf)
    gdf = estandarizar_crs(gdf)
    gdf = calcular_area_hectareas(gdf)
    return gdf

def separar_listas_en_columna(gdf, columna_objetivo, columna_reemplazar):
    if columna_objetivo in gdf.columns:
        if columna_reemplazar in gdf.columns:
            gdf = gdf.drop(columns=[columna_reemplazar])
        gdf = separar_datos(gdf, columna_objetivo)
        gdf = gdf.rename(columns={columna_objetivo: columna_reemplazar})
    return gdf