"""
Página para la creación de nuevas cotizaciones.

Esta página permite al usuario:
1. Seleccionar un cliente y una fecha.
2. Añadir/editar/eliminar conceptos (líneas de producto) en una tabla interactiva.
3. Aplicar descuentos por concepto y un descuento general adicional.
4. Configurar IVA, forma de pago y notas.
5. Visualizar el total calculado en tiempo real.
6. Guardar la cotización, que la almacena como "Borrador".

Utiliza un patrón de estado avanzado para manejar el `data_editor` de forma robusta.
"""
import streamlit as st
import pandas as pd
import data_manager
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(page_title="Nuevo Cotización", page_icon="📝", layout="wide")
st.title("📝 Nueva Cotización")

# --- Data Loading ---
# Carga todos los datos necesarios al inicio usando el data_manager centralizado.
clients_df = data_manager.load_clients()
quotes_df = data_manager.load_quotes()
quote_items_df = data_manager.load_quote_items()

# --- State Initialization ---
# Inicializa el DataFrame de items en el estado de la sesión si no existe.
# Esto es crucial para que la tabla de conceptos persista entre interacciones.
if 'items' not in st.session_state or not isinstance(st.session_state.items, pd.DataFrame):
    st.session_state.items = pd.DataFrame(columns=["Descripción", "Cantidad", "Precio Unitario", "Descuento (%)"])

# --- UI ---
# Si no hay clientes, no se puede crear una cotización.
if clients_df.empty:
    st.warning("No hay clientes registrados. Por favor, agregue un cliente en la página de 'Clientes' antes de crear una cotización.")
    st.stop()

# --- Main Layout ---
# Contenedor para los detalles generales de la cotización.
with st.container(border=True):
    st.subheader("1. Detalles Generales")
    col1, col2 = st.columns(2)
    selected_client_str = col1.selectbox("Seleccionar Cliente*", [f"{row['name']} ({row.get('company', 'N/A')})" for _, row in clients_df.iterrows()], index=None, placeholder="Elige un cliente...")
    quote_date = col2.date_input("Fecha de Cotización", datetime.now())

# Contenedor para la tabla de conceptos.
with st.container(border=True):
    st.subheader("2. Conceptos de la Cotización")

    # --- Advanced State Management for Data Editor ---
    # 1. Se crea una copia local del estado para pasarla al editor.
    df_copy = st.session_state.items.copy()

    # 2. El editor de datos trabaja sobre la copia.
    edited_df = st.data_editor(
        df_copy,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Descripción": st.column_config.TextColumn(required=True, width="large"),
            "Cantidad": st.column_config.NumberColumn(required=True, min_value=0.01, format="%.2f"),
            "Precio Unitario": st.column_config.NumberColumn(required=True, min_value=0.0, format="$%.2f"),
            "Descuento (%)": st.column_config.NumberColumn(required=False, min_value=0, max_value=100, default=0, format="%d%%"),
            "Total": st.column_config.NumberColumn(disabled=True, format="$%.2f", help="Se calcula automáticamente"),
        },
        key="data_editor"
    )

    # 3. Se compara el resultado con el estado original. Si hay cambios,
    # se actualiza el estado y se fuerza una recarga para recalcular todo.
    # Este es el patrón que previene los errores de estado.
    if not edited_df.equals(st.session_state.items):
        st.session_state.items = edited_df
        st.rerun()

# --- Calculations ---
# Se realizan los cálculos en cada ejecución del script sobre el estado ya actualizado.
current_items = st.session_state.items.copy()
current_items["Descuento (%)"] = current_items["Descuento (%)"].fillna(0)
current_items['Total'] = (current_items['Cantidad'].fillna(0) * current_items['Precio Unitario'].fillna(0) * (1 - current_items['Descuento (%)'].fillna(0) / 100))
subtotal = current_items['Total'].sum()

# --- Final Options & Saving Form ---
with st.form("quote_form"):
    st.subheader("3. Resumen y Opciones Finales")

    col3, col4 = st.columns(2)
    with col3:
        apply_iva = st.checkbox("Aplicar IVA (16%)", value=True)
        payment_method = st.selectbox("Forma de Pago", ["Transferencia Bancaria", "Efectivo", "Tarjeta de Crédito/Débito", "Otro"], index=0)
    with col4:
        discount = st.number_input("Descuento General Adicional ($)", min_value=0.0, value=0.0, format="%.2f", help="Este descuento se aplica al subtotal.")

    notes = st.text_area("Notas Adicionales", "Vigencia de la cotización: 15 días. Precios sujetos a cambio sin previo aviso.")

    # Cálculos finales basados en las opciones del formulario.
    iva = subtotal * 0.16 if apply_iva else 0
    total = subtotal + iva - discount

    st.markdown("---")
    total_col1, total_col2, total_col3 = st.columns(3)
    total_col1.metric("Subtotal", f"${subtotal:,.2f}")
    total_col2.metric("IVA (16%)", f"${iva:,.2f}")
    total_col3.metric("Total Final", f"${total:,.2f}")

    # El botón de guardado encapsula toda la lógica de validación y almacenamiento.
    submitted = st.form_submit_button("💾 Guardar Cotización", type="primary", use_container_width=True)
    if submitted:
        # Validación de campos obligatorios.
        if not selected_client_str:
            st.error("Error: Debes seleccionar un cliente.")
        elif current_items.empty or current_items["Descripción"].isnull().all():
            st.error("Error: Debes agregar al menos un concepto a la cotización.")
        else:
            # Lógica de guardado.
            client_id = clients_df[clients_df.apply(lambda row: f"{row['name']} ({row.get('company', 'N/A')})" == selected_client_str, axis=1)].iloc[0]["client_id"]

            quotes_df = data_manager.load_quotes()
            new_quote_id = (quotes_df["quote_id"].max() + 1) if not quotes_df.empty else 1

            new_quote_data = {"quote_id": new_quote_id, "client_id": client_id, "quote_date": quote_date.strftime("%Y-%m-%d"), "total_amount": total, "discount": discount, "notes": notes, "status": "Borrador", "payment_method": payment_method}
            new_quote_df = pd.DataFrame([new_quote_data])
            all_quotes_df = pd.concat([quotes_df, new_quote_df], ignore_index=True)
            data_manager.save_quotes(all_quotes_df)

            items_to_save = current_items.copy()
            items_to_save["quote_id"] = new_quote_id
            items_to_save.rename(columns={"Descripción": "description", "Cantidad": "quantity", "Precio Unitario": "unit_price", "Descuento (%)": "discount_percent"}, inplace=True)

            quote_items_df = data_manager.load_quote_items()
            last_item_id = (quote_items_df["item_id"].max()) if not quote_items_df.empty else 0
            items_to_save["item_id"] = range(last_item_id + 1, last_item_id + 1 + len(items_to_save))

            all_items_df = pd.concat([quote_items_df, items_to_save[data_manager.ITEM_COLUMNS]], ignore_index=True)
            data_manager.save_quote_items(all_items_df)

            st.success(f"Cotización #{new_quote_id} guardada como borrador.")
            # Limpia el estado para la siguiente cotización.
            del st.session_state.items
            st.rerun()
