"""
Página de Configuración de la Aplicación.

Esta página permite al usuario configurar los datos de su empresa,
que se utilizarán en otras partes de la aplicación, principalmente
en la generación de documentos PDF.

Los datos se guardan en `config.json`.
"""
import streamlit as st
import data_manager

# --- Page Configuration ---
st.set_page_config(page_title="Configuración", page_icon="⚙️", layout="wide")
st.title("⚙️ Configuración de la Empresa")
st.markdown("Aquí puedes configurar los datos de tu empresa que aparecerán en las cotizaciones en PDF.")
st.markdown("---")

# --- Load existing config ---
config = data_manager.load_config()

# --- UI for Configuration ---
# Se utilizan contenedores para agrupar lógicamente los campos.
with st.container(border=True):
    st.subheader("Información de la Empresa")
    company_name = st.text_input("Nombre de la Empresa", value=config.get("company_name", ""))
    address = st.text_input("Dirección", value=config.get("address", ""))
    phone = st.text_input("Teléfono / Contacto", value=config.get("phone", ""))
    tax_id = st.text_input("ID Fiscal (RFC, NIF, etc.)", value=config.get("tax_id", ""))

with st.container(border=True):
    st.subheader("Logo y Datos Bancarios")
    logo_url = st.text_input(
        "URL del Logo (Opcional)",
        value=config.get("logo_url", ""),
        help="Pega aquí un enlace directo a una imagen (ej. https://.../logo.png)"
    )
    if logo_url:
        st.image(logo_url, width=200)

    bank_details = st.text_area(
        "Información de Pago (Opcional)",
        value=config.get("bank_details", ""),
        help="Escribe aquí tus datos bancarios para transferencias. Aparecerán en el PDF."
    )

# --- Save Button ---
if st.button("💾 Guardar Configuración", type="primary", use_container_width=True):
    # Se recogen todos los valores y se guardan en el archivo de configuración.
    new_config = {
        "company_name": company_name,
        "address": address,
        "phone": phone,
        "tax_id": tax_id,
        "logo_url": logo_url,
        "bank_details": bank_details
    }
    data_manager.save_config(new_config)
    st.success("¡Configuración guardada con éxito!")
    st.balloons()
