"""
Página para la Gestión de Clientes (CRUD).

Esta página permite al usuario:
1. Ver una lista de todos los clientes.
2. Agregar un nuevo cliente a través de un formulario en un expander.
3. Editar los datos de los clientes directamente en la tabla interactiva.
4. Seleccionar uno o más clientes para eliminarlos.

Utiliza el `data_manager` para todas las operaciones de carga y guardado.
"""
import streamlit as st
import pandas as pd
import data_manager

# --- Page Configuration ---
st.set_page_config(page_title="Gestión de Clientes", page_icon="👥", layout="wide")
st.title("👥 Gestión de Clientes")

# --- Session State Initialization ---
# Se carga el DataFrame de clientes en el estado de la sesión para persistencia.
if 'clients_df' not in st.session_state:
    st.session_state.clients_df = data_manager.load_clients()

# --- Add New Client Expander ---
# Un expander mantiene la interfaz limpia, mostrando el formulario solo cuando es necesario.
with st.expander("➕ Agregar Nuevo Cliente"):
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
                # Lógica para generar un nuevo ID y agregar el cliente.
                new_id = st.session_state.clients_df["client_id"].max() + 1 if not st.session_state.clients_df.empty else 1
                new_client = pd.DataFrame([{"client_id": new_id, "name": name, "company": company, "phone": phone, "email": email}])
                st.session_state.clients_df = pd.concat([st.session_state.clients_df, new_client], ignore_index=True)
                data_manager.save_clients(st.session_state.clients_df)
                st.success(f"¡Cliente '{name}' agregado con éxito!")

# --- Client Data Editor for Read, Update, Delete ---
st.header("Lista de Clientes")
st.info("Puedes editar los datos directamente en la tabla. Para eliminar, marca la casilla 'Eliminar' y haz clic en el botón correspondiente.")

# Se añade una columna temporal 'Eliminar' solo para la UI.
edited_df = st.session_state.clients_df.copy()
edited_df['Eliminar'] = False

# El data_editor permite la visualización y edición directa.
edited_df = st.data_editor(
    edited_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "client_id": st.column_config.NumberColumn("ID Cliente", disabled=True),
        "name": st.column_config.TextColumn("Nombre", required=True),
        "company": st.column_config.TextColumn("Empresa"),
        "phone": st.column_config.TextColumn("Teléfono"),
        "email": st.column_config.TextColumn("Email"),
        "Eliminar": st.column_config.CheckboxColumn("Eliminar", default=False)
    },
    key="client_editor"
)

# --- Save and Delete Logic ---
col1, col2 = st.columns([0.8, 0.2])

with col1:
    # Se detectan los cambios comparando el DataFrame editado con el original.
    # El botón de guardar solo aparece si hay cambios pendientes.
    if not edited_df.drop('Eliminar', axis=1).equals(st.session_state.clients_df):
        if st.button("💾 Guardar Cambios", type="primary"):
            st.session_state.clients_df = edited_df.drop('Eliminar', axis=1)
            data_manager.save_clients(st.session_state.clients_df)
            st.success("¡Cambios guardados con éxito!")
            st.rerun()

with col2:
    # Se detectan los clientes marcados para eliminar.
    # El botón de eliminar solo aparece si hay clientes seleccionados.
    clients_to_delete = edited_df[edited_df['Eliminar']]
    if not clients_to_delete.empty:
        if st.button("❌ Eliminar Seleccionados"):
            # Se filtran los clientes a eliminar y se guarda el DataFrame resultante.
            st.session_state.clients_df.drop(clients_to_delete.index, inplace=True)
            data_manager.save_clients(st.session_state.clients_df)
            st.success(f"{len(clients_to_delete)} cliente(s) eliminado(s).")
            st.rerun()
