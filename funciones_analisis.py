import pandas as pd
from constantes import DEPARTAMENTO

def ranking_departamentos(gdf, nombre_figura):
    if DEPARTAMENTO not in gdf.columns:
        return pd.DataFrame({DEPARTAMENTO: [], nombre_figura: []})
    return (
        gdf.groupby(DEPARTAMENTO)
        .size()
        .reset_index(name=nombre_figura)
        .sort_values(nombre_figura, ascending=False)
    )

def sumar_area(gdf, columna):
    if columna in gdf.columns:
        return round(gdf[columna].sum(), 2)
    return "No disponible"

def resumen_superposiciones(superposiciones):
    resumen = {
        nombre: len(gdf)
        for nombre, gdf in superposiciones.items()
    }
    df_resumen = pd.DataFrame.from_dict(resumen, orient="index", columns=["Número de zonas"])
    return df_resumen