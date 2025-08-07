"""
Página para visualizar y gestionar el historial de cotizaciones.

Esta página permite al usuario:
1. Ver una lista de todas las cotizaciones guardadas.
2. Buscar cotizaciones por ID o por nombre de cliente.
3. Filtrar cotizaciones por su estado (Borrador, Aprobada).
4. Seleccionar una cotización de la tabla para ver sus detalles completos.
5. Realizar acciones sobre la cotización seleccionada: Aprobar, mover a borrador,
   eliminar o generar un PDF.
"""
import streamlit as st
import pandas as pd
import data_manager
import pdf_generator

# --- Page Configuration ---
st.set_page_config(page_title="Historial de Cotizaciones", page_icon="📚", layout="wide")
st.title("📚 Historial de Cotizaciones")

# --- Load Data ---
clients_df = data_manager.load_clients()
quotes_df = data_manager.load_quotes()
quote_items_df = data_manager.load_quote_items()

# --- Main Logic ---
if quotes_df.empty:
    st.info("No hay cotizaciones guardadas en el historial. Crea una desde la página '📝 Cotizador'.")
    st.stop()

# --- Merge data for a richer display ---
# Se combinan las cotizaciones con los nombres de los clientes para una visualización más amigable.
quotes_with_clients = pd.merge(quotes_df, clients_df, on="client_id", how="left")
# Se crea una columna de visualización para el cliente.
quotes_with_clients['client_display'] = quotes_with_clients.apply(
    lambda row: f"{row.get('name', 'Cliente no encontrado')} ({row.get('company', 'N/A')})", axis=1
)

# --- Filtering and Searching ---
st.header("Buscar y Filtrar Cotizaciones")
col1, col2 = st.columns([0.7, 0.3])
with col1:
    search_term = st.text_input("Buscar por ID de cotización o nombre de cliente", placeholder="Escribe para buscar...")
with col2:
    status_options = ["Borrador", "Aprobada"]
    selected_statuses = st.multiselect("Filtrar por Estado", options=status_options, default=status_options)

# Lógica de filtrado y búsqueda.
filtered_quotes = quotes_with_clients[quotes_with_clients["status"].isin(selected_statuses)]
if search_term:
    search_term = search_term.lower()
    filtered_quotes = filtered_quotes[
        filtered_quotes['client_display'].str.lower().str.contains(search_term) |
        filtered_quotes['quote_id'].astype(str).str.contains(search_term)
    ]

# --- Display Filtered Quotes Table ---
st.header("Resultados")
if filtered_quotes.empty:
    st.warning("No se encontraron cotizaciones con los filtros actuales.")
else:
    # Se utiliza un dataframe con selección de fila única para ver detalles.
    selected_quote_df = st.dataframe(
        filtered_quotes[["quote_id", "client_display", "quote_date", "total_amount", "status"]],
        use_container_width=True,
        hide_index=True,
        column_config={"quote_id": "ID", "client_display": "Cliente", "quote_date": "Fecha", "total_amount": "Monto Total", "status": "Estado"},
        selection_mode="single-row",
        key="quote_selector"
    )

    # --- Detailed View and Actions ---
    # Se muestra la vista detallada solo si el usuario ha seleccionado una fila.
    if not selected_quote_df.selection.rows:
        st.info("Haz clic en una fila de la tabla para ver los detalles y las acciones disponibles.")
    else:
        selected_row_index = selected_quote_df.selection.rows[0]
        selected_quote_id = filtered_quotes.iloc[selected_row_index]["quote_id"]

        st.markdown("---")
        st.header(f"Detalles de la Cotización #{selected_quote_id}")

        # Se obtienen los datos completos de la cotización seleccionada.
        quote_details = filtered_quotes[filtered_quotes["quote_id"] == selected_quote_id].iloc[0]
        items = quote_items_df[quote_items_df["quote_id"] == selected_quote_id]
        client_details = clients_df[clients_df["client_id"] == quote_details['client_id']].iloc[0]

        # Muestra de detalles y conceptos.
        detail_col1, detail_col2 = st.columns(2)
        with detail_col1:
            st.markdown(f"**Cliente:** {quote_details['client_display']}")
            st.markdown(f"**Fecha:** {quote_details['quote_date']}")
            st.markdown(f"**Estado:** {quote_details['status']}")
        with detail_col2:
            st.markdown(f"**Monto Total:** ${quote_details['total_amount']:,.2f}")
            if pd.notna(quote_details.get('payment_method')):
                st.markdown(f"**Forma de Pago:** {quote_details['payment_method']}")

        st.info(f"**Notas:** {quote_details.get('notes', 'Sin notas')}")

        st.subheader("Conceptos:")
        if 'discount_percent' in items.columns and items['discount_percent'].fillna(0).sum() > 0:
            st.table(items[['description', 'quantity', 'unit_price', 'discount_percent']])
        else:
            st.table(items[['description', 'quantity', 'unit_price']])

        # --- Botones de Acción ---
        st.subheader("Acciones")
        action_cols = st.columns(4)
        current_status = quote_details['status']

        # Cambiar estado.
        if current_status == "Borrador":
            if action_cols[0].button("✅ Aprobar", key=f"approve_{selected_quote_id}", use_container_width=True):
                quotes_df.loc[quotes_df["quote_id"] == selected_quote_id, "status"] = "Aprobada"
                data_manager.save_quotes(quotes_df)
                st.success(f"Cotización #{selected_quote_id} marcada como Aprobada."); st.rerun()
        elif current_status == "Aprobada":
            if action_cols[0].button("🔄 Pasar a Borrador", key=f"draft_{selected_quote_id}", use_container_width=True):
                quotes_df.loc[quotes_df["quote_id"] == selected_quote_id, "status"] = "Borrador"
                data_manager.save_quotes(quotes_df)
                st.warning(f"Cotización #{selected_quote_id} marcada como Borrador."); st.rerun()

        # Generar PDF.
        pdf_bytes = pdf_generator.create_quote_pdf(quote_details, client_details, items)
        action_cols[1].download_button(label="📄 Generar PDF", data=pdf_bytes, file_name=f"Cotizacion_{selected_quote_id}.pdf", mime="application/pdf", use_container_width=True)

        # Eliminar (sin confirmación en esta versión para simplificar).
        if action_cols[3].button("❌ Eliminar", key=f"delete_{selected_quote_id}", use_container_width=True):
            quotes_df_new = quotes_df[quotes_df["quote_id"] != selected_quote_id]
            quote_items_df_new = quote_items_df[quote_items_df["quote_id"] != selected_quote_id]
            data_manager.save_quotes(quotes_df_new)
            data_manager.save_quote_items(quote_items_df_new)
            st.success(f"Cotización #{selected_quote_id} eliminada."); st.rerun()
