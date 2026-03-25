from __future__ import annotations

import io
import json
import os
from dataclasses import dataclass, asdict, field
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import List, Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import (
    Image,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"
ASSETS_DIR = APP_DIR / "assets"
SETTINGS_PATH = DATA_DIR / "settings.json"
CLIENTS_PATH = DATA_DIR / "clients.json"
INVOICES_PATH = DATA_DIR / "invoices.json"
LOGO_PATH = ASSETS_DIR / "bkk_logo.jpeg"


def money(value: Decimal | float | int | str) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def fmt_currency(value: Decimal | float | int | str, symbol: str = "R") -> str:
    amount = money(value)
    return f"{symbol}{amount:,.2f}"


@dataclass
class BusinessSettings:
    business_name: str = "BKK Innovation Hub"
    address_line_1: str = "323 Capefox Extension 21"
    address_line_2: str = "Nellmapius"
    billing_email: str = "billing@bkkinnovationhub.org.za"
    phone: str = "+27 63 793 7523"
    bank_name: str = "Capitec Business"
    account_name: str = "BKK Innovation Hub"
    account_number: str = "1053747152"
    currency_symbol: str = "R"
    vat_rate: float = 15.0
    invoice_prefix: str = "BKK-INV"
    payment_terms_days: int = 7
    payment_note: str = "Please use the invoice number as your payment reference."
    footer_tagline: str = "Empowering inclusive opportunities and youth innovation."
    logo_path: str = str(LOGO_PATH)


@dataclass
class Client:
    name: str
    contact_person: str = ""
    email: str = ""
    phone: str = ""
    address: str = ""


@dataclass
class InvoiceItem:
    description: str
    qty: Decimal
    rate: Decimal

    @property
    def amount(self) -> Decimal:
        return money(self.qty * self.rate)


@dataclass
class Invoice:
    invoice_number: str
    issue_date: str
    due_date: str
    bill_to_name: str
    bill_to_address: str
    bill_to_email: str = ""
    bill_to_phone: str = ""
    reference: str = ""
    notes: str = "Thank you for partnering with BKK Innovation Hub."
    status: str = "Draft"
    items: List[InvoiceItem] = field(default_factory=list)
    vat_rate: float = 15.0

    @property
    def subtotal(self) -> Decimal:
        return money(sum((item.amount for item in self.items), Decimal("0.00")))

    @property
    def vat_amount(self) -> Decimal:
        return money(self.subtotal * Decimal(str(self.vat_rate / 100)))

    @property
    def total(self) -> Decimal:
        return money(self.subtotal + self.vat_amount)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["items"] = [
            {
                "description": item.description,
                "qty": str(item.qty),
                "rate": str(item.rate),
            }
            for item in self.items
        ]
        data["subtotal"] = str(self.subtotal)
        data["vat_amount"] = str(self.vat_amount)
        data["total"] = str(self.total)
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Invoice":
        items = [
            InvoiceItem(
                description=item["description"],
                qty=money(item["qty"]),
                rate=money(item["rate"]),
            )
            for item in data.get("items", [])
        ]
        return cls(
            invoice_number=data["invoice_number"],
            issue_date=data["issue_date"],
            due_date=data["due_date"],
            bill_to_name=data["bill_to_name"],
            bill_to_address=data.get("bill_to_address", ""),
            bill_to_email=data.get("bill_to_email", ""),
            bill_to_phone=data.get("bill_to_phone", ""),
            reference=data.get("reference", ""),
            notes=data.get("notes", ""),
            status=data.get("status", "Draft"),
            items=items,
            vat_rate=float(data.get("vat_rate", 15.0)),
        )


DEFAULT_CLIENTS = [
    Client(
        name="Khanyisa Disability Centre",
        email="accounts@khanyisadisability.org.za",
        phone="+27 12 000 0000",
        address="Pretoria, South Africa",
    )
]


def ensure_data_files() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not SETTINGS_PATH.exists():
        SETTINGS_PATH.write_text(json.dumps(asdict(BusinessSettings()), indent=2))
    if not CLIENTS_PATH.exists():
        CLIENTS_PATH.write_text(json.dumps([asdict(c) for c in DEFAULT_CLIENTS], indent=2))
    if not INVOICES_PATH.exists():
        INVOICES_PATH.write_text("[]")



def load_settings() -> BusinessSettings:
    ensure_data_files()
    data = json.loads(SETTINGS_PATH.read_text())
    return BusinessSettings(**data)



def save_settings(settings: BusinessSettings) -> None:
    ensure_data_files()
    SETTINGS_PATH.write_text(json.dumps(asdict(settings), indent=2))



def load_clients() -> List[Client]:
    ensure_data_files()
    data = json.loads(CLIENTS_PATH.read_text())
    return [Client(**entry) for entry in data]



def save_clients(clients: List[Client]) -> None:
    ensure_data_files()
    CLIENTS_PATH.write_text(json.dumps([asdict(c) for c in clients], indent=2))



def load_invoices() -> List[Invoice]:
    ensure_data_files()
    data = json.loads(INVOICES_PATH.read_text())
    return [Invoice.from_dict(entry) for entry in data]



def save_invoice(invoice: Invoice) -> None:
    invoices = load_invoices()
    filtered = [i for i in invoices if i.invoice_number != invoice.invoice_number]
    filtered.insert(0, invoice)
    INVOICES_PATH.write_text(json.dumps([i.to_dict() for i in filtered], indent=2))



def next_invoice_number(settings: BusinessSettings) -> str:
    invoices = load_invoices()
    max_num = 0
    prefix = settings.invoice_prefix
    year = datetime.now().year
    for inv in invoices:
        if inv.invoice_number.startswith(f"{prefix}-{year}-"):
            try:
                num = int(inv.invoice_number.split("-")[-1])
                max_num = max(max_num, num)
            except ValueError:
                continue
    return f"{prefix}-{year}-{max_num + 1:03d}"



def make_example_invoice(settings: Optional[BusinessSettings] = None) -> Invoice:
    settings = settings or load_settings()
    today = date.today()
    invoice = Invoice(
        invoice_number=next_invoice_number(settings),
        issue_date=today.isoformat(),
        due_date=(today + timedelta(days=settings.payment_terms_days)).isoformat(),
        bill_to_name="Khanyisa Disability Centre",
        bill_to_address="Pretoria, South Africa",
        bill_to_email="accounts@khanyisadisability.org.za",
        reference="KD-BKK-PILOT-001",
        notes=(
            "Community support pricing has been applied for Khanyisa Disability Centre. "
            "This invoice reflects a heavily discounted rate in support of disability inclusion work."
        ),
        status="Draft",
        vat_rate=0.0,
        items=[
            InvoiceItem("Website design and page layout", money("1"), money("650")),
            InvoiceItem("Domain name purchase and setup", money("1"), money("350")),
            InvoiceItem("Backend integration and configuration", money("1"), money("1500")),
            InvoiceItem("Disability centre community support discount", money("1"), money("-1000")),
        ],
    )
    return invoice



def _styles():
    styles = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "title",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=24,
            textColor=colors.HexColor("#173C65"),
            spaceAfter=6,
            alignment=TA_RIGHT,
        ),
        "normal": ParagraphStyle(
            "normal",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor("#1B2430"),
        ),
        "small": ParagraphStyle(
            "small",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#425466"),
        ),
        "section": ParagraphStyle(
            "section",
            parent=styles["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=colors.white,
            backColor=colors.HexColor("#173C65"),
            leftIndent=6,
            rightIndent=6,
            borderPadding=(4, 4, 4),
            spaceBefore=6,
            spaceAfter=6,
        ),
        "meta_label": ParagraphStyle(
            "meta_label",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=8,
            textColor=colors.HexColor("#5B6B7A"),
        ),
        "meta_value": ParagraphStyle(
            "meta_value",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=colors.HexColor("#102A43"),
        ),
        "body_bold": ParagraphStyle(
            "body_bold",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor("#102A43"),
        ),
        "table_head": ParagraphStyle(
            "table_head",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=9.2,
            leading=12,
            textColor=colors.white,
        ),
    }



def _top_band(canvas, doc):
    width, height = A4
    canvas.saveState()
    canvas.setFillColor(colors.HexColor("#173C65"))
    canvas.rect(0, height - 18 * mm, width, 18 * mm, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor("#0F766E"))
    canvas.rect(0, height - 20 * mm, width * 0.68, 2 * mm, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor("#E77728"))
    canvas.rect(width * 0.68, height - 20 * mm, width * 0.32, 2 * mm, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor("#173C65"))
    canvas.rect(0, 0, width, 9 * mm, fill=1, stroke=0)
    canvas.restoreState()



def build_invoice_pdf(invoice: Invoice, settings: BusinessSettings, output_path: Optional[str] = None) -> bytes:
    styles = _styles()
    buffer = io.BytesIO()
    target = output_path or buffer

    doc = SimpleDocTemplate(
        target,
        pagesize=A4,
        leftMargin=17 * mm,
        rightMargin=17 * mm,
        topMargin=28 * mm,
        bottomMargin=18 * mm,
        title=f"Invoice {invoice.invoice_number}",
    )

    story = []

    # Header layout
    business_details = [
        Paragraph(f"<b>{settings.business_name}</b>", styles["body_bold"]),
        Paragraph(settings.address_line_1, styles["normal"]),
        Paragraph(settings.address_line_2, styles["normal"]),
        Paragraph(settings.billing_email, styles["normal"]),
        Paragraph(settings.phone, styles["normal"]),
    ]
    if Path(settings.logo_path).exists():
        left_header = Table([[Image(settings.logo_path, width=28 * mm, height=38 * mm), business_details]], colWidths=[32 * mm, 63 * mm])
        left_header.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0,0), (-1,-1), 0), ("RIGHTPADDING", (0,0), (-1,-1), 0)]))
    else:
        left_header = Table([[business_details]], colWidths=[95 * mm])
        left_header.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0,0), (-1,-1), 0), ("RIGHTPADDING", (0,0), (-1,-1), 0)]))

    meta_table = Table(
        [
            [Paragraph("Invoice Number", styles["meta_label"]), Paragraph(invoice.invoice_number, styles["meta_value"])],
            [Paragraph("Issue Date", styles["meta_label"]), Paragraph(invoice.issue_date, styles["meta_value"])],
            [Paragraph("Due Date", styles["meta_label"]), Paragraph(invoice.due_date, styles["meta_value"])],
            [Paragraph("Reference", styles["meta_label"]), Paragraph(invoice.reference or "-", styles["meta_value"])],
            [Paragraph("Status", styles["meta_label"]), Paragraph(invoice.status, styles["meta_value"])],
        ],
        colWidths=[28 * mm, 40 * mm],
        hAlign="RIGHT",
    )
    meta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7FAFC")),
                ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#D9E2EC")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5EDF5")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    right_header = Table([[Paragraph("INVOICE", styles["title"])] , [Spacer(1, 2 * mm)], [meta_table]], colWidths=[73 * mm])
    right_header.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0,0), (-1,-1), 0), ("RIGHTPADDING", (0,0), (-1,-1), 0)]))

    header = Table(
        [[left_header, right_header]],
        colWidths=[95 * mm, 73 * mm],
    )
    header.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(header)
    story.append(Spacer(1, 6 * mm))

    # Bill to section
    story.append(Paragraph("Bill To", styles["section"]))
    bill_to_lines = [
        f"<b>{invoice.bill_to_name}</b>",
        invoice.bill_to_address,
    ]
    if invoice.bill_to_email:
        bill_to_lines.append(invoice.bill_to_email)
    if invoice.bill_to_phone:
        bill_to_lines.append(invoice.bill_to_phone)
    story.append(Paragraph("<br/>".join([line for line in bill_to_lines if line]), styles["normal"]))
    story.append(Spacer(1, 5 * mm))

    # Items table
    story.append(Paragraph("Invoice Items", styles["section"]))
    item_rows = [[
        Paragraph("#", styles["table_head"]),
        Paragraph("Description", styles["table_head"]),
        Paragraph("Qty", styles["table_head"]),
        Paragraph("Rate", styles["table_head"]),
        Paragraph("Amount", styles["table_head"]),
    ]]
    for index, item in enumerate(invoice.items, start=1):
        item_rows.append([
            Paragraph(str(index), styles["normal"]),
            Paragraph(item.description, styles["normal"]),
            Paragraph(f"{item.qty}", styles["normal"]),
            Paragraph(fmt_currency(item.rate, settings.currency_symbol), styles["normal"]),
            Paragraph(fmt_currency(item.amount, settings.currency_symbol), styles["normal"]),
        ])

    items_table = Table(
        item_rows,
        colWidths=[10 * mm, 88 * mm, 18 * mm, 28 * mm, 30 * mm],
        repeatRows=1,
    )
    items_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#173C65")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("LINEBELOW", (0, 0), (-1, 0), 0.8, colors.HexColor("#173C65")),
                ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#D9E2EC")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5EDF5")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FAFCFE")]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (0, -1), "CENTER"),
                ("ALIGN", (2, 1), (2, -1), "CENTER"),
                ("ALIGN", (3, 1), (4, -1), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(items_table)
    story.append(Spacer(1, 6 * mm))

    # Summary + bank details side by side
    bank_box = Table(
        [[Paragraph(
            f"<b>Bank:</b> {settings.bank_name}<br/>"
            f"<b>Account Name:</b> {settings.account_name}<br/>"
            f"<b>Account Number:</b> {settings.account_number}<br/>"
            f"<b>Payment Terms:</b> {settings.payment_terms_days} days<br/>"
            f"<b>Payment Note:</b> {settings.payment_note}",
            styles["normal"],
        )]],
        colWidths=[86 * mm],
    )
    bank_box.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7FAFC")),
            ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#D9E2EC")),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ])
    )

    summary_rows = [
        [Paragraph("Subtotal", styles["normal"]), Paragraph(fmt_currency(invoice.subtotal, settings.currency_symbol), styles["body_bold"])],
        [Paragraph(f"VAT ({invoice.vat_rate:.0f}%)", styles["normal"]), Paragraph(fmt_currency(invoice.vat_amount, settings.currency_symbol), styles["body_bold"])],
        [Paragraph("TOTAL DUE", styles["body_bold"]), Paragraph(fmt_currency(invoice.total, settings.currency_symbol), styles["body_bold"])],
    ]
    summary_box = Table(summary_rows, colWidths=[30 * mm, 36 * mm])
    summary_box.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -2), colors.HexColor("#F7FAFC")),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#FFF3E8")),
            ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#D9E2EC")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5EDF5")),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ])
    )

    summary_table = Table([[bank_box, summary_box]], colWidths=[92 * mm, 66 * mm])
    summary_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(summary_table)
    story.append(Spacer(1, 5 * mm))

    story.append(Paragraph("Notes", styles["section"]))
    story.append(Paragraph(invoice.notes, styles["normal"]))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(settings.footer_tagline, styles["small"]))

    doc.build(story, onFirstPage=_top_band, onLaterPages=_top_band)

    if output_path:
        return Path(output_path).read_bytes()
    return buffer.getvalue()



def mailto_link(invoice: Invoice, settings: BusinessSettings) -> str:
    subject = f"Invoice {invoice.invoice_number} from {settings.business_name}"
    body = (
        f"Dear {invoice.bill_to_name},\n\n"
        f"Please find attached invoice {invoice.invoice_number} for {fmt_currency(invoice.total, settings.currency_symbol)}.\n"
        f"Due date: {invoice.due_date}.\n\n"
        f"Kind regards,\n{settings.business_name}"
    )
    from urllib.parse import quote

    return f"mailto:{invoice.bill_to_email}?subject={quote(subject)}&body={quote(body)}"



def whatsapp_link(invoice: Invoice, settings: BusinessSettings) -> str:
    from urllib.parse import quote

    message = (
        f"Hello {invoice.bill_to_name}, invoice {invoice.invoice_number} from {settings.business_name} "
        f"for {fmt_currency(invoice.total, settings.currency_symbol)} is ready. Due date: {invoice.due_date}."
    )
    return f"https://wa.me/?text={quote(message)}"
