import streamlit as st

st.set_page_config(
    page_title="Cotizador Pro",
    page_icon="🛠️",
)

st.title("🛠️ Cotizador Pro")

st.write(
    "Bienvenido a Cotizador Pro. Esta es una herramienta para ayudarte a "
    "crear, gestionar y dar seguimiento a tus cotizaciones de forma eficiente."
)

st.sidebar.success("Selecciona una página arriba.")

st.markdown(
    """
    ### ¿Cómo empezar?
    - **Clientes**: Ve a la página de `Clientes` para agregar o administrar tu base de datos de clientes.
    - **Cotizador**: Usa el `Cotizador` para crear una nueva cotización para un cliente existente.
    - **Historial**: Consulta todas tus cotizaciones guardadas, ve su estado y genera PDFs en la página de `Historial`.
    """
)
