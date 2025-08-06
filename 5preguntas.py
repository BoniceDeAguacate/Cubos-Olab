import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Configuración de la página
st.set_page_config(
    page_title="Análisis OLAP Visual",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Carga de datos
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('data/ventas.csv', parse_dates=['Fecha'])
        
        # Procesamiento para análisis OLAP
        df['Año'] = df['Fecha'].dt.year
        df['Trimestre'] = 'T' + df['Fecha'].dt.quarter.astype(str)
        df['Mes'] = df['Fecha'].dt.month_name(locale='Spanish')
        
        return df
    
    except Exception as e:
        st.error(f"Error cargando datos: {str(e)}")
        st.stop()

df = load_data()

# Título principal
st.title("Visualización de Respuestas OLAP")

## Pregunta 1: Diferencias por año (Roll-up)
st.header("1. Diferencias al agrupar por año (Roll-up)")
st.write("""
**Análisis:** Comparación de ventas agregadas por mes vs por año, mostrando cómo el roll-up revela tendencias macro.
""")

# Gráfica comparativa
col1, col2 = st.columns(2)
with col1:
    fig1a = px.line(
        df.groupby(['Año', 'Mes'])['Ventas'].sum().reset_index(),
        x='Mes', y='Ventas', color='Año',
        title="Ventas Mensuales (Detalle)"
    )
    st.plotly_chart(fig1a, use_container_width=True)

with col2:
    fig1b = px.bar(
        df.groupby('Año')['Ventas'].sum().reset_index(),
        x='Año', y='Ventas',
        title="Ventas Anuales (Roll-up)"
    )
    st.plotly_chart(fig1b, use_container_width=True)

## Pregunta 2: Productos con ventas parejas (Dice)
st.header("2. Productos con ventas consistentes por región (Dice)")
st.write("""
**Análisis:** Desviación estándar de ventas por producto entre regiones, mostrando consistencia.
""")

# Cálculo de consistencia
product_consistency = df.groupby(['Producto', 'Región'])['Ventas'].sum().unstack().std(axis=1).reset_index()
product_consistency.columns = ['Producto', 'Desviación']

fig2 = px.bar(
    product_consistency.sort_values('Desviación'),
    x='Producto', y='Desviación',
    color='Desviación',
    title="Consistencia de Ventas por Producto (Menor desviación = más consistente)"
)
st.plotly_chart(fig2, use_container_width=True)

## Pregunta 3: Región líder por trimestre (Slice + Roll-up)
st.header("3. Región líder en Q2 2024 (Slice + Roll-up)")

# Filtro para Q2 2024
q2_2024 = df[(df['Trimestre'] == 'T2') & (df['Año'] == 2024)]
region_sales = q2_2024.groupby('Región')['Ventas'].sum().reset_index()

fig3 = px.pie(
    region_sales,
    names='Región', values='Ventas',
    title="Distribución de Ventas por Región en Q2 2024",
    hole=0.3
)
st.plotly_chart(fig3, use_container_width=True)

## Pregunta 4: Comparación con/sin filtros (Slice)
st.header("4. Impacto de aplicar filtros (Slice)")

# Selectores
col1, col2 = st.columns(2)
with col1:
    selected_region = st.selectbox(
        'Selecciona región:',
        options=df['Región'].unique()
    )
with col2:
    selected_product = st.selectbox(
        'Selecciona producto:',
        options=['Todos'] + list(df['Producto'].unique())
    )

# Preparar datos
df_all = df.groupby('Mes')['Ventas'].sum().reset_index()
df_all['Tipo'] = 'Todos los datos'

df_filtered = df[df['Región'] == selected_region]
if selected_product != 'Todos':
    df_filtered = df_filtered[df_filtered['Producto'] == selected_product]
    
df_filtered = df_filtered.groupby('Mes')['Ventas'].sum().reset_index()
df_filtered['Tipo'] = f'Filtrado: {selected_region}' + \
                     (f' + {selected_product}' if selected_product != 'Todos' else '')

comparison_df = pd.concat([df_all, df_filtered])

# Gráfico de líneas comparativo
fig = px.line(
    comparison_df,
    x='Mes',
    y='Ventas',
    color='Tipo',
    title=f"Evolución Mensual de Ventas: Comparación Global vs Filtrado",
    labels={'Ventas': 'Ventas Totales (USD)', 'Mes': 'Periodo'},
    color_discrete_sequence=['#636EFA', '#EF553B'],
    line_dash='Tipo',
    markers=True
)

# Personalización
fig.update_layout(
    hovermode='x unified',
    legend_title_text='Dataset',
    xaxis_title='Mes',
    yaxis_title='Ventas Totales (USD)',
    xaxis={'type': 'category', 'tickangle': 45}
)

# Líneas verticales para trimestres
for month_idx in [3, 6, 9]:
    fig.add_vline(
        x=month_idx-0.5, 
        line_width=1, 
        line_dash="dash", 
        line_color="grey"
    )

# Mostrar gráfico y análisis
st.plotly_chart(fig, use_container_width=True)

# Análisis comparativo
st.subheader("Análisis Comparativo")
col1, col2 = st.columns(2)

with col1:
    st.metric(
        "Ventas Totales (Filtrado)", 
        f"${df_filtered['Ventas'].sum():,.0f}",
        f"{df_filtered['Ventas'].sum()/df_all['Ventas'].sum():.1%} del total"
    )

with col2:
    st.metric(
        "Diferencia Promedio Mensual", 
        f"${df_filtered['Ventas'].mean() - df_all['Ventas'].mean():+,.0f}",
        f"{df_filtered['Ventas'].mean()/df_all['Ventas'].mean():.1%} del promedio"
    )
## Pregunta 5: Rendimiento con filtros
st.header("5. Rendimiento de filtros y cálculo")

# Simulación de rendimiento
import time

col1, col2 = st.columns(2)
with col1:
    st.write("**Prueba de velocidad:**")
    start_time = time.time()
    filtered = df[df['Año'] == 2024]
    calc_time = time.time() - start_time
    st.metric("Tiempo de filtrado (5,000 registros)", f"{calc_time:.4f} seg")

with col2:
    st.write("**Recomendación:**")
    st.markdown("""
    - Datos pequeños (<10K filas): Cálculo en tiempo real
    - Datos grandes (>100K filas): Cubos precalculados
    """)

# Notas finales
st.markdown("---")
st.write("**Instrucciones:**")
st.write("1. Explora cada gráfico interactivamente")
st.write("2. Usa los controles para filtrar datos")
st.write("3. Descarga imágenes con el menú de cada gráfico")

# Para ejecutar: streamlit run nombre_archivo.py