import streamlit as st
import pandas as pd
import os
from pdf_generator import create_quote_pdf

# --- Page Configuration ---
st.set_page_config(page_title="Historial", page_icon="📚")
st.title("📚 Historial de Cotizaciones")

# --- Data Loading Functions ---
def load_data(file_path, columns):
    """Generic function to load data from a CSV file."""
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        try:
            return pd.read_csv(file_path)
        except pd.errors.EmptyDataError:
            return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

def save_data(df, file_path):
    """Generic function to save a DataFrame to a CSV file."""
    df.to_csv(file_path, index=False)

# Load all data
clients_df = load_data("data/clients.csv", ["client_id", "name", "company", "phone", "email"])
quotes_df = load_data("data/quotes.csv", ["quote_id", "client_id", "quote_date", "total_amount", "discount", "notes", "status", "payment_method"])
quote_items_df = load_data("data/quote_items.csv", ["item_id", "quote_id", "description", "quantity", "unit_price", "discount_percent"])

# --- Main Logic ---
if quotes_df.empty:
    st.info("No hay cotizaciones guardadas en el historial.")
else:
    # Merge quotes with client names for better display
    quotes_with_clients = pd.merge(quotes_df, clients_df, on="client_id", how="left")
    quotes_with_clients['client_display'] = quotes_with_clients.apply(lambda row: f"{row['name']} ({row.get('company', 'N/A')})", axis=1)

    # --- Filtering ---
    st.header("Filtrar Cotizaciones")
    status_options = quotes_with_clients["status"].unique().tolist()
    selected_statuses = st.multiselect("Filtrar por Estado", options=status_options, default=status_options)

    filtered_quotes = quotes_with_clients[quotes_with_clients["status"].isin(selected_statuses)]

    # --- Display Filtered Quotes ---
    st.header("Cotizaciones")
    st.dataframe(
        filtered_quotes[["quote_id", "client_display", "quote_date", "total_amount", "status"]],
        use_container_width=True,
        column_config={"quote_id": "ID", "client_display": "Cliente", "quote_date": "Fecha", "total_amount": "Monto Total", "status": "Estado"}
    )

    # --- Detailed View and Actions ---
    st.header("Ver Detalles y Acciones")
    if not filtered_quotes.empty:
        quote_ids = filtered_quotes["quote_id"].tolist()
        selected_quote_id = st.selectbox("Selecciona una cotización para ver sus detalles", options=quote_ids, format_func=lambda x: f"Cotización #{x}")

        if selected_quote_id:
            # Get selected quote details
            quote_details = filtered_quotes[filtered_quotes["quote_id"] == selected_quote_id].iloc[0]
            items = quote_items_df[quote_items_df["quote_id"] == selected_quote_id]

            # Display details
            st.subheader(f"Detalles de la Cotización #{selected_quote_id}")
            st.text(f"Cliente: {quote_details['client_display']}")
            st.text(f"Fecha: {quote_details['quote_date']}")
            st.text(f"Monto Total: ${quote_details['total_amount']:,.2f}")
            st.text(f"Estado: {quote_details['status']}")
            if pd.notna(quote_details.get('payment_method')):
                st.text(f"Forma de Pago: {quote_details['payment_method']}")
            st.info(f"Notas: {quote_details['notes']}")

            st.subheader("Conceptos:")
            # Display discount column if it exists and has non-zero values
            if 'discount_percent' in items.columns and items['discount_percent'].sum() > 0:
                st.table(items[['description', 'quantity', 'unit_price', 'discount_percent']])
            else:
                st.table(items[['description', 'quantity', 'unit_price']])

            # --- Action Buttons ---
            st.subheader("Acciones")
            cols = st.columns(4)
            current_status = quote_details['status']

            # Change Status Button
            if current_status == "Borrador":
                if cols[0].button("✅ Aprobar", key=f"approve_{selected_quote_id}"):
                    quotes_df.loc[quotes_df["quote_id"] == selected_quote_id, "status"] = "Aprobada"
                    save_data(quotes_df, "data/quotes.csv")
                    st.success(f"Cotización #{selected_quote_id} marcada como Aprobada.")
                    st.rerun()
            elif current_status == "Aprobada":
                if cols[0].button("🔄 Pasar a Borrador", key=f"draft_{selected_quote_id}"):
                    quotes_df.loc[quotes_df["quote_id"] == selected_quote_id, "status"] = "Borrador"
                    save_data(quotes_df, "data/quotes.csv")
                    st.warning(f"Cotización #{selected_quote_id} marcada como Borrador.")
                    st.rerun()

            # PDF Download Button
            client_details = clients_df[clients_df["client_id"] == quote_details['client_id']].iloc[0]
            pdf_bytes = create_quote_pdf(quote_details, client_details, items)

            cols[1].download_button(
                label="📄 Generar PDF",
                data=pdf_bytes,
                file_name=f"Cotizacion_{selected_quote_id}_{client_details['name']}.pdf",
                mime="application/pdf",
                key=f"pdf_{selected_quote_id}"
            )

            # Delete Button
            if cols[3].button("❌ Eliminar", key=f"delete_{selected_quote_id}"):
                st.session_state.confirm_delete = True
                st.session_state.quote_to_delete = selected_quote_id

            if 'confirm_delete' in st.session_state and st.session_state.confirm_delete:
                if st.session_state.quote_to_delete == selected_quote_id:
                    st.warning(f"**¿Estás seguro de que quieres eliminar la cotización #{selected_quote_id}?** Esta acción no se puede deshacer.")
                    if st.button("SÍ, ELIMINAR DEFINITIVAMENTE", type="primary"):
                        # Delete from quotes.csv
                        quotes_df_new = quotes_df[quotes_df["quote_id"] != selected_quote_id]
                        save_data(quotes_df_new, "data/quotes.csv")

                        # Delete from quote_items.csv
                        quote_items_df_new = quote_items_df[quote_items_df["quote_id"] != selected_quote_id]
                        save_data(quote_items_df_new, "data/quote_items.csv")

                        st.success(f"Cotización #{selected_quote_id} eliminada.")
                        del st.session_state.confirm_delete
                        del st.session_state.quote_to_delete
                        st.rerun()
                    if st.button("CANCELAR"):
                        del st.session_state.confirm_delete
                        del st.session_state.quote_to_delete
                        st.rerun()

    else:
        st.info("No hay cotizaciones que coincidan con los filtros seleccionados.")
