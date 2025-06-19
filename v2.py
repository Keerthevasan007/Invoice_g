from flask import Flask, render_template_string, request, jsonify, send_from_directory
from datetime import datetime
import os
import traceback
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from io import BytesIO
import psycopg2
from psycopg2 import sql

app = Flask(__name__)
# Replace DB_CONFIG with PostgreSQL config
DB_CONFIG = {
    'dbname': 'neondb',
    'user': 'neondb_owner',
    'password': 'npg_5lEep4WwULJa',
    'host': 'ep-winter-brook-a58n4hja-pooler.us-east-2.aws.neon.tech',
    'port': '5432',
    'sslmode': 'require'
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

# Create static directory if it doesn't exist
if not os.path.exists('static'):
    os.makedirs('static')

# Initialize the DB
def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            id SERIAL PRIMARY KEY,
            invoice_no TEXT,
            invoice_date TEXT,
            patient_name TEXT,
            patient_id TEXT,
            address TEXT,
            treatment TEXT,
            quantity INTEGER,
            unit_price REAL,
            total REAL,
            vat REAL,
            grand_total REAL
        )
    ''')
    conn.commit()
    conn.close()

def generate_invoice_number():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM invoices')
    count = c.fetchone()[0]
    conn.close()
    year = datetime.now().year
    return f"SA-{year}-{count + 1:04d}"

# Invoice template
invoice_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SA Physio Care Invoice</title>
  <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
  <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
  <style>
    :root {
      --primary-color: #76ccd0;
      --secondary-color: #76ccd0;
      --accent-color: #76ccd0;
      --light-bg: #f8fafc;
      --card-bg: #ffffff;
      --text-primary: #1e293b;
      --text-secondary: #64748b;
      --border-color: #e2e8f0;
      --success-color: #10b981;
      --warning-color: #f59e0b;
    }

    * {
      box-sizing: border-box;
    }

    body {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
      min-height: 100vh;
      margin: 0;
      padding: 0;
    }

    .main-container {
      min-height: 100vh;
      padding: 1rem;
      display: flex;
      justify-content: center;
      align-items: flex-start;
    }

    .invoice-card {
      background: var(--card-bg);
      border-radius: 16px;
      box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
      width: 100%;
      max-width: 1200px;
      overflow: hidden;
    }

    .header-section {
      background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
      color: white;
      padding: 2rem;
      position: relative;
      overflow: hidden;
    }

    .header-section::before {
      content: '';
      position: absolute;
      top: 0;
      right: 0;
      width: 200px;
      height: 200px;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 50%;
      transform: translate(50%, -50%);
    }

    .logo-container {
      display: flex;
      align-items: center;
      gap: 1rem;
      margin-bottom: 1rem;
    }

    .logo {
      width: 80px;
      height: 80px;
      border-radius: 12px;
      background: rgba(255, 255, 255, 0.2);
      backdrop-filter: blur(10px);
      display: flex;
      align-items: center;
      justify-content: center;
      border: 2px solid rgba(255, 255, 255, 0.3);
    }

    .logo img {
      width: 60px;
      height: 60px;
      object-fit: contain;
      border-radius: 8px;
    }

    .logo-fallback {
      font-size: 24px;
      font-weight: bold;
      color: white;
    }

    .company-info h1 {
      font-size: 2rem;
      font-weight: 800;
      margin: 0;
      letter-spacing: -0.025em;
    }

    .company-tagline {
      font-size: 0.875rem;
      opacity: 0.9;
      font-style: italic;
      margin: 0.25rem 0 1rem 0;
    }

    .contact-info {
      font-size: 0.875rem;
      line-height: 1.6;
      opacity: 0.95;
    }

    .invoice-title {
      position: absolute;
      top: 2rem;
      right: 2rem;
      text-align: right;
    }

    .invoice-title h2 {
      font-size: 2.5rem;
      font-weight: 900;
      margin: 0;
      text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    .content-section {
      padding: 2rem;
    }

    .form-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 2rem;
      margin-bottom: 2rem;
    }

    .form-group {
      background: var(--light-bg);
      padding: 1.5rem;
      border-radius: 12px;
      border: 1px solid var(--border-color);
    }

    .form-group h3 {
      color: var(--text-primary);
      font-size: 1.125rem;
      font-weight: 600;
      margin: 0 0 1rem 0;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .input-group {
      margin-bottom: 1rem;
    }

    .input-group:last-child {
      margin-bottom: 0;
    }

    .input-label {
      display: block;
      font-size: 0.875rem;
      font-weight: 500;
      color: var(--text-secondary);
      margin-bottom: 0.5rem;
    }

    .input-field {
      width: 100%;
      padding: 0.75rem 1rem;
      border: 2px solid var(--border-color);
      border-radius: 8px;
      font-size: 0.875rem;
      transition: all 0.2s ease;
      background: white;
    }

    .input-field:focus {
      outline: none;
      border-color: var(--primary-color);
      box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
    }

    .invoice-details {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 1rem;
      margin-bottom: 2rem;
    }

    .detail-item {
      text-align: center;
      padding: 1rem;
      background: var(--light-bg);
      border-radius: 8px;
      border: 1px solid var(--border-color);
    }

    .detail-item label {
      display: block;
      font-size: 0.75rem;
      font-weight: 500;
      color: var(--text-secondary);
      margin-bottom: 0.5rem;
    }

    .items-section {
      margin: 2rem 0;
    }

    .items-section h3 {
      color: var(--text-primary);
      font-size: 1.125rem;
      font-weight: 600;
      margin: 0 0 1rem 0;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .items-table {
      width: 100%;
      border-collapse: collapse;
      background: white;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }

    .items-table thead {
      background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
      color: white;
    }

    .items-table th,
    .items-table td {
      padding: 1rem;
      text-align: left;
      border-bottom: 1px solid var(--border-color);
    }

    .items-table th {
      font-weight: 600;
      font-size: 0.875rem;
    }

    .items-table tbody tr:hover {
      background: var(--light-bg);
    }

    .items-table input {
      border: none;
      background: transparent;
      width: 100%;
      padding: 0.5rem;
      font-size: 0.875rem;
    }

    .items-table input:focus {
      outline: 2px solid var(--primary-color);
      border-radius: 4px;
      background: white;
    }

    .add-row-btn {
      margin-top: 1rem;
      padding: 0.75rem 1.5rem;
      background: var(--accent-color);
      color: white;
      border: none;
      border-radius: 8px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s ease;
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
    }

    .add-row-btn:hover {
      background: #0891b2;
      transform: translateY(-1px);
    }

    .bottom-section {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 2rem;
      margin-top: 2rem;
    }

    .notes-section textarea {
      width: 100%;
      height: 120px;
      padding: 1rem;
      border: 2px solid var(--border-color);
      border-radius: 8px;
      resize: vertical;
      font-family: inherit;
      font-size: 0.875rem;
    }

    .totals-section {
      background: var(--light-bg);
      padding: 1.5rem;
      border-radius: 12px;
      border: 1px solid var(--border-color);
      min-width: 300px;
    }

    .total-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.75rem;
      font-size: 0.875rem;
    }

    .total-row:last-child {
      margin-bottom: 0;
      font-size: 1.125rem;
      font-weight: 600;
      color: var(--primary-color);
      padding-top: 0.75rem;
      border-top: 2px solid var(--border-color);
    }

    .action-buttons {
      display: flex;
      gap: 1rem;
      justify-content: center;
      margin-top: 2rem;
      padding-top: 2rem;
      border-top: 1px solid var(--border-color);
    }

    .btn {
      padding: 0.875rem 2rem;
      border: none;
      border-radius: 8px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      font-size: 0.875rem;
    }

    .btn-primary {
      background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
      color: white;
    }

    .btn-primary:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
    }

    .btn-success {
      background: var(--success-color);
      color: white;
    }

    .btn-success:hover {
      background: #059669;
      transform: translateY(-2px);
    }

    .btn-warning {
      background: var(--warning-color);
      color: white;
    }

    .btn-warning:hover {
      background: #d97706;
      transform: translateY(-2px);
    }

    /* Print Styles */
    @media print {
      @page {
        size: A4;
        margin: 15mm;
      }
      
      body {
        background: white !important;
        margin: 0;
        padding: 0;
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
        font-size: 12px;
      }
    
      .main-container {
        padding: 0;
        min-height: auto;
        display: block;
        max-width: 210mm;
        margin: 0 auto;
      }
    
      .invoice-card {
        box-shadow: none;
        border-radius: 0;
        max-width: none;
        margin: 0;
        page-break-inside: avoid;
        page-break-after: avoid;
      }
    
      .header-section {
        padding: 15mm 0;
        margin-bottom: 10mm;
      }
    
      .logo-container {
        margin-bottom: 5mm;
      }
    
      .logo {
        width: 60px;
        height: 60px;
      }
    
      .company-info h1 {
        font-size: 24px;
        margin-bottom: 2mm;
      }
    
      .company-tagline {
        font-size: 12px;
        margin-bottom: 3mm;
      }
    
      .contact-info {
        font-size: 10px;
        line-height: 1.4;
      }
    
      .invoice-title {
        position: absolute;
        top: 15mm;
        right: 0;
      }
    
      .content-section {
        padding: 0;
      }
    
      .invoice-details {
        margin-bottom: 10mm;
      }
    
      .form-grid {
        gap: 10mm;
        margin-bottom: 10mm;
      }
    
      .form-group {
        padding: 5mm;
      }
    
      .items-table {
        margin-bottom: 10mm;
        font-size: 11px;
      }
    
      .items-table th,
      .items-table td {
        padding: 3mm;
      }
    
      .bottom-section {
        gap: 10mm;
        margin-top: 10mm;
      }
    
      .notes-section textarea {
        height: 60px;
        font-size: 10px;
      }
    
      .totals-section {
        padding: 5mm;
        min-width: 80mm;
      }
    
      .total-row {
        font-size: 11px;
        margin-bottom: 2mm;
      }
    
      .total-row:last-child {
        font-size: 14px;
        padding-top: 3mm;
      }
    
      .action-buttons,
      .add-row-btn {
        display: none !important;
      }
    
      input, textarea, select {
        border: none !important;
        padding: 0 !important;
        font-size: inherit;
      }
    }

    /* Mobile Responsive */
    @media (max-width: 768px) {
      .main-container {
        padding: 0.5rem;
      }

      .header-section {
        padding: 1.5rem;
      }

      .content-section {
        padding: 1rem;
      }

      .form-grid {
        grid-template-columns: 1fr;
        gap: 1rem;
      }

      .invoice-details {
        grid-template-columns: 1fr;
      }

      .bottom-section {
        grid-template-columns: 1fr;
      }

      .totals-section {
        min-width: auto;
      }

      .action-buttons {
        flex-direction: column;
      }

      .invoice-title {
        position: static;
        text-align: left;
        margin-top: 1rem;
      }

      .invoice-title h2 {
        font-size: 2rem;
      }
    }
  </style>
</head>
<body>
  <div class="main-container">
    <div class="invoice-card" id="invoice">
      <!-- Header Section -->
      <div class="header-section">
        <div class="logo-container">
          <div class="logo">
            <img src="/static/sa_logo.png" alt="SA Physio Care Logo" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
            <div class="logo-fallback" style="display: none;">SA</div>
          </div>
          <div class="company-info">
            <h1>SA PHYSIO CARE</h1>
            <p class="company-tagline">RESTORE. RELIEVE. REVITALISE.</p>
            <div class="contact-info">
              <div><strong>Suvarna Avilala</strong> - Specialist Physiotherapist</div>
              <div><i class="fas fa-phone"></i> 01296 580770 / 07438 326185</div>
              <div><i class="fas fa-envelope"></i> info@saphysiocare.co.uk</div>
              <div><i class="fas fa-map-marker-alt"></i> 51 Savernake Road, Aylesbury, Buckinghamshire, HP19 9XP</div>
            </div>
          </div>
        </div>
        
        <div class="invoice-title">
          <h2>INVOICE</h2>
        </div>
      </div>

      <!-- Content Section -->
      <div class="content-section">
        <!-- Invoice Details -->
        <div class="invoice-details">
          <div class="detail-item">
            <label>Invoice Number</label>
            <input id="invoice-no" type="text" class="input-field" value="{{ invoice_no }}" readonly>
          </div>
          <div class="detail-item">
            <label>Invoice Date</label>
            <input type="date" id="invoice-date" class="input-field">
          </div>
          <div class="detail-item">
            <label>Due Date</label>
            <input type="date" id="due-date" class="input-field">
          </div>
        </div>

        <!-- Patient and Treatment Info -->
        <div class="form-grid">
          <div class="form-group">
            <h3><i class="fas fa-user-injured"></i> Patient Information</h3>
            <div class="input-group">
              <label class="input-label">Patient Name</label>
              <input id="patient-name" type="text" class="input-field" placeholder="Enter patient full name">
            </div>
            <div class="input-group">
              <label class="input-label">Patient ID / NHS Number</label>
              <input id="patient-id" type="text" class="input-field" placeholder="Enter patient ID or NHS number">
            </div>
            <div class="input-group">
              <label class="input-label">Address</label>
              <textarea id="patient-address" class="input-field" rows="3" placeholder="Enter patient address"></textarea>
            </div>
          </div>
          
          <div class="form-group">
            <h3><i class="fas fa-stethoscope"></i> Treatment Category</h3>
            <div class="input-group">
              <label class="input-label">Primary Treatment</label>
              <select id="treatment-category" class="input-field">
                <option>Manual Therapy</option>
                <option>Sports Rehabilitation</option>
                <option>Postural Correction</option>
                <option>Electrotherapy</option>
                <option>Exercise Therapy</option>
                <option>Massage Therapy</option>
                <option>Custom Treatment</option>
              </select>
            </div>
            <div class="input-group">
              <label class="input-label">Internal Reference</label>
              <input type="text" class="input-field" placeholder="Reference number or notes">
            </div>
            <div class="input-group">
              <label class="input-label">Treatment Notes</label>
              <textarea class="input-field" rows="2" placeholder="Additional treatment information"></textarea>
            </div>
          </div>
        </div>

        <!-- Items Table -->
        <div class="items-section">
          <h3><i class="fas fa-list-ul"></i> Treatment Details</h3>
          <table class="items-table">
            <thead>
              <tr>
                <th style="width: 50%;">Treatment Description</th>
                <th style="width: 10%;">Qty</th>
                <th style="width: 20%;">Unit Price (£)</th>
                <th style="width: 20%;">Total (£)</th>
              </tr>
            </thead>
            <tbody id="item-rows">
              <tr>
                <td><input type="text" class="treatment" placeholder="Enter detailed treatment description"></td>
                <td><input type="number" class="qty" value="1" min="1"></td>
                <td><input type="number" class="price" value="0.00" step="0.01" min="0"></td>
                <td class="total font-semibold">0.00</td>
              </tr>
            </tbody>
          </table>
          <button class="add-row-btn" onclick="addRow()">
            <i class="fas fa-plus"></i> Add Treatment Item
          </button>
        </div>

        <!-- Bottom Section -->
        <div class="bottom-section">
          <div class="notes-section">
            <h3><i class="fas fa-sticky-note"></i> Notes & Terms</h3>
            <textarea id="invoice-notes" placeholder="Payment terms, follow-up instructions, or additional notes..."></textarea>
          </div>
          
          <div class="totals-section">
            <div class="total-row">
              <span>Subtotal:</span>
              <span>£<span id="subtotal">0.00</span></span>
            </div>
            <div class="total-row">
              <span>VAT (20%):</span>
              <span>£<span id="vat">0.00</span></span>
            </div>
            <div class="total-row">
              <span>Total Amount Due:</span>
              <span>£<span id="grand">0.00</span></span>
            </div>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="action-buttons">
          <button onclick="saveInvoice()" class="btn btn-success">
            <i class="fas fa-save"></i> Save Invoice
          </button>
          <button onclick="generatePDF()" class="btn btn-primary">
            <i class="fas fa-file-pdf"></i> Download PDF
          </button>
          <button onclick="printInvoice()" class="btn btn-warning">
            <i class="fas fa-print"></i> Print Invoice
          </button>
        </div>
      </div>
    </div>
  </div>

  <script>
    function addRow() {
      const tbody = document.getElementById('item-rows');
      const row = document.createElement('tr');
      row.innerHTML = `
        <td><input type="text" class="treatment" placeholder="Enter detailed treatment description"></td>
        <td><input type="number" class="qty" value="1" min="1"></td>
        <td><input type="number" class="price" value="0.00" step="0.01" min="0"></td>
        <td class="total font-semibold">0.00</td>
      `;
      tbody.appendChild(row);
      bindInputEvents();
    }

    function bindInputEvents() {
      document.querySelectorAll('.qty, .price').forEach(input => {
        input.addEventListener('input', updateTotals);
      });
    }

    function updateTotals() {
      let subtotal = 0;
      document.querySelectorAll('#item-rows tr').forEach(row => {
        const qtyInput = row.querySelector('.qty');
        const priceInput = row.querySelector('.price');
        const totalCell = row.querySelector('.total');
        
        if (qtyInput && priceInput && totalCell) {
          const qty = parseFloat(qtyInput.value || 0);
          const price = parseFloat(priceInput.value || 0);
          const total = qty * price;
          totalCell.textContent = total.toFixed(2);
          subtotal += total;
        }
      });
      
      const vatAmount = subtotal * 0.20;
      const grandTotal = subtotal + vatAmount;
      
      document.getElementById('subtotal').textContent = subtotal.toFixed(2);
      document.getElementById('vat').textContent = vatAmount.toFixed(2);
      document.getElementById('grand').textContent = grandTotal.toFixed(2);
    }

    function printInvoice() {
      window.print();
    }

    function generatePDF() {
        const pdfButton = document.querySelector('.btn-primary');
        const originalText = pdfButton.innerHTML;
        pdfButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating PDF...';
        pdfButton.disabled = true;
        
        try {
            const invoiceData = {
                invoice_no: document.getElementById('invoice-no').value,
                invoice_date: document.getElementById('invoice-date').value,
                due_date: document.getElementById('due-date').value,
                patient_name: document.getElementById('patient-name').value,
                patient_id: document.getElementById('patient-id').value,
                address: document.getElementById('patient-address').value,
                treatment_category: document.getElementById('treatment-category').value,
                notes: document.getElementById('invoice-notes').value,
                items: [],
                subtotal: parseFloat(document.getElementById('subtotal').textContent) || 0,
                vat: parseFloat(document.getElementById('vat').textContent) || 0,
                grand_total: parseFloat(document.getElementById('grand').textContent) || 0
            };

            document.querySelectorAll('#item-rows tr').forEach(row => {
                const treatment = row.querySelector('.treatment').value;
                const qty = row.querySelector('.qty').value;
                const price = row.querySelector('.price').value;
                const total = row.querySelector('.total').textContent;
                
                if (treatment.trim()) {
                    invoiceData.items.push({
                        treatment: treatment,
                        quantity: parseInt(qty) || 1,
                        unit_price: parseFloat(price) || 0,
                        total: parseFloat(total) || 0
                    });
                }
            });

            if (invoiceData.items.length === 0) {
                alert("Please add at least one treatment item before generating PDF.");
                throw new Error("No items in invoice");
            }
            
            if (!invoiceData.patient_name.trim()) {
                alert("Please enter patient name before generating PDF.");
                throw new Error("Patient name missing");
            }

            fetch('/generate-pdf', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(invoiceData)
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(err => {
                        throw new Error(err.message || 'PDF generation failed');
                    });
                }
                return response.blob();
            })
            .then(blob => {
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `SA_Physio_Invoice_${invoiceData.invoice_no}.pdf`;
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(url);
            })
            .catch(error => {
                console.error('Error:', error);
                alert('PDF generation failed: ' + error.message);
            })
            .finally(() => {
                pdfButton.innerHTML = originalText;
                pdfButton.disabled = false;
            });
        } catch (error) {
            console.error('Error:', error);
            alert('PDF generation failed: ' + error.message);
            pdfButton.innerHTML = originalText;
            pdfButton.disabled = false;
        }
    }

    function saveInvoice() {
      const rows = document.querySelectorAll('#item-rows tr');
      const items = [];
      
      rows.forEach(row => {
        const treatment = row.querySelector('.treatment');
        const qty = row.querySelector('.qty');
        const price = row.querySelector('.price');
        const total = row.querySelector('.total');
        
        if (treatment && qty && price && total && treatment.value.trim()) {
          items.push({
            treatment: treatment.value.trim(),
            quantity: parseInt(qty.value) || 1,
            unit_price: parseFloat(price.value) || 0,
            total: parseFloat(total.textContent) || 0
          });
        }
      });
      
      if (items.length === 0) {
        alert("⚠️ Please add at least one treatment item before saving.");
        return;
      }
      
      const patientName = document.getElementById('patient-name').value.trim();
      if (!patientName) {
        alert("⚠️ Please enter patient name before saving.");
        document.getElementById('patient-name').focus();
        return;
      }
      
      const data = {
        invoice_no: document.getElementById('invoice-no').value,
        invoice_date: document.getElementById('invoice-date').value,
        patient_name: patientName,
        patient_id: document.getElementById('patient-id').value.trim(),
        address: document.getElementById('patient-address').value.trim(),
        items: items,
        vat: parseFloat(document.getElementById('vat').textContent) || 0,
        grand_total: parseFloat(document.getElementById('grand').textContent) || 0
      };
      
      fetch('/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
      .then(response => response.json())
      .then(result => {
        if (result.status === 'success') {
          alert("✅ Invoice saved successfully!");
        } else {
          alert("❌ Error saving invoice: " + (result.message || "Please try again."));
        }
      })
      .catch(error => {
        console.error('Error:', error);
        alert("❌ Error saving invoice. Please check your connection.");
      });
    }

    function updateDueDate() {
      const invoiceDate = document.getElementById('invoice-date').value;
      if (invoiceDate) {
        const dueDate = new Date(invoiceDate);
        dueDate.setDate(dueDate.getDate() + 30);
        document.getElementById('due-date').value = dueDate.toISOString().split('T')[0];
      }
    }

    document.addEventListener("DOMContentLoaded", () => {
      const today = new Date().toISOString().split('T')[0];
      document.getElementById("invoice-date").value = today;
      updateDueDate();
      bindInputEvents();
      document.getElementById('invoice-date').addEventListener('change', updateDueDate);
    });
  </script>
</body>
</html>
'''

# Admin dashboard template
admin_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SA Physio Care - Admin Dashboard</title>
  <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
  <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
  <style>
    :root {
      --primary-color: #76ccd0;
      --secondary-color: #76ccd0;
      --accent-color: #76ccd0;
      --success-color: #10b981;
      --warning-color: #f59e0b;
      --danger-color: #ef4444;
    }
    
    body {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
    }
    
    .stat-card {
      background: white;
      border-radius: 12px;
      padding: 1.5rem;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
      border: 1px solid #e2e8f0;
    }
    
    .stat-card h3 {
      font-size: 2.5rem;
      font-weight: 800;
      margin: 0;
      background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
    
    .stat-card p {
      color: #64748b;
      margin: 0.5rem 0 0 0;
      font-weight: 500;
    }
    
    .invoice-table {
      background: white;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .invoice-table th {
      background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
      color: white;
      padding: 1rem;
      font-weight: 600;
      text-align: left;
    }
    
    .invoice-table td {
      padding: 1rem;
      border-bottom: 1px solid #e2e8f0;
    }
    
    .invoice-table tr:hover {
      background: #f8fafc;
    }
    
    .btn {
      padding: 0.5rem 1rem;
      border-radius: 6px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s;
      border: none;
      font-size: 0.875rem;
    }
    
    .btn-primary {
      background: var(--primary-color);
      color: white;
    }
    
    .btn-primary:hover {
      background: #4f46e5;
    }
    
    .btn-danger {
      background: var(--danger-color);
      color: white;
    }
    
    .btn-danger:hover {
      background: #dc2626;
    }
    
    .status-badge {
      padding: 0.25rem 0.75rem;
      border-radius: 20px;
      font-size: 0.75rem;
      font-weight: 500;
    }
    
    .status-paid {
      background: #dcfce7;
      color: #166534;
    }
    
    .status-pending {
      background: #fef3c7;
      color: #92400e;
    }
    
    .search-box {
      background: white;
      border: 2px solid #e2e8f0;
      border-radius: 8px;
      padding: 0.75rem 1rem;
      width: 100%;
      max-width: 400px;
    }
    
    .search-box:focus {
      outline: none;
      border-color: var(--primary-color);
      box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
    }
  </style>
</head>
<body>
  <div class="min-h-screen bg-gray-50">
    <header class="bg-white shadow-sm border-b">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center py-4">
          <div class="flex items-center">
            <div class="w-10 h-10 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center text-white font-bold text-lg">
              SA
            </div>
            <div class="ml-3">
              <h1 class="text-xl font-bold text-gray-900">SA Physio Care</h1>
              <p class="text-sm text-gray-500">Admin Dashboard</p>
            </div>
          </div>
          <div class="flex items-center space-x-4">
            <button onclick="window.location.href='/'" class="btn btn-primary">
              <i class="fas fa-plus mr-2"></i>New Invoice
            </button>
          </div>
        </div>
      </div>
    </header>

    <main class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div class="stat-card">
          <div class="flex items-center justify-between">
            <div>
              <h3 id="total-invoices">{{ stats.total_invoices }}</h3>
              <p>Total Invoices</p>
            </div>
            <div class="text-indigo-500 text-2xl">
              <i class="fas fa-file-invoice"></i>
            </div>
          </div>
        </div>
        
        <div class="stat-card">
          <div class="flex items-center justify-between">
            <div>
              <h3 id="total-revenue">£{{ "%.2f"|format(stats.total_revenue) }}</h3>
              <p>Total Revenue</p>
            </div>
            <div class="text-green-500 text-2xl">
              <i class="fas fa-pound-sign"></i>
            </div>
          </div>
        </div>
        
        <div class="stat-card">
          <div class="flex items-center justify-between">
            <div>
              <h3 id="this-month">{{ stats.this_month }}</h3>
              <p>This Month</p>
            </div>
            <div class="text-blue-500 text-2xl">
              <i class="fas fa-calendar-alt"></i>
            </div>
          </div>
        </div>
        
        <div class="stat-card">
          <div class="flex items-center justify-between">
            <div>
              <h3 id="avg-invoice">£{{ "%.2f"|format(stats.avg_invoice) }}</h3>
              <p>Avg Invoice</p>
            </div>
            <div class="text-purple-500 text-2xl">
              <i class="fas fa-chart-line"></i>
            </div>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-lg shadow-sm p-6 mb-6">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div class="flex-1">
            <input type="text" id="search-input" placeholder="Search invoices..." class="search-box">
          </div>
          <div class="flex gap-2">
            <select id="filter-month" class="search-box max-w-none w-auto">
              <option value="">All Months</option>
              <option value="2025-01">January 2025</option>
              <option value="2025-02">February 2025</option>
              <option value="2025-03">March 2025</option>
              <option value="2025-04">April 2025</option>
              <option value="2025-05">May 2025</option>
              <option value="2025-06">June 2025</option>
            </select>
            <button onclick="exportData()" class="btn btn-primary">
              <i class="fas fa-download mr-2"></i>Export
            </button>
          </div>
        </div>
      </div>

      <div class="invoice-table">
        <table class="w-full">
          <thead>
            <tr>
              <th>Invoice #</th>
              <th>Date</th>
              <th>Patient</th>
              <th>Treatment</th>
              <th>Amount</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody id="invoices-table-body">
            {% for invoice in invoices %}
            <tr>
              <td class="font-mono">{{ invoice.invoice_no }}</td>
              <td>{{ invoice.invoice_date or 'N/A' }}</td>
              <td>{{ invoice.patient_name or 'N/A' }}</td>
              <td>{{ invoice.treatment or 'N/A' }}</td>
              <td class="font-semibold">£{{ "%.2f"|format(invoice.grand_total or 0) }}</td>
              <td>
                <span class="status-badge status-paid">Paid</span>
              </td>
              <td>
                <div class="flex gap-2">
                  <button onclick="viewInvoice({{ invoice.id }})" class="btn btn-primary">
                    <i class="fas fa-eye"></i>
                  </button>
                  <button onclick="deleteInvoice({{ invoice.id }})" class="btn btn-danger">
                    <i class="fas fa-trash"></i>
                  </button>
                </div>
              </td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    </main>
  </div>

  <script>
    document.getElementById('search-input').addEventListener('input', function() {
      const searchTerm = this.value.toLowerCase();
      const rows = document.querySelectorAll('#invoices-table-body tr');
      rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchTerm) ? '' : 'none';
      });
    });

    document.getElementById('filter-month').addEventListener('change', function() {
      const selectedMonth = this.value;
      const rows = document.querySelectorAll('#invoices-table-body tr');
      rows.forEach(row => {
        const dateCell = row.cells[1].textContent;
        if (!selectedMonth || dateCell.includes(selectedMonth)) {
          row.style.display = '';
        } else {
          row.style.display = 'none';
        }
      });
    });

    function viewInvoice(id) {
      window.open(`/invoice/${id}`, '_blank');
    }

    function deleteInvoice(id) {
      if (confirm('Are you sure you want to delete this invoice?')) {
        fetch(`/delete/${id}`, { method: 'DELETE' })
          .then(response => response.json())
          .then(result => {
            if (result.status === 'success') {
              location.reload();
            } else {
              alert('Error deleting invoice');
            }
          });
      }
    }

    function exportData() {
      window.location.href = '/export';
    }
  </script>
</body>
</html>
'''

@app.route('/')
def index():
    invoice_no = generate_invoice_number()
    return render_template_string(invoice_template, invoice_no=invoice_no)

@app.route('/admin')
def admin():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM invoices ORDER BY id DESC')
    invoices = [dict(zip([col[0] for col in c.description], row)) for row in c.fetchall()]
    
    c.execute('SELECT COUNT(*) FROM invoices')
    total_invoices = c.fetchone()[0]
    
    c.execute('SELECT SUM(grand_total) FROM invoices')
    total_revenue = c.fetchone()[0] or 0
    
    current_month = datetime.now().strftime('%Y-%m')
    c.execute('SELECT COUNT(*) FROM invoices WHERE invoice_date LIKE %s', (f'{current_month}%',))
    this_month = c.fetchone()[0]
    
    avg_invoice = total_revenue / total_invoices if total_invoices > 0 else 0
    conn.close()
    
    stats = {
        'total_invoices': total_invoices,
        'total_revenue': total_revenue,
        'this_month': this_month,
        'avg_invoice': avg_invoice
    }
    
    return render_template_string(admin_template, invoices=invoices, stats=stats)

# Example for save_invoice route
@app.route('/save', methods=['POST'])
def save_invoice():
    try:
        init_db()
        data = request.get_json()
        conn = get_db_connection()
        c = conn.cursor()
        
        for i, item in enumerate(data.get('items', [])):
            c.execute('''
                INSERT INTO invoices (
                    invoice_no, invoice_date, patient_name, patient_id, address,
                    treatment, quantity, unit_price, total, vat, grand_total
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                data['invoice_no'] + (f'-{i+1}' if i > 0 else ''),
                data['invoice_date'],
                data['patient_name'],
                data['patient_id'],
                data['address'],
                item['treatment'],
                item['quantity'],
                item['unit_price'],
                item['total'],
                data['vat'] if i == 0 else 0,
                data['grand_total'] if i == 0 else item['total']
            ))
        
        conn.commit()
        conn.close()
        return jsonify({'status': 'success', 'message': 'Invoice saved successfully'})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/invoice/<int:invoice_id>')
def view_invoice(invoice_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM invoices WHERE id = %s', (invoice_id,))
    invoice = c.fetchone()
    conn.close()
    
    if invoice:
        cols = [col[0] for col in c.description]
        return render_template_string(invoice_template, **dict(zip(cols, invoice)))
    return "Invoice not found", 404

@app.route('/delete/<int:invoice_id>', methods=['DELETE'])
def delete_invoice(invoice_id):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('DELETE FROM invoices WHERE id = %s', (invoice_id,))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/export')
def export_data():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM invoices ORDER BY invoice_date DESC')
    invoices = c.fetchall()
    conn.close()
    
    import csv, io
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Invoice No', 'Date', 'Patient Name', 'Patient ID', 'Address', 
                     'Treatment', 'Quantity', 'Unit Price', 'Total', 'VAT', 'Grand Total'])
    for invoice in invoices:
        writer.writerow(invoice[1:])
    
    output.seek(0)
    return output.getvalue(), 200, {
        'Content-Type': 'text/csv',
        'Content-Disposition': 'attachment; filename=sa_physio_invoices.csv'
    }

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

def create_invoice_pdf(data):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Theme Colors
    theme_color = colors.HexColor('#76ccd0')
    light_text = colors.white
    border_color = colors.HexColor('#dddddd')
    dark_text = colors.HexColor('#333333')

    # Header Background
    c.setFillColor(theme_color)
    c.rect(0, height - 120, width, 120, fill=True, stroke=False)

    # Logo
    try:
        logo_path = os.path.join('static', 'sa_logo.png')
        if os.path.exists(logo_path):
            c.drawImage(logo_path, 40, height - 100, width=60, height=60, preserveAspectRatio=True, mask='auto')
    except:
        pass

    # Clinic Info (top-right)
    c.setFillColor(light_text)
    c.setFont("Helvetica-Bold", 18)
    c.drawRightString(width - 40, height - 50, "SA PHYSIO CARE LTD")

    c.setFont("Helvetica", 9)
    contact_lines = [
        "Suvarna Avilala - Specialist Physiotherapist",
        "01296 580770 / 07438 326185",
        "info@saphysiocare.co.uk",
        "51 Savernake Road, Aylesbury, HP19 9XP"
    ]
    for i, line in enumerate(contact_lines):
        c.drawRightString(width - 40, height - 65 - (i * 12), line)

    # Invoice Title
    c.setFillColor(dark_text)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(40, height - 150, "INVOICE")

    # Bill To
    y = height - 170
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, y, "BILL TO:")
    c.setFont("Helvetica", 10)
    y -= 15
    c.drawString(40, y, data.get("patient_name", ""))
    y -= 15
    c.drawString(40, y, data.get("address", ""))
    y -= 30

    # Invoice Meta Info with reduced horizontal spacing
    meta_y = height - 150
    line_gap = 14
    c.setFont("Helvetica-Bold", 10)
    c.drawString(width - 200, meta_y, "INVOICE:")
    c.drawString(width - 200, meta_y - line_gap, "DATE:")
    c.drawString(width - 200, meta_y - 2 * line_gap, "DUE DATE:")

    c.setFont("Helvetica", 10)
    c.drawString(width - 130, meta_y, data.get('invoice_no', ''))
    c.drawString(width - 130, meta_y - line_gap, data.get('invoice_date', ''))
    c.drawString(width - 130, meta_y - 2 * line_gap, data.get('due_date', ''))

    # Table Headers
    y = height - 220
    c.setStrokeColor(border_color)
    c.setLineWidth(0.5)
    c.line(40, y, width - 40, y)

    y -= 15
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(dark_text)
    c.drawString(40, y, "DESCRIPTION")
    c.drawRightString(width - 220, y, "QTY")
    c.drawRightString(width - 150, y, "UNIT PRICE")
    c.drawRightString(width - 40, y, "TOTAL")

    y -= 10
    c.line(40, y, width - 40, y)

    # Table Rows
    c.setFont("Helvetica", 10)
    items = data.get("items", [])
    for item in items:
        y -= 18
        if y < 100:
            c.showPage()
            y = height - 100

        treatment = item.get("treatment", "")[:60]
        qty = str(item.get("quantity", ""))
        unit_price = f"{item.get('unit_price', 0):.2f}"
        total = f"{item.get('total', 0):.2f}"

        c.drawString(40, y, treatment)
        c.drawRightString(width - 220, y, qty)
        c.drawRightString(width - 150, y, unit_price)
        c.drawRightString(width - 40, y, total)

    # Notes Section
    y -= 40
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, y, "NOTES")
    c.setFont("Helvetica", 9)
    y -= 15
    for line in data.get("notes", "").split('\n'):
        c.drawString(40, y, line[:100])
        y -= 12

    # Totals Box (bottom-right)
    y = 130
    c.setFillColor(theme_color)
    c.rect(width - 200, y, 160, 90, fill=True, stroke=False)

    c.setFillColor(light_text)
    c.setFont("Helvetica", 10)
    c.drawString(width - 190, y + 65, "Subtotal:")
    c.drawString(width - 190, y + 45, "VAT (20%):")
    c.setFont("Helvetica-Bold", 12)
    c.drawString(width - 190, y + 20, "TOTAL:")

    c.setFont("Helvetica", 10)
    c.drawRightString(width - 50, y + 65, f"£{data.get('subtotal', 0):.2f}")
    c.drawRightString(width - 50, y + 45, f"£{data.get('vat', 0):.2f}")
    c.setFont("Helvetica-Bold", 14)
    c.drawRightString(width - 50, y + 20, f"£{data.get('grand_total', 0):.2f}")

    # Footer
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.grey)
    c.drawCentredString(width / 2, 30, "SA Physio Care | 51 Savernake Road, HP19 9XP")
    c.drawCentredString(width / 2, 20, "Tel: 01296 580770 / 07438 326185 | Email: info@saphysiocare.co.uk")
    c.drawCentredString(width / 2, 10, f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    c.save()
    buffer.seek(0)
    return buffer



@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    try:
        data = request.get_json()
        pdf_buffer = create_invoice_pdf(data)
        pdf_data = pdf_buffer.getvalue()
        
        if not pdf_data.startswith(b'%PDF-'):
            raise ValueError("Invalid PDF generated")
        
        filename = f"SA_Physio_Invoice_{data.get('invoice_no', '')}.pdf"
        return pdf_data, 200, {
            'Content-Type': 'application/pdf',
            'Content-Disposition': f'attachment; filename={filename}'
        }
    
    except Exception as e:
        app.logger.error(f"PDF generation error: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': f'PDF generation failed: {str(e)}'
        }), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5002)