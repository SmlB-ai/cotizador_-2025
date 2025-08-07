import streamlit as st
import pandas as pd
import os

# --- Page Configuration ---
st.set_page_config(page_title="Clientes", page_icon="👥")

st.title("👥 Gestión de Clientes")

# --- Data Loading ---
DATA_FILE = "data/clients.csv"

def load_data():
    """Loads client data from the CSV file."""
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            if df.empty:
                # If file is empty, create it with headers
                df = pd.DataFrame(columns=["client_id", "name", "company", "phone", "email"])
        except pd.errors.EmptyDataError:
             df = pd.DataFrame(columns=["client_id", "name", "company", "phone", "email"])
    else:
        # If file doesn't exist, create it with headers
        df = pd.DataFrame(columns=["client_id", "name", "company", "phone", "email"])
        df.to_csv(DATA_FILE, index=False)
    return df

clients_df = load_data()

# --- Display Existing Clients ---
st.header("Lista de Clientes")
if not clients_df.empty:
    st.dataframe(clients_df, use_container_width=True)
else:
    st.info("No hay clientes registrados todavía. Agrega uno usando el formulario de abajo.")

# --- Add New Client Form ---
st.header("Agregar Nuevo Cliente")

with st.form("new_client_form", clear_on_submit=True):
    name = st.text_input("Nombre Completo*", help="Nombre y apellido del cliente.")
    company = st.text_input("Empresa (Opcional)")
    phone = st.text_input("Teléfono (Opcional)")
    email = st.text_input("Email (Opcional)")

    submitted = st.form_submit_button("Agregar Cliente")

    if submitted:
        if not name:
            st.warning("El campo 'Nombre Completo' es obligatorio.")
        else:
            # Generate new client_id
            if clients_df.empty or 'client_id' not in clients_df.columns or clients_df['client_id'].isnull().all():
                 new_id = 1
            else:
                 new_id = clients_df["client_id"].max() + 1

            new_client = pd.DataFrame([{
                "client_id": new_id,
                "name": name,
                "company": company,
                "phone": phone,
                "email": email
            }])

            # Append and save
            updated_df = pd.concat([clients_df, new_client], ignore_index=True)
            updated_df.to_csv(DATA_FILE, index=False)

            st.success(f"¡Cliente '{name}' agregado con éxito!")
            # No need for st.rerun() because form submission already triggers a rerun.
            # We can trigger one more if we want to be absolutely sure the table updates.
            st.rerun()
