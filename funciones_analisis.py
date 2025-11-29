import pandas as pd

DEPARTAMENTO = "DEPARTAMENTO"

def ranking_departamentos(gdf, nombre_figura):
    if DEPARTAMENTO not in gdf.columns:
        return pd.DataFrame({DEPARTAMENTO: [], nombre_figura: []})
    return (
        gdf.groupby(DEPARTAMENTO)
        .size()
        .reset_index(name=nombre_figura)
        .sort_values(nombre_figura, ascending=False)
    )

def sumar_area(gdf):
    if "area_ha" in gdf.columns:
        return round(gdf["area_ha"].sum(), 2)
    return "No disponible"