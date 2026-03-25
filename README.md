# BKK Innovation Hub Invoice System

A branded invoicing app for BKK Innovation Hub with:

- digital invoice creation
- client directory
- professional PDF export with letterhead
- invoice history
- one-click SMTP email sending
- invoice status badges
- logo upload support in Settings

## Included

- `app.py` - Streamlit app
- `invoice_system.py` - invoice models, storage, PDF generator, SMTP sender
- `generate_sample.py` - creates a sample invoice PDF for Khanyisa Disability Centre
- `assets/` - put your logo here
- `data/` - JSON storage for settings, clients, and invoices

## Logo placement

Put your logo file here:

```bash
assets/bkk_logo.png
```

or

```bash
assets/bkk_logo.jpeg
```

Then update the path in **Settings** if needed.

## SMTP password

Create a `.env` file or export the env var directly:

```bash
export BKK_SMTP_PASSWORD="your_app_password_here"
```

For Gmail / Google Workspace, use an **App Password**.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Git workflow

```bash
git checkout dev
git pull origin dev
git checkout -b feature/email-send-system
git add .
git commit -m "Add invoice email sending and UI upgrades"
git push origin feature/email-send-system
```

Then open a PR from `feature/email-send-system` into `dev`.
