import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(page_title="Cotizador", page_icon="📝")
st.title("📝 Nueva Cotización")

# --- Data Loading Functions ---
def load_data(file_path, columns):
    """Generic function to load data from a CSV file."""
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        try:
            return pd.read_csv(file_path)
        except (pd.errors.EmptyDataError, ValueError):
            return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

clients_df = load_data("data/clients.csv", ["client_id", "name", "company", "phone", "email"])
quotes_df = load_data("data/quotes.csv", ["quote_id", "client_id", "quote_date", "total_amount", "discount", "notes", "status"])
quote_items_df = load_data("data/quote_items.csv", ["item_id", "quote_id", "description", "quantity", "unit_price"])

# --- Initialize Session State for Quote Items ---
if 'items' not in st.session_state:
    st.session_state.items = pd.DataFrame(columns=["Descripción", "Cantidad", "Precio Unitario"])

# --- UI for Quote Creation ---
if clients_df.empty:
    st.warning("No hay clientes registrados. Por favor, agregue un cliente en la página de 'Clientes' antes de crear una cotización.")
    st.stop()

st.header("Detalles de la Cotización")

# --- Client and Date Selection (Outside Form) ---
col1, col2 = st.columns(2)
with col1:
    client_list = [f"{row['name']} ({row.get('company', 'N/A')})" for index, row in clients_df.iterrows()]
    selected_client_str = st.selectbox("Seleccionar Cliente*", client_list, index=None, placeholder="Elige un cliente...")
with col2:
    quote_date = st.date_input("Fecha de Cotización", datetime.now())

st.header("Conceptos")

# --- Interactive Data Editor for Quote Items (Outside Form) ---
# Use a copy to prevent direct mutation issues with data_editor
items_df = st.session_state.items.copy()

edited_items = st.data_editor(
    items_df,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Descripción": st.column_config.TextColumn(required=True),
        "Cantidad": st.column_config.NumberColumn(required=True, min_value=0.01, format="%.2f"),
        "Precio Unitario": st.column_config.NumberColumn(required=True, min_value=0.0, format="$%.2f"),
    },
    key="data_editor"
)

# --- Update session state with the edited data ---
st.session_state.items = edited_items

# --- Calculate and Display Totals (Outside Form) ---
st.session_state.items['Total'] = st.session_state.items['Cantidad'] * st.session_state.items['Precio Unitario']
subtotal = st.session_state.items['Total'].sum()

st.header("Resumen y Opciones Finales")

with st.form("quote_form"):
    col3, col4 = st.columns(2)
    with col3:
        apply_iva = st.checkbox("Aplicar IVA (16%)", value=True)
        discount = st.number_input("Descuento ($)", min_value=0.0, value=0.0, format="%.2f")
    with col4:
        notes = st.text_area("Notas Adicionales", "Vigencia de la cotización: 15 días.")

    # --- Final Calculations ---
    iva = subtotal * 0.16 if apply_iva else 0
    total = subtotal + iva - discount

    # --- Display Totals in Form ---
    st.metric("Subtotal", f"${subtotal:,.2f}")
    st.metric("IVA (16%)", f"${iva:,.2f}")
    st.metric("Total Final", f"${total:,.2f}")

    # --- Form Submission ---
    submitted = st.form_submit_button("Guardar Cotización", type="primary")
    if submitted:
        # --- Validation ---
        if not selected_client_str:
            st.error("Error: Debes seleccionar un cliente.")
        elif st.session_state.items.empty or st.session_state.items["Descripción"].isnull().all():
            st.error("Error: Debes agregar al menos un concepto a la cotización.")
        else:
            # --- Save Logic ---
            client_row = clients_df[clients_df.apply(lambda row: f"{row['name']} ({row.get('company', 'N/A')})" == selected_client_str, axis=1)]
            client_id = client_row.iloc[0]["client_id"]

            new_quote_id = (quotes_df["quote_id"].max() + 1) if not quotes_df.empty else 1

            new_quote = pd.DataFrame([{
                "quote_id": new_quote_id, "client_id": client_id, "quote_date": quote_date.strftime("%Y-%m-%d"),
                "total_amount": total, "discount": discount, "notes": notes, "status": "Borrador"
            }])
            updated_quotes_df = pd.concat([quotes_df, new_quote], ignore_index=True)
            updated_quotes_df.to_csv("data/quotes.csv", index=False)

            items_to_save = st.session_state.items.copy()
            items_to_save["quote_id"] = new_quote_id
            items_to_save.rename(columns={"Descripción": "description", "Cantidad": "quantity", "Precio Unitario": "unit_price"}, inplace=True)

            last_item_id = (quote_items_df["item_id"].max()) if not quote_items_df.empty else 0
            items_to_save["item_id"] = range(last_item_id + 1, last_item_id + 1 + len(items_to_save))

            updated_items_df = pd.concat([quote_items_df, items_to_save[["item_id", "quote_id", "description", "quantity", "unit_price"]]], ignore_index=True)
            updated_items_df.to_csv("data/quote_items.csv", index=False)

            st.success(f"Cotización #{new_quote_id} guardada como borrador.")

            # Clear items from session state for the next quote
            del st.session_state.items
            st.rerun()
