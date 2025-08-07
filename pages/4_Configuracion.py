import streamlit as st
import json
import os

CONFIG_FILE = "config.json"

# --- Configuration Loading and Saving ---
def load_config():
    """Loads configuration from a JSON file."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {} # Return empty dict if file is empty or corrupt
    return {}

def save_config(config_data):
    """Saves configuration to a JSON file."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config_data, f, indent=4)

# --- Page Configuration ---
st.set_page_config(page_title="Configuración", page_icon="⚙️")
st.title("⚙️ Configuración de la Empresa")

st.info("Aquí puedes configurar los datos de tu empresa que aparecerán en las cotizaciones en PDF.")

# Load existing config
config = load_config()

# --- UI for Configuration ---
company_name = st.text_input(
    "Nombre de la Empresa",
    value=config.get("company_name", "Tu Empresa Constructora")
)
address = st.text_input(
    "Dirección",
    value=config.get("address", "Calle Falsa 123, Ciudad")
)
phone = st.text_input(
    "Teléfono / Contacto",
    value=config.get("phone", "+1 234 567 890")
)
logo_url = st.text_input(
    "URL del Logo (Opcional)",
    value=config.get("logo_url", ""),
    help="Pega aquí un enlace directo a una imagen (ej. https://.../logo.png)"
)

if st.button("Guardar Configuración", type="primary"):
    new_config = {
        "company_name": company_name,
        "address": address,
        "phone": phone,
        "logo_url": logo_url
    }
    save_config(new_config)
    st.success("¡Configuración guardada con éxito!")

# --- Preview Section ---
st.header("Vista Previa del Encabezado del PDF")
st.markdown(f"**{company_name}**")
st.markdown(f"{address} | {phone}")
if logo_url:
    st.markdown("**Logo:**")
    st.image(logo_url, width=200)
else:
    st.markdown("_(No se ha proporcionado un logo)_")
