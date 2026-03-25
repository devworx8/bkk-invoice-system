from __future__ import annotations

import os
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
    ensure_data_files,
    fmt_currency,
    load_clients,
    load_invoices,
    load_settings,
    mailto_link,
    make_example_invoice,
    next_invoice_number,
    save_clients,
    save_invoice,
    save_settings,
    whatsapp_link,
    money,
)

st.set_page_config(page_title="BKK Invoice System", page_icon="🧾", layout="wide")

ensure_data_files()


def inject_css() -> None:
    st.markdown(
        """
        <style>
        .stApp { background: linear-gradient(180deg, #f8fbfd 0%, #eef5f9 100%); }
        .hero-card {
            background: linear-gradient(135deg, #173C65 0%, #0F766E 70%, #E77728 100%);
            padding: 1.2rem 1.4rem;
            border-radius: 20px;
            color: white;
            box-shadow: 0 12px 30px rgba(23,60,101,0.18);
            margin-bottom: 1rem;
        }
        .metric-card {
            background: white;
            border-radius: 18px;
            padding: 1rem;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
            border: 1px solid rgba(15, 118, 110, 0.08);
        }
        .block-title { font-size: 0.9rem; color: #486581; margin-bottom: 0.25rem; }
        .block-value { font-size: 1.45rem; font-weight: 700; color: #102A43; }
        .share-row a {
            display: inline-block;
            margin-right: 12px;
            padding: 10px 14px;
            background: white;
            border-radius: 999px;
            text-decoration: none;
            color: #173C65;
            border: 1px solid #d9e2ec;
            font-weight: 600;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


inject_css()
settings = load_settings()
clients = load_clients()
invoices = load_invoices()

logo_path = Path(settings.logo_path)
with st.container():
    col1, col2 = st.columns([1.4, 3])
    with col1:
        if logo_path.exists():
            st.image(str(logo_path), width=150)
    with col2:
        st.markdown(
            f"""
            <div class="hero-card">
                <div style="font-size:0.9rem; opacity:0.92; letter-spacing:0.04em;">DIGITAL INVOICING + PDF EXPORT + SHARE</div>
                <div style="font-size:2rem; font-weight:800; line-height:1.15; margin-top:0.2rem;">{settings.business_name} Invoice System</div>
                <div style="margin-top:0.4rem; font-size:1rem; opacity:0.94;">Professional invoices with letterhead, downloadable PDFs, and quick email or WhatsApp sharing.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

count_paid = sum(1 for inv in invoices if inv.status == "Paid")
outstanding = sum((inv.total for inv in invoices if inv.status in {"Draft", "Sent", "Overdue"}), Decimal("0.00"))
col_a, col_b, col_c = st.columns(3)
for col, title, value in [
    (col_a, "Invoices", str(len(invoices))),
    (col_b, "Paid", str(count_paid)),
    (col_c, "Outstanding", fmt_currency(outstanding, settings.currency_symbol)),
]:
    with col:
        st.markdown(
            f'<div class="metric-card"><div class="block-title">{title}</div><div class="block-value">{value}</div></div>',
            unsafe_allow_html=True,
        )


def client_lookup(name: str) -> Client | None:
    for c in clients:
        if c.name == name:
            return c
    return None


tab1, tab2, tab3, tab4 = st.tabs(["Create Invoice", "Invoice History", "Clients", "Settings"])

with tab1:
    st.subheader("Create invoice")

    defaults = make_example_invoice(settings)
    default_client_index = 0 if clients else None

    with st.form("invoice_form", clear_on_submit=False):
        left, right = st.columns([2, 1])
        with left:
            selected_client_name = st.selectbox(
                "Client",
                options=[c.name for c in clients] + ["Custom client"],
                index=default_client_index if default_client_index is not None else 0,
            )
            chosen_client = client_lookup(selected_client_name) if selected_client_name != "Custom client" else None
            bill_to_name = st.text_input("Bill to name", value=chosen_client.name if chosen_client else defaults.bill_to_name)
            bill_to_address = st.text_area(
                "Bill to address",
                value=chosen_client.address if chosen_client else defaults.bill_to_address,
                height=70,
            )
            bill_to_email = st.text_input("Client email", value=chosen_client.email if chosen_client else defaults.bill_to_email)
            bill_to_phone = st.text_input("Client phone", value=chosen_client.phone if chosen_client else "")
        with right:
            invoice_number = st.text_input("Invoice number", value=next_invoice_number(settings))
            issue_date = st.date_input("Issue date", value=date.today())
            due_date = st.date_input("Due date", value=date.today() + timedelta(days=settings.payment_terms_days))
            reference = st.text_input("Reference / PO", value=defaults.reference)
            status = st.selectbox("Status", ["Draft", "Sent", "Paid", "Overdue", "Cancelled"], index=0)
            vat_rate = st.number_input("VAT %", min_value=0.0, max_value=100.0, value=float(settings.vat_rate), step=0.5)

        st.markdown("### Line items")
        item_defaults = pd.DataFrame([
            {"Description": item.description, "Qty": float(item.qty), "Rate": float(item.rate)}
            for item in defaults.items
        ])
        item_df = st.data_editor(
            item_defaults,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Description": st.column_config.TextColumn(required=True, width="large"),
                "Qty": st.column_config.NumberColumn(min_value=0.0, step=1.0, format="%.2f"),
                "Rate": st.column_config.NumberColumn(min_value=0.0, step=100.0, format="%.2f"),
            },
            key="items_editor",
        )

        notes = st.text_area("Notes", value=defaults.notes, height=90)
        submitted = st.form_submit_button("Save invoice")

    items: list[InvoiceItem] = []
    for _, row in item_df.iterrows():
        desc = str(row.get("Description", "")).strip()
        qty = row.get("Qty", 0)
        rate = row.get("Rate", 0)
        if desc:
            items.append(InvoiceItem(desc, money(qty), money(rate)))

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

    preview1, preview2 = st.columns([1.5, 1])
    with preview1:
        st.markdown("### Invoice totals")
        st.write(f"**Subtotal:** {fmt_currency(live_invoice.subtotal, settings.currency_symbol)}")
        st.write(f"**VAT:** {fmt_currency(live_invoice.vat_amount, settings.currency_symbol)}")
        st.write(f"**Total:** {fmt_currency(live_invoice.total, settings.currency_symbol)}")
    with preview2:
        pdf_bytes = build_invoice_pdf(live_invoice, settings)
        st.download_button(
            "Download PDF",
            data=pdf_bytes,
            file_name=f"{live_invoice.invoice_number}_{bill_to_name.replace(' ', '_')}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    st.markdown("### Share options")
    st.markdown(
        f'<div class="share-row"><a href="{mailto_link(live_invoice, settings)}">Share by Email</a>'
        f'<a href="{whatsapp_link(live_invoice, settings)}" target="_blank">Share by WhatsApp</a></div>',
        unsafe_allow_html=True,
    )

    if submitted:
        save_invoice(live_invoice)
        st.success(f"Invoice {live_invoice.invoice_number} saved.")
        st.rerun()

with tab2:
    st.subheader("Invoice history")
    if not invoices:
        st.info("No invoices saved yet.")
    else:
        for inv in invoices:
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([2, 2, 2, 1.2])
                c1.markdown(f"**{inv.invoice_number}**")
                c2.write(inv.bill_to_name)
                c3.write(fmt_currency(inv.total, settings.currency_symbol))
                c4.write(inv.status)
                st.caption(f"Issued {inv.issue_date} • Due {inv.due_date} • Ref {inv.reference or '-'}")
                pdf_bytes = build_invoice_pdf(inv, settings)
                st.download_button(
                    f"Download {inv.invoice_number}",
                    data=pdf_bytes,
                    file_name=f"{inv.invoice_number}.pdf",
                    mime="application/pdf",
                    key=f"download_{inv.invoice_number}",
                )

with tab3:
    st.subheader("Client directory")
    client_rows = pd.DataFrame([c.__dict__ for c in clients])
    edited = st.data_editor(
        client_rows if not client_rows.empty else pd.DataFrame(columns=["name", "contact_person", "email", "phone", "address"]),
        num_rows="dynamic",
        use_container_width=True,
        key="clients_editor",
    )
    if st.button("Save clients"):
        cleaned = []
        for _, row in edited.iterrows():
            name = str(row.get("name", "")).strip()
            if name:
                cleaned.append(
                    Client(
                        name=name,
                        contact_person=str(row.get("contact_person", "")).strip(),
                        email=str(row.get("email", "")).strip(),
                        phone=str(row.get("phone", "")).strip(),
                        address=str(row.get("address", "")).strip(),
                    )
                )
        save_clients(cleaned)
        st.success("Clients saved.")
        st.rerun()

with tab4:
    st.subheader("Business settings")
    with st.form("settings_form"):
        a, b = st.columns(2)
        with a:
            business_name = st.text_input("Business name", value=settings.business_name)
            address_line_1 = st.text_input("Address line 1", value=settings.address_line_1)
            address_line_2 = st.text_input("Address line 2", value=settings.address_line_2)
            billing_email = st.text_input("Billing email", value=settings.billing_email)
            phone = st.text_input("Phone", value=settings.phone)
            logo_path_input = st.text_input("Logo path", value=settings.logo_path)
        with b:
            bank_name = st.text_input("Bank name", value=settings.bank_name)
            account_name = st.text_input("Account name", value=settings.account_name)
            account_number = st.text_input("Account number", value=settings.account_number)
            invoice_prefix = st.text_input("Invoice prefix", value=settings.invoice_prefix)
            vat_rate_settings = st.number_input("Default VAT %", min_value=0.0, max_value=100.0, value=float(settings.vat_rate))
            payment_terms_days = st.number_input("Payment terms (days)", min_value=0, max_value=120, value=int(settings.payment_terms_days))
        payment_note = st.text_input("Payment note", value=settings.payment_note)
        footer_tagline = st.text_input("Footer tagline", value=settings.footer_tagline)
        save_settings_btn = st.form_submit_button("Save settings")
    if save_settings_btn:
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
        )
        save_settings(updated)
        st.success("Settings saved.")
        st.rerun()
