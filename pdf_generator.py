from fpdf import FPDF
import json
import os
import requests
import io

CONFIG_FILE = "config.json"

def load_config():
    """Loads configuration from a JSON file."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

class PDF(FPDF):
    def header(self):
        config = load_config()
        company_name = config.get("company_name", "Tu Empresa")
        address = config.get("address", "Tu Dirección")
        phone = config.get("phone", "Tu Teléfono")
        logo_url = config.get("logo_url", "")

        # --- Logo ---
        if logo_url:
            try:
                response = requests.get(logo_url, timeout=5)
                response.raise_for_status() # Raise an exception for bad status codes

                # Use BytesIO to handle the image in memory
                image_bytes = io.BytesIO(response.content)

                # The name parameter is used by FPDF to determine the image type
                self.image(image_bytes, x=10, y=8, w=33, link=logo_url, type='PNG' if '.png' in logo_url.lower() else 'JPG')

                # Move cursor to the right of the logo
                self.set_x(45)
            except Exception as e:
                # If logo fails, just print a warning and continue without it
                print(f"Warning: Could not load logo from URL. Error: {e}")
                self.set_x(10)
        else:
            self.set_x(10)

        # --- Company Info ---
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, company_name, 0, 1, 'L')
        self.set_x(self.get_x() if not logo_url else 45) # Indent if logo is present
        self.set_font('Arial', '', 10)
        self.cell(0, 7, f'{address} | {phone}', 0, 1, 'L')
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def create_quote_pdf(quote_details, client_details, items_df):
    """
    Generates a PDF for a given quote.
    Returns the PDF content as bytes.
    """
    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Arial', '', 12)

    # --- Quote Header ---
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, f"Cotización #{quote_details['quote_id']}", 0, 1, 'R')
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f"Fecha: {quote_details['quote_date']}", 0, 1, 'R')
    pdf.ln(5)

    # --- Client Details ---
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "Cliente:", 0, 1)
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 7, f"Nombre: {client_details['name']}", 0, 1)
    if 'company' in client_details and client_details['company']:
        pdf.cell(0, 7, f"Empresa: {client_details['company']}", 0, 1)
    if 'email' in client_details and client_details['email']:
        pdf.cell(0, 7, f"Email: {client_details['email']}", 0, 1)
    if 'phone' in client_details and client_details['phone']:
        pdf.cell(0, 7, f"Teléfono: {client_details['phone']}", 0, 1)
    pdf.ln(10)

    # --- Items Table ---
    pdf.set_font('Arial', 'B', 11)
    # Adjust column widths for the new "Dto." column
    col_widths = [85, 25, 30, 25, 25]
    headers = ['Descripción', 'Cantidad', 'P. Unitario', 'Dto. (%)', 'Total']
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 10, header, 1, 0, 'C')
    pdf.ln()

    pdf.set_font('Arial', '', 10)
    subtotal = 0
    for index, item in items_df.iterrows():
        quantity = item['quantity']
        unit_price = item['unit_price']
        total_item = quantity * unit_price
        subtotal += total_item

        pdf.cell(col_widths[0], 10, str(item['description']), 1)
        pdf.cell(col_widths[1], 10, str(quantity), 1, 0, 'C')
        pdf.cell(col_widths[2], 10, f"${unit_price:,.2f}", 1, 0, 'R')
        pdf.cell(col_widths[3], 10, f"${total_item:,.2f}", 1, 0, 'R')
        pdf.ln()

    # --- Totals ---
    pdf.ln(10)

    discount = quote_details.get('discount', 0)
    total = quote_details.get('total_amount', 0)
    iva = total - subtotal + discount

    total_items = [
        ("Subtotal:", f"${subtotal:,.2f}"),
        ("Descuento:", f"-${discount:,.2f}"),
        ("IVA:", f"${iva:,.2f}"),
        ("Total:", f"${total:,.2f}")
    ]

    pdf.set_font('Arial', 'B', 12)
    for label, value in total_items:
        pdf.cell(130, 8, label, 0, 0, 'R')
        pdf.cell(60, 8, value, 0, 1, 'R')

    # --- Notes & Payment Method ---
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "Notas Adicionales:", 0, 1)
    pdf.set_font('Arial', '', 12)
    pdf.multi_cell(0, 10, str(quote_details.get('notes', '')))

    if 'payment_method' in quote_details and quote_details['payment_method']:
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, "Forma de Pago:", 0, 1)
        pdf.set_font('Arial', '', 12)
        pdf.multi_cell(0, 10, str(quote_details['payment_method']))

    # Return PDF as bytes
    return pdf.output(dest='S').encode('latin-1')
