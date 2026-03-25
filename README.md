# BKK Innovation Hub Invoice System

A branded invoicing app for BKK Innovation Hub with:
- digital invoice creation
- client directory
- professional PDF export with letterhead
- invoice history
- email and WhatsApp share links
- editable business settings

## Included
- `app.py` - Streamlit app
- `invoice_system.py` - invoice models, storage, and PDF generator
- `generate_sample.py` - creates a sample invoice PDF for Khanyisa Disability Centre
- `assets/bkk_logo.jpeg` - BKK logo used in the letterhead
- `data/` - JSON storage for settings, clients, and invoices

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Generate the sample PDF

```bash
python generate_sample.py
```

## Production notes
- Replace the logo file if needed and update the path in Settings.
- JSON storage is good for a starter deployment. For a multi-user deployment, move invoices and clients into PostgreSQL.
- SMTP email sending can be added later if you want one-click sending from inside the app.
- You can deploy this on Streamlit Community Cloud, Render, or your own Linux VPS.
