"""Reportes geográficos sobre los datos ya filtrados del dashboard."""
import html
import json
from pathlib import Path

import altair as alt
import pandas as pd
import pydeck as pdk
import streamlit as st

from metrics import calcular_metricas

UBICACIONES = Path(__file__).with_name('ubicaciones_comercios.csv')
INDICADORES = {
    'Monto colocado ($)': 'monto_liquidado',
    'Créditos liquidados': 'liquidadas',
    'Consultas brutas': 'total_consultas',
    'Aprobación / oferta (%)': 'pct_aprobacion',
    'Conversión a liquidado (%)': 'pct_conversion_bruta',
}


def resumir(datos, agrupacion):
    filas = []
    for nombre, grupo in datos.groupby(agrupacion, dropna=False):
        metricas = calcular_metricas([
            {'estado': r.Estado, 'monto': r.Monto}
            for r in grupo.itertuples()
        ])
        filas.append({agrupacion: nombre, **metricas})
    return pd.DataFrame(filas)


def mostrar_reportes(datos, pesos):
    st.header('Reportes y gráficos')
    st.caption('Se aplican la cartera, el período, los comercios y las localidades seleccionados. Colocación y conversión consideran créditos liquidados.')
    if datos.empty:
        st.info('No hay datos para los filtros seleccionados.')
        return
    indicador = st.selectbox('Indicador a analizar', list(INDICADORES), key='indicador_reportes')
    campo = INDICADORES[indicador]
    minimo = st.number_input('Mínimo de consultas para comparar localidades', min_value=1, value=1, step=1)
    datos = datos.copy()
    referencias = json.loads(Path(__file__).with_name('referencias_localidades.json').read_text())
    datos['Provincia'] = datos['Localidad'].map(lambda loc: referencias.get(loc, {}).get('Provincia', 'A confirmar'))
    datos.loc[datos['Comercio'].str.contains(r'KELLER|SUNRA', case=False, na=False), 'Provincia'] = 'Buenos Aires'
    nivel = st.radio('Agrupar por', ['Localidad', 'Provincia'], horizontal=True)
    localidades = resumir(datos, nivel).rename(columns={nivel: 'Localidad'})
    comparacion = localidades[localidades['total_consultas'] >= minimo].copy()
    st.subheader('Comparación por ' + nivel.lower())
    st.caption('Las localidades actuales se estiman a partir del nombre del comercio. “Otras Localidades” agrupa comercios sin localidad identificada. Los porcentajes reflejan el estado actual del reporte.')
    if comparacion.empty:
        st.info('Ninguna localidad alcanza el mínimo de consultas seleccionado.')
    else:
        grafico = alt.Chart(comparacion).mark_bar(color='#f78b21', cornerRadiusEnd=4).encode(
            x=alt.X(campo + ':Q', title=indicador),
            y=alt.Y('Localidad:N', sort='-x', title=None),
            tooltip=[alt.Tooltip('Localidad:N'), alt.Tooltip(campo + ':Q', title=indicador, format=',.2f'), alt.Tooltip('total_consultas:Q', title='Consultas'), alt.Tooltip('total_con_oferta:Q', title='Con oferta'), alt.Tooltip('liquidadas:Q', title='Liquidados')],
        ).properties(height=max(240, len(comparacion) * 28))
        st.altair_chart(grafico, use_container_width=True)
        tabla = comparacion[['Localidad', 'total_consultas', 'total_con_oferta', 'liquidadas', 'monto_liquidado', 'pct_aprobacion', 'pct_conversion_bruta']].rename(columns={'total_consultas': 'Consultas', 'total_con_oferta': 'Con oferta', 'liquidadas': 'Liquidados', 'monto_liquidado': 'Monto colocado', 'pct_aprobacion': 'Oferta (%)', 'pct_conversion_bruta': 'Conversión (%)'})
        st.dataframe(tabla.style.format({'Monto colocado': pesos, 'Oferta (%)': '{:.2f}%', 'Conversión (%)': '{:.2f}%'}), hide_index=True, use_container_width=True)
        st.markdown(f"**Total del monto colocado en las localidades mostradas: {pesos(comparacion['monto_liquidado'].sum())}**")
    st.subheader('Mapa de comercios · Referencias por localidad')
    st.caption('Puntos simbólicos en el centro de cada localidad, no direcciones exactas. Un punto agrupa los comercios de esa localidad. Fuente geográfica: Georef Argentina.')
    localidades_mapa = resumir(datos, 'Localidad')
    referencias_df = pd.DataFrame.from_dict(referencias, orient='index').rename_axis('Localidad').reset_index()
    puntos = localidades_mapa.merge(referencias_df, on='Localidad', how='inner', validate='one_to_one')
    cantidades = datos.groupby('Localidad')['Comercio'].nunique()
    puntos['comercios'] = puntos['Localidad'].map(cantidades)
    pendientes = datos[~datos['Localidad'].isin(referencias)].groupby(['Comercio', 'Localidad'], as_index=False).size().rename(columns={'size': 'Consultas'})
    st.caption(f"{int(puntos['comercios'].sum())} comercios agrupados en {len(puntos)} localidades. {pendientes['Comercio'].nunique()} comercios pendientes de ubicación.")
    if puntos.empty:
        st.info('No hay localidades identificadas para estos filtros.')
    else:
        puntos['nombre_seguro'] = puntos['Localidad'].map(html.escape)
        puntos['valor'] = puntos[campo].map(lambda v: f'{v:,.2f}')
        maximo = puntos[campo].max()
        puntos['radio'] = 1500 + (puntos[campo] / maximo * 12000 if maximo > 0 else 0)
        capa = pdk.Layer('ScatterplotLayer', puntos, id='localidades', get_position='[Longitud, Latitud]', get_radius='radio', radius_min_pixels=7, radius_max_pixels=35, get_fill_color=[247, 139, 33, 190], pickable=True, auto_highlight=True)
        evento = st.pydeck_chart(pdk.Deck(layers=[capa], initial_view_state=pdk.ViewState(latitude=-38.4, longitude=-64, zoom=3), map_style=pdk.map_styles.LIGHT, tooltip={'text': '{nombre_seguro} · {Provincia}\nReferencia aproximada\nComercios: {comercios}\n' + indicador + ': {valor}\nConsultas: {total_consultas}'}), on_select='rerun', selection_mode='single-object', key='mapa_reportes')
        seleccion = evento.selection.get('indices', {}).get('localidades', [])
        if seleccion:
            st.session_state['localidad_reporte'] = puntos.iloc[seleccion[0]]['Localidad']
    if not pendientes.empty:
        with st.expander('Comercios con provincia o localidad a confirmar'):
            st.dataframe(pendientes, hide_index=True, use_container_width=True)
            st.download_button('Descargar pendientes de ubicación', pendientes.to_csv(index=False).encode('utf-8-sig'), 'ubicaciones_a_confirmar.csv', 'text/csv')
    st.caption('Tocá un punto del mapa o elegí una localidad para ver los comercios agrupados.')
    localidad = st.selectbox('Explorar comercios de una localidad', sorted(datos['Localidad'].dropna().unique()), key='localidad_reporte')
    detalle = resumir(datos[datos['Localidad'] == localidad], 'Comercio')
    detalle = detalle[['Comercio', 'total_consultas', 'liquidadas', 'monto_liquidado', 'pct_aprobacion', 'pct_conversion_bruta']].rename(columns={'total_consultas': 'Consultas', 'liquidadas': 'Liquidados', 'monto_liquidado': 'Monto colocado', 'pct_aprobacion': 'Oferta (%)', 'pct_conversion_bruta': 'Conversión (%)'})
    st.dataframe(detalle.style.format({'Monto colocado': pesos, 'Oferta (%)': '{:.2f}%', 'Conversión (%)': '{:.2f}%'}), hide_index=True, use_container_width=True)
    st.markdown(f"**Total del monto colocado en {html.escape(str(localidad))}: {pesos(detalle['Monto colocado'].sum())}**")
