
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pandas as pd
import streamlit as st

from invoice_system import (
    BusinessSettings,
    Client,
    Invoice,
    InvoiceItem,
    build_invoice_pdf,
    delete_invoice,
    ensure_data_files,
    fmt_currency,
    load_clients,
    load_invoices,
    load_settings,
    make_example_invoice,
    next_invoice_number,
    save_clients,
    save_invoice,
    save_settings,
    send_invoice_email,
    money,
)

st.set_page_config(
    page_title="BKK Invoice System",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded",
)

ensure_data_files()


# -----------------------------
# Styling
# -----------------------------
def inject_css() -> None:
    # PWA meta tags for mobile "Add to Home Screen"
    st.markdown(
        """
        <link rel="manifest" href="./app/static/manifest.json">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
        <meta name="apple-mobile-web-app-title" content="BKK Invoice">
        <meta name="mobile-web-app-capable" content="yes">
        <meta name="theme-color" content="#173C65">
        <link rel="apple-touch-icon" href="./app/static/icon-192.png">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <style>
            :root {
                --bg: #f5f8fb;
                --surface: #ffffff;
                --surface-2: #f8fbfd;
                --primary: #173C65;
                --teal: #0F766E;
                --orange: #E77728;
                --text: #102A43;
                --muted: #627D98;
                --border: #D9E2EC;
                --shadow: 0 10px 30px rgba(16, 42, 67, 0.08);
                --radius: 18px;
            }

            .stApp {
                background: linear-gradient(180deg, #f9fbfd 0%, #f2f6fa 100%) !important;
                color: var(--text) !important;
            }

            /* Force light text/background on main content */
            .stApp [data-testid="stAppViewContainer"] {
                color: var(--text) !important;
            }

            .stApp [data-testid="stHeader"] {
                background: transparent !important;
            }

            /* Form inputs - force light mode */
            .stTextInput input,
            .stTextArea textarea,
            .stNumberInput input,
            .stDateInput input {
                background-color: #ffffff !important;
                color: #102A43 !important;
            }

            div[data-baseweb="select"] > div {
                background-color: #ffffff !important;
                color: #102A43 !important;
            }

            div[data-baseweb="select"] * {
                color: #102A43 !important;
            }

            /* Labels */
            .stTextInput label,
            .stTextArea label,
            .stNumberInput label,
            .stDateInput label,
            .stSelectbox label,
            .stDataFrame label,
            .stCheckbox label {
                color: #102A43 !important;
            }

            /* Markdown text */
            .stMarkdown, .stMarkdown p, .stMarkdown li {
                color: var(--text) !important;
            }

            /* Data editor header */
            [data-testid="stDataFrame"] {
                color: #102A43 !important;
            }

            [data-testid="stSidebar"] {
                background: linear-gradient(180deg, #0e1726 0%, #132238 100%) !important;
                border-right: 1px solid rgba(255,255,255,0.06);
            }

            [data-testid="stSidebar"] * {
                color: #EAF2F8 !important;
            }

            .sidebar-brand {
                padding: 0.9rem 1rem 1rem 1rem;
                border-radius: 16px;
                background: linear-gradient(135deg, rgba(23,60,101,0.96) 0%, rgba(15,118,110,0.96) 72%, rgba(231,119,40,0.96) 100%);
                box-shadow: 0 16px 32px rgba(0,0,0,0.18);
                margin-bottom: 1rem;
            }

            .sidebar-brand .eyebrow {
                font-size: 0.75rem;
                opacity: 0.9;
                letter-spacing: 0.08em;
                text-transform: uppercase;
            }

            .sidebar-brand .title {
                font-size: 1.35rem;
                font-weight: 800;
                margin-top: 0.2rem;
                line-height: 1.15;
            }

            .hero {
                background: linear-gradient(135deg, #173C65 0%, #155e75 65%, #E77728 100%);
                color: white;
                padding: 1.4rem 1.5rem;
                border-radius: 24px;
                box-shadow: 0 20px 45px rgba(23, 60, 101, 0.18);
                margin-bottom: 1rem;
                border: 1px solid rgba(255,255,255,0.18);
            }

            .hero .eyebrow {
                font-size: 0.78rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                opacity: 0.88;
            }

            .hero .title {
                font-size: 2rem;
                font-weight: 800;
                line-height: 1.1;
                margin-top: 0.25rem;
            }

            .hero .sub {
                margin-top: 0.45rem;
                font-size: 1rem;
                opacity: 0.95;
            }

            .metric-card {
                background: var(--surface);
                border: 1px solid rgba(15, 118, 110, 0.08);
                border-radius: 20px;
                padding: 1rem 1rem 0.9rem 1rem;
                box-shadow: var(--shadow);
            }

            .metric-label {
                font-size: 0.82rem;
                color: var(--muted);
                margin-bottom: 0.35rem;
            }

            .metric-value {
                font-size: 1.6rem;
                font-weight: 800;
                color: var(--text);
                line-height: 1.1;
            }

            .metric-foot {
                margin-top: 0.4rem;
                font-size: 0.82rem;
                color: var(--muted);
            }

            .section-card {
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: 22px;
                padding: 1rem 1rem 0.6rem 1rem;
                box-shadow: var(--shadow);
                margin-bottom: 1rem;
            }

            .section-title {
                font-size: 1.05rem;
                font-weight: 800;
                color: var(--text);
                margin-bottom: 0.15rem;
            }

            .section-sub {
                font-size: 0.9rem;
                color: var(--muted);
                margin-bottom: 0.9rem;
            }

            .preview-card {
                background: linear-gradient(180deg, #ffffff 0%, #f8fbfd 100%);
                border: 1px solid var(--border);
                border-radius: 22px;
                padding: 1rem;
                box-shadow: var(--shadow);
                position: sticky;
                top: 1rem;
            }

            .preview-total {
                font-size: 1.8rem;
                font-weight: 800;
                color: var(--primary);
                line-height: 1.05;
            }

            .muted {
                color: var(--muted);
                font-size: 0.9rem;
            }

            .badge {
                display: inline-block;
                padding: 0.28rem 0.65rem;
                border-radius: 999px;
                font-size: 0.78rem;
                font-weight: 700;
                border: 1px solid transparent;
            }

            .badge-draft {
                background: #F2F4F7;
                color: #344054;
                border-color: #E4E7EC;
            }

            .badge-sent {
                background: #EFF8FF;
                color: #175CD3;
                border-color: #B2DDFF;
            }

            .badge-paid {
                background: #ECFDF3;
                color: #027A48;
                border-color: #ABEFC6;
            }

            .badge-overdue {
                background: #FEF3F2;
                color: #B42318;
                border-color: #FECDCA;
            }

            .badge-cancelled {
                background: #FFF1F3;
                color: #C01048;
                border-color: #FCCEE0;
            }

            .history-row {
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: 18px;
                padding: 0.85rem 1rem;
                box-shadow: 0 6px 20px rgba(16,42,67,0.05);
                margin-bottom: 0.75rem;
            }

            .invoice-number {
                font-weight: 800;
                color: var(--primary);
            }

            .tiny {
                font-size: 0.82rem;
                color: var(--muted);
            }

            .stButton>button, .stDownloadButton>button {
                border-radius: 14px !important;
                min-height: 2.7rem !important;
                font-weight: 700 !important;
                border: 1px solid #D0D7E2 !important;
                background-color: #ffffff !important;
                color: #102A43 !important;
            }

            .stButton>button:hover, .stDownloadButton>button:hover {
                background-color: #f0f4f8 !important;
                border-color: #173C65 !important;
                color: #173C65 !important;
            }

            .stTextInput input,
            .stTextArea textarea,
            div[data-baseweb="select"] > div,
            .stDateInput input,
            .stNumberInput input {
                border-radius: 14px !important;
                background-color: #ffffff !important;
                color: #102A43 !important;
                border-color: #D9E2EC !important;
            }

            /* Subheaders and form titles */
            h1, h2, h3, h4, h5, h6 {
                color: #102A43 !important;
            }

            /* Info/warning/success boxes */
            .stAlert {
                border-radius: 14px !important;
            }

            /* Caption text */
            .stCaption, small {
                color: #627D98 !important;
            }

            .stTabs [data-baseweb="tab-list"] {
                gap: 0.4rem;
            }

            .stTabs [data-baseweb="tab"] {
                border-radius: 14px 14px 0 0;
                padding-left: 1rem;
                padding-right: 1rem;
            }

            /* ── Mobile responsive ── */
            @media (max-width: 768px) {
                .hero { padding: 1rem; border-radius: 16px; }
                .hero .title { font-size: 1.3rem; }
                .metric-card { padding: 0.7rem; border-radius: 14px; }
                .metric-value { font-size: 1.2rem; }
                .section-card { padding: 0.7rem; border-radius: 14px; }
                .preview-card { padding: 0.7rem; border-radius: 14px; }
                .history-row { padding: 0.6rem 0.7rem; border-radius: 12px; }
                .preview-total { font-size: 1.3rem; }
            }

            /* ── Spinner styling ── */
            .stSpinner > div {
                border-radius: 14px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------
# Utilities
# -----------------------------
def badge_html(status: str) -> str:
    lookup = {
        "Draft": "badge-draft",
        "Sent": "badge-sent",
        "Paid": "badge-paid",
        "Overdue": "badge-overdue",
        "Cancelled": "badge-cancelled",
    }
    css = lookup.get(status, "badge-draft")
    return f'<span class="badge {css}">{status}</span>'


def client_lookup(clients: list[Client], name: str) -> Client | None:
    for client in clients:
        if client.name == name:
            return client
    return None


def safe_ratio(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "0%"
    return f"{round((numerator / denominator) * 100)}%"


def render_metric_card(label: str, value: str, foot: str = "") -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-foot">{foot}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="section-title">{title}</div>
        <div class="section-sub">{subtitle}</div>
        """,
        unsafe_allow_html=True,
    )


def back_button(fallback: str = "Dashboard") -> None:
    """Render a back button that returns to the previous page."""
    history = st.session_state.get("page_history", [])
    prev = history[-1] if history else fallback
    if st.button(f"← Back to {prev}", key=f"back_{prev}"):
        st.session_state["page_history"] = history[:-1]
        st.session_state["nav_page"] = prev
        st.rerun()


# -----------------------------
# App bootstrap
# -----------------------------
inject_css()
settings = load_settings()
clients = load_clients()
invoices = load_invoices()

# Resolve logo path: try settings value, fall back to default assets location
_logo_candidate = Path(settings.logo_path)
if not _logo_candidate.exists():
    _logo_candidate = Path(__file__).resolve().parent / "assets" / "bkk_logo.jpeg"
logo_path = _logo_candidate


# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="eyebrow">BKK Innovation Hub</div>
            <div class="title">Invoice System</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if logo_path.exists():
        st.image(str(logo_path), width=140)

    # Support programmatic navigation (e.g. Edit button → Create Invoice)
    nav_options = ["Dashboard", "Create Invoice", "Invoice History", "Clients", "Settings"]
    nav_override = st.session_state.pop("nav_page", None)
    default_nav_index = nav_options.index(nav_override) if nav_override in nav_options else 0

    page = st.radio(
        "Navigate",
        nav_options,
        index=default_nav_index,
        label_visibility="collapsed",
    )

    # Track page history for back navigation
    if "page_history" not in st.session_state:
        st.session_state["page_history"] = []
    if "last_page" not in st.session_state:
        st.session_state["last_page"] = "Dashboard"
    if page != st.session_state["last_page"]:
        st.session_state["page_history"].append(st.session_state["last_page"])
        # Keep history short
        st.session_state["page_history"] = st.session_state["page_history"][-10:]
        st.session_state["last_page"] = page

    st.markdown("---")
    st.caption("Professional invoicing, PDF export, and client management for BKK Innovation Hub.")


# -----------------------------
# Top hero
# -----------------------------
col_logo, col_hero = st.columns([1, 4])
with col_logo:
    if logo_path.exists():
        st.image(str(logo_path), width=130)
with col_hero:
    st.markdown(
        f"""
        <div class="hero">
            <div class="eyebrow">Digital invoicing + PDF export + share</div>
            <div class="title">{settings.business_name}</div>
            <div class="sub">A clean, premium invoicing workspace for creating, sending, and tracking professional invoices.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------
# KPI bar
# -----------------------------
paid_count = sum(1 for inv in invoices if inv.status == "Paid")
sent_count = sum(1 for inv in invoices if inv.status == "Sent")
outstanding_total = sum(
    (inv.total for inv in invoices if inv.status in {"Draft", "Sent", "Overdue"}),
    Decimal("0.00"),
)
paid_total = sum((inv.total for inv in invoices if inv.status == "Paid"), Decimal("0.00"))

a, b, c, d = st.columns(4)
with a:
    render_metric_card("Total invoices", str(len(invoices)), "All saved invoices")
with b:
    render_metric_card("Paid revenue", fmt_currency(paid_total, settings.currency_symbol), f"{paid_count} paid invoices")
with c:
    render_metric_card("Outstanding", fmt_currency(outstanding_total, settings.currency_symbol), f"{sent_count} already sent")
with d:
    render_metric_card("Collection rate", safe_ratio(paid_count, len(invoices)), "Paid invoices vs total")

st.write("")


# -----------------------------
# Dashboard
# -----------------------------
if page == "Dashboard":
    left, right = st.columns([1.45, 1])

    with left:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        render_section_header("Recent invoices", "Quick visibility into the latest billing activity.")

        if not invoices:
            st.info("No invoices yet. Create your first invoice to get started.")
        else:
            recent = invoices[:5]
            for inv in recent:
                st.markdown('<div class="history-row">', unsafe_allow_html=True)
                c1, c2, c3, c4 = st.columns([2, 2, 1.3, 1])
                c1.markdown(f'<div class="invoice-number">{inv.invoice_number}</div><div class="tiny">Issued {inv.issue_date}</div>', unsafe_allow_html=True)
                c2.markdown(f'**{inv.bill_to_name}**<div class="tiny">Due {inv.due_date}</div>', unsafe_allow_html=True)
                c3.markdown(f'**{fmt_currency(inv.total, settings.currency_symbol)}**', unsafe_allow_html=True)
                c4.markdown(badge_html(inv.status), unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        render_section_header("Business snapshot", "Your active brand and payment profile.")
        st.write(f"**Business:** {settings.business_name}")
        st.write(f"**Billing email:** {settings.billing_email}")
        st.write(f"**Phone:** {settings.phone}")
        st.write(f"**Invoice prefix:** {settings.invoice_prefix}")
        st.write(f"**Default VAT:** {settings.vat_rate:.0f}%")
        st.write(f"**Payment terms:** {settings.payment_terms_days} days")
        st.write(f"**Bank:** {settings.bank_name}")
        st.write(f"**Account:** {settings.account_number}")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        render_section_header("Top actions", "Move quickly with your most common tasks.")
        if st.button("+ Create new invoice", use_container_width=True, key="dash_create"):
            st.session_state["nav_page"] = "Create Invoice"
            st.rerun()
        if st.button("Manage clients", use_container_width=True, key="dash_clients"):
            st.session_state["nav_page"] = "Clients"
            st.rerun()
        if st.button("Update settings", use_container_width=True, key="dash_settings"):
            st.session_state["nav_page"] = "Settings"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


# -----------------------------
# Create Invoice
# -----------------------------
elif page == "Create Invoice":
    back_button()
    # Check if we're editing an existing invoice
    edit_inv = st.session_state.pop("edit_invoice", None)
    if edit_inv:
        defaults = edit_inv
        editing_existing = True
    else:
        defaults = make_example_invoice(settings)
        editing_existing = False

    client_options = [client.name for client in clients] + ["Custom client"]
    # Match client dropdown to the invoice being edited
    if editing_existing and defaults.bill_to_name in client_options:
        default_index = client_options.index(defaults.bill_to_name)
    elif editing_existing:
        default_index = len(client_options) - 1  # Custom client
    else:
        default_index = 0 if clients else len(client_options) - 1

    # Pre-compute status index for editing
    status_options = ["Draft", "Sent", "Paid", "Overdue", "Cancelled"]
    default_status_index = status_options.index(defaults.status) if defaults.status in status_options else 0

    left, right = st.columns([1.7, 1])

    with left:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        header_text = f"Editing {defaults.invoice_number}" if editing_existing else "Create invoice"
        render_section_header(header_text, "A clean editor for client details, line items, and billing information.")

        with st.form("invoice_form", clear_on_submit=False):
            info_left, info_right = st.columns([1.3, 1])

            with info_left:
                selected_client_name = st.selectbox("Client", options=client_options, index=default_index)
                chosen_client = client_lookup(clients, selected_client_name) if selected_client_name != "Custom client" else None
                bill_to_name = st.text_input("Bill to name", value=chosen_client.name if chosen_client and not editing_existing else defaults.bill_to_name)
                bill_to_address = st.text_area(
                    "Bill to address",
                    value=chosen_client.address if chosen_client and not editing_existing else defaults.bill_to_address,
                    height=90,
                )
                bill_to_email = st.text_input("Client email", value=chosen_client.email if chosen_client and not editing_existing else defaults.bill_to_email)
                bill_to_phone = st.text_input("Client phone", value=chosen_client.phone if chosen_client and not editing_existing else (defaults.bill_to_phone or ""))

            with info_right:
                invoice_number = st.text_input("Invoice number", value=defaults.invoice_number if editing_existing else next_invoice_number(settings))
                issue_date = st.date_input("Issue date", value=date.fromisoformat(defaults.issue_date) if editing_existing else date.today())
                due_date = st.date_input("Due date", value=date.fromisoformat(defaults.due_date) if editing_existing else date.today() + timedelta(days=settings.payment_terms_days))
                reference = st.text_input("Reference / PO", value=defaults.reference)
                status = st.selectbox("Status", status_options, index=default_status_index)
                vat_rate = st.number_input("VAT %", min_value=0.0, max_value=100.0, value=float(defaults.vat_rate) if editing_existing else float(settings.vat_rate), step=0.5)

            st.markdown("#### Line items")
            item_defaults = pd.DataFrame(
                [
                    {"Description": item.description, "Qty": float(item.qty), "Rate": float(item.rate)}
                    for item in defaults.items
                ]
            )
            item_df = st.data_editor(
                item_defaults,
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "Description": st.column_config.TextColumn(required=True, width="large"),
                    "Qty": st.column_config.NumberColumn(min_value=-999999.0, step=1.0, format="%.2f"),
                    "Rate": st.column_config.NumberColumn(min_value=-999999.0, step=50.0, format="%.2f"),
                },
                key="items_editor_redesign",
            )

            notes = st.text_area("Notes", value=defaults.notes, height=100)
            btn_label = "Update invoice" if editing_existing else "Save invoice"
            submitted = st.form_submit_button(btn_label, use_container_width=True)

        st.markdown('</div>', unsafe_allow_html=True)

    items: list[InvoiceItem] = []
    for _, row in item_df.iterrows():
        description = str(row.get("Description", "")).strip()
        qty = row.get("Qty", 0)
        rate = row.get("Rate", 0)
        if description:
            items.append(InvoiceItem(description=description, qty=money(qty), rate=money(rate)))

    live_invoice = Invoice(
        invoice_number=invoice_number,
        issue_date=str(issue_date),
        due_date=str(due_date),
        bill_to_name=bill_to_name,
        bill_to_address=bill_to_address,
        bill_to_email=bill_to_email,
        bill_to_phone=bill_to_phone,
        reference=reference,
        notes=notes,
        status=status,
        items=items,
        vat_rate=vat_rate,
    )

    with right:
        st.markdown('<div class="preview-card">', unsafe_allow_html=True)
        render_section_header("Live preview", "See totals and actions without leaving the editor.")
        st.markdown(f'<div class="muted">Invoice number</div><div class="invoice-number">{live_invoice.invoice_number}</div>', unsafe_allow_html=True)
        st.write("")
        st.markdown(f'<div class="muted">Client</div><div><strong>{live_invoice.bill_to_name}</strong></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="muted">Status</div>{badge_html(live_invoice.status)}', unsafe_allow_html=True)
        st.write("")
        st.markdown('<div class="muted">Total due</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="preview-total">{fmt_currency(live_invoice.total, settings.currency_symbol)}</div>', unsafe_allow_html=True)
        st.write(f"**Subtotal:** {fmt_currency(live_invoice.subtotal, settings.currency_symbol)}")
        st.write(f"**VAT:** {fmt_currency(live_invoice.vat_amount, settings.currency_symbol)}")
        st.write(f"**Due date:** {live_invoice.due_date}")
        st.write("---")

        pdf_bytes = build_invoice_pdf(live_invoice, settings)
        st.download_button(
            "Download PDF",
            data=pdf_bytes,
            file_name=f"{live_invoice.invoice_number}_{bill_to_name.replace(' ', '_')}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
        st.caption("Save the invoice first, then send the PDF from Invoice History.")
        st.markdown('</div>', unsafe_allow_html=True)

    if submitted:
        with st.spinner("Saving invoice…"):
            save_invoice(live_invoice)
        st.success(f"Invoice {live_invoice.invoice_number} saved successfully.")
        st.rerun()


# -----------------------------
# Invoice History
# -----------------------------
elif page == "Invoice History":
    back_button()
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    render_section_header("Invoice history", "Filter, review, and re-download every invoice from one place.")

    if not invoices:
        st.info("No invoices saved yet.")
    else:
        filter_a, filter_b = st.columns([1, 1])
        with filter_a:
            status_filter = st.selectbox("Filter by status", ["All", "Draft", "Sent", "Paid", "Overdue", "Cancelled"])
        with filter_b:
            search_term = st.text_input("Search by invoice or client", placeholder="e.g. BKK-INV or Khanyisa")

        filtered_invoices = invoices
        if status_filter != "All":
            filtered_invoices = [inv for inv in filtered_invoices if inv.status == status_filter]
        if search_term.strip():
            term = search_term.strip().lower()
            filtered_invoices = [
                inv
                for inv in filtered_invoices
                if term in inv.invoice_number.lower() or term in inv.bill_to_name.lower()
            ]

        if not filtered_invoices:
            st.warning("No invoices matched your filters.")
        else:
            for inv in filtered_invoices:
                st.markdown('<div class="history-row">', unsafe_allow_html=True)
                r1, r2, r3, r4, r5 = st.columns([1.8, 2, 1.3, 1.1, 1.2])
                r1.markdown(f'<div class="invoice-number">{inv.invoice_number}</div><div class="tiny">Ref: {inv.reference or "-"}</div>', unsafe_allow_html=True)
                r2.markdown(f'**{inv.bill_to_name}**<div class="tiny">Issued {inv.issue_date} • Due {inv.due_date}</div>', unsafe_allow_html=True)
                r3.markdown(f'**{fmt_currency(inv.total, settings.currency_symbol)}**', unsafe_allow_html=True)
                r4.markdown(badge_html(inv.status), unsafe_allow_html=True)
                pdf_bytes = build_invoice_pdf(inv, settings)
                r5.download_button(
                    "PDF",
                    data=pdf_bytes,
                    file_name=f"{inv.invoice_number}.pdf",
                    mime="application/pdf",
                    key=f"history_{inv.invoice_number}",
                    use_container_width=True,
                )

                # Action buttons row
                act1, act2, act3, act4 = st.columns(4)
                with act1:
                    if inv.status != "Paid":
                        if st.button("✅ Mark Paid", key=f"paid_{inv.invoice_number}", use_container_width=True):
                            with st.spinner("Updating…"):
                                inv.status = "Paid"
                                save_invoice(inv)
                            st.rerun()
                with act2:
                    if st.button("✏️ Edit", key=f"edit_{inv.invoice_number}", use_container_width=True):
                        st.session_state["edit_invoice"] = inv
                        st.session_state["nav_page"] = "Create Invoice"
                        st.rerun()
                with act3:
                    if inv.status == "Draft":
                        if st.button("🗑️ Remove", key=f"del_{inv.invoice_number}", use_container_width=True):
                            st.session_state[f"confirm_del_{inv.invoice_number}"] = True
                with act4:
                    if st.button("📧 Send", key=f"send_toggle_{inv.invoice_number}", use_container_width=True):
                        st.session_state[f"show_send_{inv.invoice_number}"] = not st.session_state.get(f"show_send_{inv.invoice_number}", False)

                # Send email panel
                if st.session_state.get(f"show_send_{inv.invoice_number}"):
                    st.markdown("---")
                    st.markdown("**Send invoice PDF by email**")
                    send_to = st.text_input("Recipient email", value=inv.bill_to_email, key=f"mailto_{inv.invoice_number}")
                    send_subject = st.text_input(
                        "Subject",
                        value=f"Invoice {inv.invoice_number} from {settings.business_name}",
                        key=f"subject_{inv.invoice_number}",
                    )
                    send_body = st.text_area(
                        "Message",
                        value=(
                            f"Dear {inv.bill_to_name},\n\n"
                            f"Please find attached invoice {inv.invoice_number} for "
                            f"{fmt_currency(inv.total, settings.currency_symbol)}.\n"
                            f"Due date: {inv.due_date}.\n\n"
                            f"Kind regards,\n{settings.business_name}"
                        ),
                        key=f"body_{inv.invoice_number}",
                        height=120,
                    )
                    if st.button(f"Send {inv.invoice_number}", key=f"do_send_{inv.invoice_number}", use_container_width=True):
                        with st.spinner("Sending email…"):
                            ok, msg = send_invoice_email(inv, settings, send_to, send_subject, send_body, pdf_bytes)
                        if ok:
                            if inv.status == "Draft":
                                inv.status = "Sent"
                                save_invoice(inv)
                            st.session_state.pop(f"show_send_{inv.invoice_number}", None)
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

                # Confirm deletion dialog
                if st.session_state.get(f"confirm_del_{inv.invoice_number}"):
                    st.warning(f"Are you sure you want to delete **{inv.invoice_number}**? This cannot be undone.")
                    yes_col, no_col = st.columns(2)
                    with yes_col:
                        if st.button("Yes, delete", key=f"yes_del_{inv.invoice_number}", use_container_width=True):
                            with st.spinner("Removing…"):
                                delete_invoice(inv.invoice_number)
                            st.session_state.pop(f"confirm_del_{inv.invoice_number}", None)
                            st.rerun()
                    with no_col:
                        if st.button("Cancel", key=f"no_del_{inv.invoice_number}", use_container_width=True):
                            st.session_state.pop(f"confirm_del_{inv.invoice_number}", None)
                            st.rerun()

                st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# -----------------------------
# Clients
# -----------------------------
elif page == "Clients":
    back_button()
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    render_section_header("Client directory", "Maintain a clean client list for faster invoice creation.")

    client_rows = pd.DataFrame([client.__dict__ for client in clients])
    edited = st.data_editor(
        client_rows if not client_rows.empty else pd.DataFrame(columns=["name", "contact_person", "email", "phone", "address"]),
        num_rows="dynamic",
        use_container_width=True,
        key="clients_editor_redesign",
    )

    save_client_btn = st.button("Save client changes", use_container_width=False)
    if save_client_btn:
        cleaned_clients: list[Client] = []
        for _, row in edited.iterrows():
            name = str(row.get("name", "")).strip()
            if not name:
                continue
            cleaned_clients.append(
                Client(
                    name=name,
                    contact_person=str(row.get("contact_person", "")).strip(),
                    email=str(row.get("email", "")).strip(),
                    phone=str(row.get("phone", "")).strip(),
                    address=str(row.get("address", "")).strip(),
                )
            )
        with st.spinner("Saving clients…"):
            save_clients(cleaned_clients)
        st.success("Client directory updated.")
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


# -----------------------------
# Settings
# -----------------------------
elif page == "Settings":
    back_button()
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    render_section_header("Business settings", "Control branding, banking details, and invoice defaults.")

    with st.form("settings_form_redesign"):
        s1, s2 = st.columns(2)

        with s1:
            st.markdown("#### Business profile")
            business_name = st.text_input("Business name", value=settings.business_name)
            address_line_1 = st.text_input("Address line 1", value=settings.address_line_1)
            address_line_2 = st.text_input("Address line 2", value=settings.address_line_2)
            billing_email = st.text_input("Billing email", value=settings.billing_email)
            phone = st.text_input("Phone", value=settings.phone)
            logo_path_input = st.text_input("Logo path", value=settings.logo_path)

        with s2:
            st.markdown("#### Payment and invoice defaults")
            bank_name = st.text_input("Bank name", value=settings.bank_name)
            account_name = st.text_input("Account name", value=settings.account_name)
            account_number = st.text_input("Account number", value=settings.account_number)
            invoice_prefix = st.text_input("Invoice prefix", value=settings.invoice_prefix)
            vat_rate_settings = st.number_input("Default VAT %", min_value=0.0, max_value=100.0, value=float(settings.vat_rate))
            payment_terms_days = st.number_input("Payment terms (days)", min_value=0, max_value=120, value=int(settings.payment_terms_days))

        payment_note = st.text_input("Payment note", value=settings.payment_note)
        footer_tagline = st.text_input("Footer tagline", value=settings.footer_tagline)

        st.markdown("#### SMTP / Email settings")
        smtp_s1, smtp_s2 = st.columns(2)
        with smtp_s1:
            smtp_host = st.text_input("SMTP host", value=settings.smtp_host)
            smtp_port = st.number_input("SMTP port", min_value=1, max_value=65535, value=int(settings.smtp_port))
            smtp_username = st.text_input("SMTP username", value=settings.smtp_username)
            smtp_sender_email = st.text_input("Sender email", value=settings.smtp_sender_email)
        with smtp_s2:
            smtp_sender_name = st.text_input("Sender name", value=settings.smtp_sender_name)
            smtp_password_env = st.text_input("SMTP password env var", value=settings.smtp_password_env)
            smtp_use_tls = st.checkbox("Use TLS", value=settings.smtp_use_tls)

        saved = st.form_submit_button("Save settings", use_container_width=True)

    if saved:
        updated = BusinessSettings(
            business_name=business_name,
            address_line_1=address_line_1,
            address_line_2=address_line_2,
            billing_email=billing_email,
            phone=phone,
            bank_name=bank_name,
            account_name=account_name,
            account_number=account_number,
            invoice_prefix=invoice_prefix,
            vat_rate=vat_rate_settings,
            payment_terms_days=int(payment_terms_days),
            payment_note=payment_note,
            footer_tagline=footer_tagline,
            logo_path=logo_path_input,
            currency_symbol=settings.currency_symbol,
            smtp_host=smtp_host,
            smtp_port=int(smtp_port),
            smtp_username=smtp_username,
            smtp_sender_email=smtp_sender_email,
            smtp_sender_name=smtp_sender_name,
            smtp_password_env=smtp_password_env,
            smtp_use_tls=smtp_use_tls,
        )
        with st.spinner("Saving settings…"):
            save_settings(updated)
        st.success("Settings saved successfully.")
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
