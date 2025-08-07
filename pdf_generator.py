from fpdf import FPDF
import data_manager
import io
import requests

class PDF(FPDF):
    def header(self):
        config = data_manager.load_config()
        company_name = config.get("company_name", "Tu Empresa")
        address = config.get("address", "Tu Dirección")
        phone = config.get("phone", "Tu Teléfono")
        tax_id = config.get("tax_id", "")
        logo_url = config.get("logo_url", "")

        # --- Logo ---
        if logo_url:
            try:
                response = requests.get(logo_url, timeout=5)
                response.raise_for_status()
                image_bytes = io.BytesIO(response.content)
                self.image(image_bytes, x=10, y=8, w=40)
                self.set_x(55)
            except Exception as e:
                print(f"Warning: Could not load logo. Error: {e}")
                self.set_x(10)
        else:
            self.set_x(10)

        # --- Company Info ---
        self.set_font('Arial', 'B', 16)
        self.cell(0, 8, company_name, 0, 1, 'L')
        self.set_x(self.get_x() if not logo_url else 55)
        self.set_font('Arial', '', 10)
        self.cell(0, 6, address, 0, 1, 'L')
        self.set_x(self.get_x() if not logo_url else 55)
        self.cell(0, 6, f"Tel: {phone}", 0, 1, 'L')
        if tax_id:
            self.set_x(self.get_x() if not logo_url else 55)
            self.cell(0, 6, f"ID Fiscal: {tax_id}", 0, 1, 'L')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def create_quote_pdf(quote_details, client_details, items_df):
    pdf = PDF()
    pdf.add_page()

    # --- Quote Header ---
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, f"Cotización #{quote_details['quote_id']}", 0, 1, 'R')
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f"Fecha: {quote_details['quote_date']}", 0, 1, 'R')
    pdf.ln(5)

    # --- Client Details ---
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(40, 7, "Cliente:", 0, 0)
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 7, client_details['name'], 0, 1)
    if client_details.get('company'):
        pdf.cell(40, 7, "Empresa:", 0, 0)
        pdf.cell(0, 7, client_details['company'], 0, 1)
    pdf.ln(10)

    # --- Items Table Header ---
    pdf.set_font('Arial', 'B', 11)
    pdf.set_fill_color(220, 220, 220)
    pdf.set_text_color(0)
    col_widths = [85, 25, 30, 25, 25]
    headers = ['Descripción', 'Cantidad', 'P. Unitario', 'Dto. (%)', 'Total']
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 10, header, 1, 0, 'C', fill=True)
    pdf.ln()

    # --- Items Table Rows ---
    pdf.set_font('Arial', '', 10)
    pdf.set_fill_color(245, 245, 245)
    fill = False
    subtotal = 0
    for _, item in items_df.iterrows():
        discount_percent = item.get('discount_percent', 0) or 0
        total_item = item['quantity'] * item['unit_price'] * (1 - discount_percent / 100)
        subtotal += total_item

        pdf.cell(col_widths[0], 10, str(item['description']), 1, 0, 'L', fill)
        pdf.cell(col_widths[1], 10, str(item['quantity']), 1, 0, 'C', fill)
        pdf.cell(col_widths[2], 10, f"${item['unit_price']:,.2f}", 1, 0, 'R', fill)
        pdf.cell(col_widths[3], 10, f"{discount_percent}%", 1, 0, 'C', fill)
        pdf.cell(col_widths[4], 10, f"${total_item:,.2f}", 1, 0, 'R', fill)
        pdf.ln()
        fill = not fill

    # --- Totals Section ---
    pdf.ln(10)
    overall_discount = quote_details.get('discount', 0)
    total = quote_details.get('total_amount', 0)
    iva = total - subtotal + overall_discount

    totals_data = [
        ("Subtotal:", f"${subtotal:,.2f}"),
        ("Descuento General:", f"-${overall_discount:,.2f}"),
        ("IVA (16%):", f"${iva:,.2f}"),
        ("Total:", f"${total:,.2f}")
    ]

    for label, value in totals_data:
        pdf.set_font('Arial', 'B' if label == "Total:" else '', 12)
        pdf.cell(130, 8, label, 0, 0, 'R')
        pdf.cell(60, 8, value, 0, 1, 'R')

    # --- Notes, Payment Method, Bank Details ---
    pdf.ln(10)
    config = data_manager.load_config()
    bank_details = config.get("bank_details", "")

    if quote_details.get('notes'):
        pdf.set_font('Arial', 'B', 10); pdf.cell(0, 10, "Notas Adicionales:", 0, 1); pdf.set_font('Arial', '', 10); pdf.multi_cell(0, 7, str(quote_details['notes']))
    if quote_details.get('payment_method'):
        pdf.set_font('Arial', 'B', 10); pdf.cell(0, 10, "Forma de Pago:", 0, 1); pdf.set_font('Arial', '', 10); pdf.multi_cell(0, 7, str(quote_details['payment_method']))
    if bank_details:
        pdf.set_font('Arial', 'B', 10); pdf.cell(0, 10, "Datos para Transferencia:", 0, 1); pdf.set_font('Arial', '', 10); pdf.multi_cell(0, 7, bank_details)

    return pdf.output(dest='S').encode('latin-1')
