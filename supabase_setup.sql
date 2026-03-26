-- ============================================================
-- BKK Invoice System — Supabase Tables
-- Run this in your Supabase SQL Editor (Dashboard → SQL Editor)
-- ============================================================

-- 1. Invoices table
CREATE TABLE IF NOT EXISTS bkk_invoices (
    invoice_number TEXT PRIMARY KEY,
    issue_date     TEXT NOT NULL,
    due_date       TEXT NOT NULL,
    bill_to_name   TEXT NOT NULL,
    bill_to_address TEXT DEFAULT '',
    bill_to_email  TEXT DEFAULT '',
    bill_to_phone  TEXT DEFAULT '',
    reference      TEXT DEFAULT '',
    notes          TEXT DEFAULT '',
    status         TEXT DEFAULT 'Draft',
    items          JSONB DEFAULT '[]'::jsonb,
    vat_rate       NUMERIC DEFAULT 15.0,
    created_at     TIMESTAMPTZ DEFAULT now()
);

-- 2. Clients table
CREATE TABLE IF NOT EXISTS bkk_clients (
    name           TEXT PRIMARY KEY,
    contact_person TEXT DEFAULT '',
    email          TEXT DEFAULT '',
    phone          TEXT DEFAULT '',
    address        TEXT DEFAULT ''
);

-- 3. Settings table (single-row key/value)
CREATE TABLE IF NOT EXISTS bkk_settings (
    id    TEXT PRIMARY KEY DEFAULT 'default',
    data  JSONB NOT NULL
);

-- 4. Enable Row Level Security
ALTER TABLE bkk_invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE bkk_clients  ENABLE ROW LEVEL SECURITY;
ALTER TABLE bkk_settings ENABLE ROW LEVEL SECURITY;

-- 5. Policies — allow full access via anon key (internal app, no public users)
CREATE POLICY "Allow all on bkk_invoices" ON bkk_invoices
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Allow all on bkk_clients" ON bkk_clients
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Allow all on bkk_settings" ON bkk_settings
    FOR ALL USING (true) WITH CHECK (true);

-- 6. Insert default settings if table is empty
INSERT INTO bkk_settings (id, data)
VALUES ('default', '{}'::jsonb)
ON CONFLICT (id) DO NOTHING;

-- 7. Insert default client
INSERT INTO bkk_clients (name, email, phone, address)
VALUES (
    'Khanyisa Disability Centre',
    'accounts@khanyisadisability.org.za',
    '+27 12 000 0000',
    'Pretoria, South Africa'
)
ON CONFLICT (name) DO NOTHING;
