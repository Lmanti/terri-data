import geopandas as gpd
import requests
from io import BytesIO

def cargar_geojson(url):
    response = requests.get(url)
    response.raise_for_status()
    gdf = gpd.read_file(BytesIO(response.content))
    return gdf

def cargar_geojson_local(path):
    return gpd.read_file(path)

def renombrar_columnas(gdf, mapeo):
    return gdf.rename(columns=mapeo)

def eliminar_duplicados(gdf):
    return gdf.drop_duplicates()

def reparar_geometrias(gdf):
    gdf["geometry"] = gdf["geometry"].buffer(0)
    return gdf

def eliminar_geometrias_nulas(gdf):
    return gdf[~gdf["geometry"].isna()]

def estandarizar_crs(gdf):
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    else:
        gdf = gdf.to_crs("EPSG:4326")
    return gdf

def calcular_area_hectareas(gdf):
    # Proyección métrica de Colombia
    gdf_proj = gdf.to_crs("EPSG:3116")
    gdf["area_ha"] = gdf_proj.geometry.area / 10000
    return gdf

def limpiar_gdf(gdf):
    gdf = eliminar_duplicados(gdf)
    gdf = reparar_geometrias(gdf)
    gdf = eliminar_geometrias_nulas(gdf)
    gdf = estandarizar_crs(gdf)
    gdf = calcular_area_hectareas(gdf)
    return gdf