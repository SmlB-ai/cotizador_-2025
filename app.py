"""
Página Principal de la Aplicación Cotizador Pro v2.0.

Esta página sirve como el dashboard principal, mostrando un resumen
de la actividad y guiando al usuario a las diferentes secciones.
"""
import streamlit as st
import data_manager

# --- Page Configuration ---
st.set_page_config(
    page_title="Cotizador Pro - Principal",
    page_icon="🛠️",
    layout="wide"
)

st.title("🛠️ Cotizador Pro v2.0")
st.markdown("Bienvenido a tu centro de control de cotizaciones.")

# --- Load Data ---
quotes_df = data_manager.load_quotes()
clients_df = data_manager.load_clients()

# --- Dashboard Metrics ---
st.header("Resumen General")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="Total de Clientes",
        value=len(clients_df)
    )

with col2:
    st.metric(
        label="Total de Cotizaciones",
        value=len(quotes_df)
    )

with col3:
    if not quotes_df.empty and 'status' in quotes_df.columns:
        approved_quotes = quotes_df[quotes_df['status'] == 'Aprobada']
        st.metric(
            label="Cotizaciones Aprobadas",
            value=len(approved_quotes)
        )
    else:
        st.metric(
            label="Cotizaciones Aprobadas",
            value=0
        )

st.sidebar.success("Selecciona una página para empezar.")

st.markdown("---")

st.subheader("Guía Rápida")
st.markdown(
    """
    1.  **⚙️ Configuración**: Empieza aquí. Ingresa los datos de tu empresa, tu logo y tus datos fiscales. Esta información aparecerá en tus cotizaciones en PDF.
    2.  **👥 Clientes**: Administra tu base de datos de clientes. Puedes agregar, editar y eliminar clientes.
    3.  **📝 Cotizador**: Crea nuevas cotizaciones de forma rápida y flexible, aplicando descuentos por producto o un descuento general.
    4.  **📚 Historial**: Busca, visualiza y gestiona todas tus cotizaciones pasadas. Desde aquí puedes aprobarlas o generar sus PDFs.
    """
)
