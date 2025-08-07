import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(page_title="Cotizador", page_icon="📝")
st.title("📝 Nueva Cotización")

# --- Data Loading Functions ---
def load_data(file_path, columns):
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        try:
            return pd.read_csv(file_path)
        except (pd.errors.EmptyDataError, ValueError):
            return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

clients_df = load_data("data/clients.csv", ["client_id", "name", "company", "phone", "email"])
quotes_df = load_data("data/quotes.csv", ["quote_id", "client_id", "quote_date", "total_amount", "discount", "notes", "status", "payment_method"])
quote_items_df = load_data("data/quote_items.csv", ["item_id", "quote_id", "description", "quantity", "unit_price", "discount_percent"])

# --- State Initialization ---
if 'items' not in st.session_state or not isinstance(st.session_state.items, pd.DataFrame):
    st.session_state.items = pd.DataFrame(columns=["Descripción", "Cantidad", "Precio Unitario", "Descuento (%)"])

# --- UI ---
if clients_df.empty:
    st.warning("No hay clientes registrados. Por favor, agregue un cliente en la página de 'Clientes' antes de crear una cotización.")
    st.stop()

st.header("Detalles de la Cotización")
col1, col2 = st.columns(2)
selected_client_str = col1.selectbox("Seleccionar Cliente*", [f"{row['name']} ({row.get('company', 'N/A')})" for _, row in clients_df.iterrows()], index=None, placeholder="Elige un cliente...")
quote_date = col2.date_input("Fecha de Cotización", datetime.now())

st.header("Conceptos")

# --- Advanced State Management for Data Editor ---
# 1. Create a local copy of the state
df_copy = st.session_state.items.copy()

# 2. Pass the copy to the editor
edited_df = st.data_editor(
    df_copy,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Descripción": st.column_config.TextColumn(required=True),
        "Cantidad": st.column_config.NumberColumn(required=True, min_value=0.01, format="%.2f"),
        "Precio Unitario": st.column_config.NumberColumn(required=True, min_value=0.0, format="$%.2f"),
        "Descuento (%)": st.column_config.NumberColumn(required=False, min_value=0, max_value=100, default=0, format="%d%%"),
        "Total": st.column_config.NumberColumn(disabled=True, format="$%.2f"),
    },
    key="data_editor"
)

# 3. Compare and update state only if there's a change
if not edited_df.equals(st.session_state.items):
    st.session_state.items = edited_df
    st.rerun()

# --- Calculations (will run on a clean state) ---
current_items = st.session_state.items.copy()
current_items["Descuento (%)"] = current_items["Descuento (%)"].fillna(0)
current_items['Total'] = (
    current_items['Cantidad'].fillna(0) *
    current_items['Precio Unitario'].fillna(0) *
    (1 - current_items['Descuento (%)'].fillna(0) / 100)
)
subtotal = current_items['Total'].sum()

# --- Final Options Form ---
st.header("Resumen y Opciones Finales")
with st.form("quote_form"):
    col3, col4 = st.columns(2)
    with col3:
        apply_iva = st.checkbox("Aplicar IVA (16%)", value=True)
        discount = st.number_input("Descuento General ($)", min_value=0.0, value=0.0, format="%.2f")
        payment_method = st.selectbox("Forma de Pago", ["Transferencia Bancaria", "Efectivo", "Tarjeta de Crédito/Débito", "Otro"], index=0)
    with col4:
        notes = st.text_area("Notas Adicionales", "Vigencia de la cotización: 15 días. Precios sujetos a cambio sin previo aviso.")

    iva = subtotal * 0.16 if apply_iva else 0
    total = subtotal + iva - discount

    st.metric("Subtotal", f"${subtotal:,.2f}")
    st.metric("IVA (16%)", f"${iva:,.2f}")
    st.metric("Total Final", f"${total:,.2f}")

    submitted = st.form_submit_button("Guardar Cotización", type="primary")
    if submitted:
        if not selected_client_str:
            st.error("Error: Debes seleccionar un cliente.")
        elif current_items.empty or current_items["Descripción"].isnull().all():
            st.error("Error: Debes agregar al menos un concepto a la cotización.")
        else:
            client_row = clients_df[clients_df.apply(lambda row: f"{row['name']} ({row.get('company', 'N/A')})" == selected_client_str, axis=1)]
            client_id = client_row.iloc[0]["client_id"]

            new_quote_id = (quotes_df["quote_id"].max() + 1) if not quotes_df.empty else 1

            new_quote = pd.DataFrame([{"quote_id": new_quote_id, "client_id": client_id, "quote_date": quote_date.strftime("%Y-%m-%d"), "total_amount": total, "discount": discount, "notes": notes, "status": "Borrador", "payment_method": payment_method}])
            updated_quotes_df = pd.concat([quotes_df, new_quote], ignore_index=True)
            updated_quotes_df.to_csv("data/quotes.csv", index=False)

            items_to_save = current_items.copy()
            items_to_save["quote_id"] = new_quote_id
            items_to_save.rename(columns={"Descripción": "description", "Cantidad": "quantity", "Precio Unitario": "unit_price", "Descuento (%)": "discount_percent"}, inplace=True)

            last_item_id = (quote_items_df["item_id"].max()) if not quote_items_df.empty else 0
            items_to_save["item_id"] = range(last_item_id + 1, last_item_id + 1 + len(items_to_save))

            final_cols = ["item_id", "quote_id", "description", "quantity", "unit_price", "discount_percent"]
            updated_items_df = pd.concat([quote_items_df, items_to_save[final_cols]], ignore_index=True)
            updated_items_df.to_csv("data/quote_items.csv", index=False)

            st.success(f"Cotización #{new_quote_id} guardada como borrador.")
            del st.session_state.items
            st.rerun()
