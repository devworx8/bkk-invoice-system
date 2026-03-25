from pathlib import Path

from invoice_system import build_invoice_pdf, load_settings, make_example_invoice, save_invoice


def main() -> None:
    settings = load_settings()
    invoice = make_example_invoice(settings)
    out = Path(__file__).resolve().parent / "sample_invoice_khanyisa.pdf"
    build_invoice_pdf(invoice, settings, str(out))
    save_invoice(invoice)
    print(out)


if __name__ == "__main__":
    main()
