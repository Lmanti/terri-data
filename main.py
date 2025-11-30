import streamlit as st
from streamlit_keplergl import keplergl_static
from keplergl import KeplerGl
from funciones_gdf import cargar_geojson, limpiar_gdf, cargar_geojson_local, reemplazar_codigo_por_nombre, separar_listas_en_columna, normalizar_area
from funciones_analisis import ranking_departamentos, sumar_area
from funciones_sodapy import cargar_json_sodapy
from constantes import DEPARTAMENTO, CODIGO_DEP, AREA_TOTAL, AREA_HA

# ------------------------------------------------------------
# CONSTANTES
# ------------------------------------------------------------
geojson_comunidades_negras = "https://utility.arcgis.com/usrsvcs/servers/abf2f9f6727b4073902c1f57c280d5dc/rest/services/DatosAbiertos/Consejo_Comunitario_Titulado/FeatureServer/0/query?outFields=*&where=1%3D1&f=geojson"
# geojson_resguardos_indigenas = "https://utility.arcgis.com/usrsvcs/servers/8944116ccfd34a7189c4bc44b8e19186/rest/services/DatosAbiertos/Resguardo_Indigena_Formalizado/FeatureServer/0/query?outFields=*&where=1%3D1&f=geojson"
geojson_resguardos_indigenas_local = "./Resguardo_Indigena_Formalizado.geojson"
geojson_zonas_reserva_campesina = "https://utility.arcgis.com/usrsvcs/servers/0eca5beb8afe43708622fdd7646cd577/rest/services/DatosAbiertos/Zonas_de_Reserva_Campesina_Constituida/FeatureServer/0/query?outFields=*&where=1%3D1&f=geojson"
server_divipola = "vcjz-niiq"

# ------------------------------------------------------------
# CONFIGURAR EL DASHBOARD
# ------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard – Territorios Colectivos en Colombia",
    layout="wide"
)

st.title("📍 Dashboard – Territorios Colectivos en Colombia")

st.markdown("""
Este dashboard permite visualizar:
- Distribución geográfica de Zonas de Reserva Campesina (ZRC)
- Resguardos Indígenas
- Consejos Comunitarios (Comunidades Negras)
- Ranking departamental
- Estadísticas de extensión territorial
""")

# ------------------------------------------------------------
# CARGAR DATOS (con caché para mejor rendimiento)
# ------------------------------------------------------------
@st.cache_data
def cargar_datos():
    print("\nCargando datos de negritudes...")
    gdf_neg = cargar_geojson(geojson_comunidades_negras)
    print("Cargando datos de reservas campesinas...")
    gdf_camp = cargar_geojson(geojson_zonas_reserva_campesina)
    print("Cargando datos de resguardos indígenas...")
    gdf_indg = cargar_geojson_local(geojson_resguardos_indigenas_local)
    print("Cargando datos de DAVIPOLA...")
    gdf_dvp = cargar_json_sodapy(server_divipola)
    
    if gdf_neg.empty or gdf_camp.empty or gdf_indg.empty or gdf_dvp.empty:
        st.error(f"No se ha podido obtener datos.")
        st.stop()
    
    # Limpiar geodataframes
    gdf_neg = limpiar_gdf(gdf_neg)
    gdf_camp = limpiar_gdf(gdf_camp)
    gdf_indg = limpiar_gdf(gdf_indg)
    
    return gdf_neg, gdf_camp, gdf_indg, gdf_dvp

with st.spinner("Cargando datos..."):
    gdf_negritudes, gdf_campesinado, gdf_indigenas, gdf_divipola = cargar_datos()

    # Se separan las listas (varios registros en una celda)
    gdf_negritudes_normalizado = separar_listas_en_columna(gdf_negritudes, CODIGO_DEP, DEPARTAMENTO)
    gdf_campesinado_normalizado = separar_listas_en_columna(gdf_campesinado, CODIGO_DEP, DEPARTAMENTO)
    gdf_indigenas_normalizado = separar_listas_en_columna(gdf_indigenas, CODIGO_DEP, DEPARTAMENTO)

    # Reemplazar códigos por nombres (departamentos)
    gdf_neg_integrado = reemplazar_codigo_por_nombre(gdf_negritudes_normalizado, gdf_divipola)
    gdf_camp_integrado = reemplazar_codigo_por_nombre(gdf_campesinado_normalizado, gdf_divipola)
    gdf_indg_integrado = reemplazar_codigo_por_nombre(gdf_indigenas_normalizado, gdf_divipola)

st.success("✓ Datos cargados correctamente")

# ------------------------------------------------------------
# SECCIÓN: MAPA KEPLER.GL
# ------------------------------------------------------------
st.subheader("🗺️ Mapa interactivo de territorios")

# Crear el mapa (siempre, no solo con botón)
with st.spinner("Generando mapa..."):
    mapa = KeplerGl(height=600)
    
    mapa.add_data(data=gdf_camp_integrado, name="Zonas de Reserva Campesina")
    mapa.add_data(data=gdf_neg_integrado, name="Consejos Comunitarios Negritudes")
    mapa.add_data(data=gdf_indg_integrado, name="Resguardo Indigena Formalizado")
    
    # Renderizar el mapa en Streamlit
    keplergl_static(mapa, height=600)

# ------------------------------------------------------------
# SECCIÓN: ESTADÍSTICAS
# ------------------------------------------------------------
st.subheader("📊 Estadísticas descriptivas")

st.markdown("### Conteo por figura territorial")

col1, col2, col3 = st.columns(3)

col1.metric("ZRC", len(gdf_campesinado))
col2.metric("Consejos Comunitarios", len(gdf_negritudes))
col3.metric("Resguardo Indigena", len(gdf_indigenas))

# ------------------------------------------------------------
# Ranking departamental
# ------------------------------------------------------------
st.markdown("### 🏆 Ranking de departamentos con más territorios")

rank_zrc = ranking_departamentos(gdf_camp_integrado, "ZRC")
rank_con = ranking_departamentos(gdf_neg_integrado, "Consejos")
rank_res = ranking_departamentos(gdf_indg_integrado, "Resguardos")

ranking_total = rank_zrc.merge(rank_con, on=DEPARTAMENTO, how="outer") \
    .merge(rank_res, on=DEPARTAMENTO, how="outer") \
    .fillna(0)

st.dataframe(ranking_total, use_container_width=True)

# ------------------------------------------------------------
# Extensión territorial
# ------------------------------------------------------------
st.markdown("### 📐 Extensión territorial (ha)")

gdf_campesinado_area_normalizada = normalizar_area(gdf_campesinado, ["Area_HA", "AREA_TOTAL_ACTOS_ADMIN"], AREA_TOTAL)
gdf_negritudes_area_normalizada = normalizar_area(gdf_negritudes, ["Area_HA", "AREA_TOTAL_ACTOS_ADMIN"], AREA_TOTAL)
gdf_indigenas_area_normalizada = normalizar_area(gdf_indigenas, ["Area_HA", "AREA_TOTAL_ACTOS_ADMIN"], AREA_TOTAL)

col1, col2, col3 = st.columns(3)

col1.metric("Área total ZRC (ha)", sumar_area(gdf_campesinado_area_normalizada, AREA_TOTAL))
col1.metric("Área total ZRC calculada (ha)", sumar_area(gdf_campesinado, AREA_HA))
col2.metric("Área total Consejos (ha)", sumar_area(gdf_negritudes_area_normalizada, AREA_TOTAL))
col2.metric("Área total Consejos calculada (ha)", sumar_area(gdf_negritudes, AREA_HA))
col3.metric("Área total Resguardos (ha)", sumar_area(gdf_indigenas_area_normalizada, AREA_TOTAL))
col3.metric("Área total Resguardos calculada (ha)", sumar_area(gdf_indigenas, AREA_HA))

# ------------------------------------------------------------
# FIN DEL DASHBOARD
# ------------------------------------------------------------
st.markdown("___")
st.markdown("Dashboard generado con **Streamlit + Kepler.gl + GeoPandas**.")