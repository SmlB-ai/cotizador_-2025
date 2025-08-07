import pandas as pd
import json
import os
from typing import Dict, List, Any

# --- Constants ---
DATA_DIR = "data"
CONFIG_FILE = "config.json"
CLIENTS_FILE = os.path.join(DATA_DIR, "clients.csv")
QUOTES_FILE = os.path.join(DATA_DIR, "quotes.csv")
ITEMS_FILE = os.path.join(DATA_DIR, "quote_items.csv")

CLIENT_COLUMNS = ["client_id", "name", "company", "phone", "email"]
QUOTE_COLUMNS = ["quote_id", "client_id", "quote_date", "total_amount", "discount", "notes", "status", "payment_method"]
ITEM_COLUMNS = ["item_id", "quote_id", "description", "quantity", "unit_price", "discount_percent"]

# --- Private Helper Functions ---
def _load_csv(file_path: str, columns: List[str]) -> pd.DataFrame:
    """A private helper to load any CSV file, creating it if it doesn't exist."""
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        # Create empty dataframe and save it to create the file with headers
        df = pd.DataFrame(columns=columns)
        df.to_csv(file_path, index=False)
        return df
    try:
        return pd.read_csv(file_path)
    except (pd.errors.EmptyDataError, ValueError):
        return pd.DataFrame(columns=columns)

def _save_csv(df: pd.DataFrame, file_path: str):
    """A private helper to save any DataFrame to a CSV file."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    df.to_csv(file_path, index=False)

# --- Public Configuration Functions ---
def load_config() -> Dict[str, Any]:
    """Loads configuration from config.json."""
    if not os.path.exists(CONFIG_FILE):
        # Create a default config if it doesn't exist
        default_config = {
            "company_name": "Tu Empresa Constructora",
            "address": "Calle Falsa 123, Ciudad",
            "phone": "+1 234 567 890",
            "logo_url": "",
            "tax_id": "",
            "bank_details": ""
        }
        save_config(default_config)
        return default_config
    with open(CONFIG_FILE, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_config(config_data: Dict[str, Any]):
    """Saves configuration to config.json."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config_data, f, indent=4)

# --- Public Data Interface Functions ---
def load_clients() -> pd.DataFrame:
    """Loads client data, adding a sample if the file is empty."""
    clients_df = _load_csv(CLIENTS_FILE, CLIENT_COLUMNS)
    if clients_df.empty:
        sample_client = pd.DataFrame([{
            "client_id": 1,
            "name": "Cliente de Ejemplo",
            "company": "Constructora XYZ",
            "phone": "555-123-4567",
            "email": "ejemplo@email.com"
        }])
        clients_df = pd.concat([clients_df, sample_client], ignore_index=True)
        save_clients(clients_df)
    return clients_df

def save_clients(df: pd.DataFrame):
    """Saves the clients DataFrame."""
    _save_csv(df, CLIENTS_FILE)

def load_quotes() -> pd.DataFrame:
    """Loads quotes data."""
    return _load_csv(QUOTES_FILE, QUOTE_COLUMNS)

def save_quotes(df: pd.DataFrame):
    """Saves the quotes DataFrame."""
    _save_csv(df, QUOTES_FILE)

def load_quote_items() -> pd.DataFrame:
    """Loads quote items data."""
    return _load_csv(ITEMS_FILE, ITEM_COLUMNS)

def save_quote_items(df: pd.DataFrame):
    """Saves the quote items DataFrame."""
    _save_csv(df, ITEMS_FILE)
