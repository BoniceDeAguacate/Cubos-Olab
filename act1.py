import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Configuración de la página
st.set_page_config(
    page_title="Análisis OLAP de Ventas - CSV",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data
def load_csv_data():
    try:
        # Cargar directamente desde CSV
        df = pd.read_csv('data/ventas.csv', parse_dates=['Fecha'])
        
        # Verificar columnas esenciales
        required_cols = {'Fecha', 'Producto', 'Región', 'Ventas'}
        missing = required_cols - set(df.columns)
        if missing:
            st.error(f"Error: Faltan columnas en el CSV: {missing}")
            st.stop()
        
        # Procesamiento de fechas
        df['Año'] = df['Fecha'].dt.year
        df['Trimestre'] = 'T' + df['Fecha'].dt.quarter.astype(str)
        df['Mes'] = df['Fecha'].dt.month_name(locale='Spanish')
        df['DíaSemana'] = df['Fecha'].dt.day_name(locale='Spanish')
        
        return df
    
    except Exception as e:
        st.error(f"Error cargando CSV: {str(e)}")
        st.stop()

# Cargar datos
df = load_csv_data()

# Sidebar con controles OLAP
st.sidebar.header("Controles OLAP - CSV")

# Operación SLICE: Filtro por año
selected_year = st.sidebar.selectbox(
    'Seleccionar Año',
    options=sorted(df['Año'].unique(), reverse=True)
)

# Operación DICE: Filtros múltiples
selected_products = st.sidebar.multiselect(
    'Seleccionar Productos',
    options=df['Producto'].unique(),
    default=df['Producto'].unique()
)

selected_regions = st.sidebar.multiselect(
    'Seleccionar Regiones',
    options=df['Región'].unique(),
    default=df['Región'].unique()
)

# Aplicar filtros
filtered_df = df[
    (df['Año'] == selected_year) &
    (df['Producto'].isin(selected_products)) &
    (df['Región'].isin(selected_regions))
]

# Main Dashboard
st.title("Análisis OLAP desde CSV")

# KPIs en tarjetas
col1, col2, col3 = st.columns(3)
with col1:
    total_sales = filtered_df['Ventas'].sum()
    st.metric("Ventas Totales", f"${total_sales:,.0f}")

with col2:
    avg_sales = filtered_df['Ventas'].mean()
    st.metric("Ventas Promedio", f"${avg_sales:,.2f}")

with col3:
    prev_year_sales = df[df['Año'] == selected_year-1]['Ventas'].sum()
    growth = ((total_sales / prev_year_sales) - 1)*100 if prev_year_sales != 0 else 0
    st.metric("Crecimiento Anual", f"{growth:.1f}%", 
              delta_color="inverse" if growth < 0 else "normal")

# Visualización 1: Evolución temporal
st.header("Análisis Temporal")
time_level = st.radio(
    "Nivel de agregación:",
    options=['Año', 'Trimestre', 'Mes', 'DíaSemana'],
    horizontal=True
)

time_df = filtered_df.groupby(time_level)['Ventas'].sum().reset_index()
fig1 = px.bar(
    time_df, 
    x=time_level, 
    y='Ventas',
    title=f"Ventas por {time_level} (Click para drill-down)"
)
st.plotly_chart(fig1, use_container_width=True)

# Visualización 2: Matriz OLAP
st.header("Matriz Multidimensional")
pivot_rows = st.selectbox("Filas:", ['Producto', 'Región'])
pivot_cols = st.selectbox("Columnas:", ['Región', 'Producto', 'Trimestre'])

pivot_table = pd.pivot_table(
    filtered_df,
    values='Ventas',
    index=pivot_rows,
    columns=pivot_cols,
    aggfunc='sum',
    fill_value=0
)

st.dataframe(
    pivot_table.style.background_gradient(cmap='Blues'),
    use_container_width=True
)

# Visualización 3: Análisis por producto
st.header("Distribución por Producto")
fig2 = px.pie(
    filtered_df.groupby('Producto')['Ventas'].sum().reset_index(),
    names='Producto',
    values='Ventas',
    hole=0.3
)
st.plotly_chart(fig2, use_container_width=True)

# Descarga de datos filtrados
st.sidebar.download_button(
    "Descargar Datos Filtrados",
    data=filtered_df.to_csv(index=False).encode('utf-8'),
    file_name=f"ventas_filtradas_{selected_year}.csv",
    mime='text/csv'
)