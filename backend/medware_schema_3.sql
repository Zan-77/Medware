-- ============================================================
--  MedWare Database Schema — PostgreSQL DDL
--  Generated from medware_erd_v4.drawio
--  30 tables across 8 modules
-- ============================================================

-- Drop order respects FK dependencies (deepest children first)
-- Uncomment if you need to reset:
-- DROP TABLE IF EXISTS ... CASCADE;

-- ============================================================
-- EXTENSIONS
-- ============================================================
CREATE EXTENSION IF NOT EXISTS "pgcrypto";  -- for gen_random_uuid()


-- ============================================================
-- MODULE: Auth & Users
-- ============================================================

CREATE TABLE "user" (
    id                  TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    username            TEXT        NOT NULL UNIQUE,
    email               TEXT        NOT NULL UNIQUE,
    password_hash       TEXT        NOT NULL,
    role                TEXT        NOT NULL,          -- e.g. 'admin','salesman','customer','b2b_partner'
    phone               TEXT,
    area                TEXT,
    is_active           BOOLEAN     NOT NULL DEFAULT TRUE,
    user_version        INTEGER     NOT NULL DEFAULT 0, -- optimistic-lock counter
    lockout_until       TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE token_blacklist (
    id              TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    user_id         TEXT        NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    jti             TEXT        NOT NULL UNIQUE,       -- JWT ID claim
    invalidated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at      TIMESTAMPTZ NOT NULL
);

CREATE TABLE notification (
    id              TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    recipient_id    TEXT        NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    type            TEXT        NOT NULL,
    ref_id          TEXT,                              -- polymorphic reference
    ref_type        TEXT,                              -- e.g. 'order','return_request'
    message         TEXT        NOT NULL,
    is_read         BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE salesman_commission_rate (
    id              TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    salesman_id     TEXT        NOT NULL,              -- FK added after SALESMAN table
    commission_pct  NUMERIC(6,4) NOT NULL,
    valid_from      TIMESTAMPTZ NOT NULL,
    valid_until     TIMESTAMPTZ,
    is_active       BOOLEAN     NOT NULL DEFAULT TRUE,
    set_by          TEXT        REFERENCES "user"(id) ON DELETE SET NULL
);


-- ============================================================
-- MODULE: Customers
-- ============================================================

CREATE TABLE customer (
    id              TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    user_id         TEXT        NOT NULL UNIQUE REFERENCES "user"(id) ON DELETE CASCADE,
    salesman_id     TEXT,                              -- FK added after SALESMAN
    company_name    TEXT,
    address         TEXT,
    area            TEXT,
    credit_limit    NUMERIC(14,2) NOT NULL DEFAULT 0,
    total_debt_syp  NUMERIC(14,2) NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE customer_salesman_history (
    id              TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    customer_id     TEXT        NOT NULL REFERENCES customer(id) ON DELETE CASCADE,
    salesman_id     TEXT        NOT NULL,              -- FK added after SALESMAN
    reason          TEXT,
    assigned_from   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    assigned_until  TIMESTAMPTZ,
    assigned_by     TEXT        REFERENCES "user"(id) ON DELETE SET NULL,
    notes           TEXT
);

CREATE TABLE customer_debt_transaction (
    id                  TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    customer_id         TEXT        NOT NULL REFERENCES customer(id) ON DELETE CASCADE,
    transaction_type    TEXT        NOT NULL,          -- 'charge','payment','adjustment','return_refund'
    amount_syp          NUMERIC(14,2) NOT NULL,
    balance_before_syp  NUMERIC(14,2) NOT NULL,
    balance_after_syp   NUMERIC(14,2) NOT NULL,
    reference_id        TEXT,                          -- polymorphic: order_id, voucher_id, etc.
    reference_type      TEXT,
    logged_by           TEXT        REFERENCES "user"(id) ON DELETE SET NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    note                TEXT
);

CREATE TABLE cart (
    id              TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    customer_id     TEXT        NOT NULL REFERENCES customer(id) ON DELETE CASCADE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE cart_item (
    id              TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    cart_id         TEXT        NOT NULL REFERENCES cart(id) ON DELETE CASCADE,
    product_id      TEXT        NOT NULL,              -- FK added after PRODUCT
    quantity        INTEGER     NOT NULL CHECK (quantity > 0),
    unit_price_syp  NUMERIC(14,2) NOT NULL
);


-- ============================================================
-- MODULE: Suppliers
-- ============================================================

CREATE TABLE supplier (
    id                  TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    name                TEXT        NOT NULL,
    phone               TEXT,
    country             TEXT,
    currency            TEXT,
    supplies_exclusive  BOOLEAN     NOT NULL DEFAULT FALSE,
    supplies_standard   BOOLEAN     NOT NULL DEFAULT TRUE
);

CREATE TABLE category (
    id              TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    supplier_id     TEXT        REFERENCES supplier(id) ON DELETE SET NULL,
    name            TEXT        NOT NULL,
    profit_model    TEXT,                              -- e.g. 'margin','fixed','tiered'
    description     TEXT
);

CREATE TABLE exclusive_agreement (
    id              TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    supplier_id     TEXT        NOT NULL REFERENCES supplier(id) ON DELETE CASCADE,
    category_id     TEXT        NOT NULL REFERENCES category(id) ON DELETE CASCADE,
    our_discount_pct    NUMERIC(6,4),
    valid_from      TIMESTAMPTZ NOT NULL,
    valid_until     TIMESTAMPTZ,
    is_active       BOOLEAN     NOT NULL DEFAULT TRUE,
    notes           TEXT
);


-- ============================================================
-- MODULE: Products
-- ============================================================

CREATE TABLE product (
    id                  TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    supplier_id         TEXT        REFERENCES supplier(id) ON DELETE SET NULL,
    category_id         TEXT        REFERENCES category(id) ON DELETE SET NULL,
    name                TEXT        NOT NULL,
    profit_model        TEXT,
    cost_usd            NUMERIC(14,4),
    margin_pct          NUMERIC(6,4),
    advised_price_syp   NUMERIC(14,2),
    sell_price_syp      NUMERIC(14,2),
    qty_on_hand         INTEGER     NOT NULL DEFAULT 0,
    low_stock_threshold INTEGER     NOT NULL DEFAULT 0,
    expiry_date         DATE,
    batch_number        TEXT,
    image_url           TEXT,
    is_active           BOOLEAN     NOT NULL DEFAULT TRUE,
    deactivated_at      TIMESTAMPTZ,
    deactivated_by      TEXT        REFERENCES "user"(id) ON DELETE SET NULL
);

CREATE TABLE product_price_history (
    id              TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    product_id      TEXT        NOT NULL REFERENCES product(id) ON DELETE CASCADE,
    cost_usd        NUMERIC(14,4),
    margin_pct      NUMERIC(6,4),
    sell_price_syp  NUMERIC(14,2),
    advised_price_syp NUMERIC(14,2),
    fx_rate_at_time NUMERIC(14,4),
    valid_from      TIMESTAMPTZ NOT NULL,
    valid_until     TIMESTAMPTZ,
    changed_by      TEXT        REFERENCES "user"(id) ON DELETE SET NULL
);

CREATE TABLE supplier_price (
    id                  TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    supplier_id         TEXT        NOT NULL REFERENCES supplier(id) ON DELETE CASCADE,
    product_id          TEXT        NOT NULL REFERENCES product(id) ON DELETE CASCADE,
    category_id         TEXT        REFERENCES category(id) ON DELETE SET NULL,
    our_discount_pct    NUMERIC(6,4),
    valid_from          TIMESTAMPTZ NOT NULL,
    valid_until         TIMESTAMPTZ,
    is_active           BOOLEAN     NOT NULL DEFAULT TRUE,
    notes               TEXT
);

CREATE TABLE discount (
    id              TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    product_id      TEXT        NOT NULL REFERENCES product(id) ON DELETE CASCADE,
    discount_type   TEXT        NOT NULL,              -- 'percentage','fixed','buy_x_get_y'
    value           NUMERIC(14,4) NOT NULL,
    valid_from      TIMESTAMPTZ NOT NULL,
    valid_until     TIMESTAMPTZ,
    store_only      BOOLEAN     NOT NULL DEFAULT FALSE
);

CREATE TABLE stock_movement (
    id              TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    product_id      TEXT        NOT NULL REFERENCES product(id) ON DELETE CASCADE,
    movement_type   TEXT        NOT NULL,              -- 'in','out','adjustment','return'
    quantity        INTEGER     NOT NULL,
    reference_id    TEXT,
    reference_type  TEXT,
    performed_by    TEXT        REFERENCES "user"(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    notes           TEXT
);

CREATE TABLE product_review (
    id                  TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    product_id          TEXT        NOT NULL REFERENCES product(id) ON DELETE CASCADE,
    customer_id         TEXT        NOT NULL REFERENCES customer(id) ON DELETE CASCADE,
    rating              SMALLINT    NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment             TEXT,
    is_verified_purchase BOOLEAN    NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ============================================================
-- MODULE: Orders
-- ============================================================

CREATE TABLE salesman (
    id              TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    user_id         TEXT        NOT NULL UNIQUE REFERENCES "user"(id) ON DELETE CASCADE,
    name            TEXT        NOT NULL,
    area            TEXT,
    is_active       BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Back-fill FK references that depend on SALESMAN
ALTER TABLE salesman_commission_rate
    ADD CONSTRAINT fk_scr_salesman FOREIGN KEY (salesman_id) REFERENCES salesman(id) ON DELETE CASCADE;

ALTER TABLE customer
    ADD CONSTRAINT fk_customer_salesman FOREIGN KEY (salesman_id) REFERENCES salesman(id) ON DELETE SET NULL;

ALTER TABLE customer_salesman_history
    ADD CONSTRAINT fk_csh_salesman FOREIGN KEY (salesman_id) REFERENCES salesman(id) ON DELETE CASCADE;

CREATE TABLE shipping_method (
    id              TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    name            TEXT        NOT NULL,
    base_cost_syp   NUMERIC(14,2) NOT NULL DEFAULT 0,
    estimated_days  INTEGER,
    is_active       BOOLEAN     NOT NULL DEFAULT TRUE
);

CREATE TABLE "order" (
    id                  TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    customer_id         TEXT        NOT NULL REFERENCES customer(id) ON DELETE RESTRICT,
    salesman_id         TEXT        REFERENCES salesman(id) ON DELETE SET NULL,
    cart_id             TEXT        REFERENCES cart(id) ON DELETE SET NULL,
    source              TEXT,                          -- 'app','salesman','web'
    status              TEXT        NOT NULL DEFAULT 'pending',
    fx_rate_locked      NUMERIC(14,4),
    subtotal_syp        NUMERIC(14,2) NOT NULL DEFAULT 0,
    discount_total_syp  NUMERIC(14,2) NOT NULL DEFAULT 0,
    shipping_cost_syp   NUMERIC(14,2) NOT NULL DEFAULT 0,
    total_syp           NUMERIC(14,2) NOT NULL DEFAULT 0,
    outstanding_syp     NUMERIC(14,2) NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    confirmed_at        TIMESTAMPTZ,
    dispatched_at       TIMESTAMPTZ,
    delivered_at        TIMESTAMPTZ
);

CREATE TABLE order_item (
    id              TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    order_id        TEXT        NOT NULL REFERENCES "order"(id) ON DELETE CASCADE,
    product_id      TEXT        NOT NULL REFERENCES product(id) ON DELETE RESTRICT,
    quantity        INTEGER     NOT NULL CHECK (quantity > 0),
    unit_price_syp  NUMERIC(14,2) NOT NULL,
    discount_pct    NUMERIC(6,4) NOT NULL DEFAULT 0,
    line_total_syp  NUMERIC(14,2) NOT NULL
);

CREATE TABLE commission_rate (
    id                  TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    salesman_id         TEXT        NOT NULL REFERENCES salesman(id) ON DELETE CASCADE,
    min_collection_pct  NUMERIC(6,4) NOT NULL DEFAULT 0,
    commission_pct      NUMERIC(6,4) NOT NULL,
    valid_from          TIMESTAMPTZ NOT NULL,
    valid_until         TIMESTAMPTZ,
    is_active           BOOLEAN     NOT NULL DEFAULT TRUE
);

CREATE TABLE order_commission_record (
    id                      TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    order_id                TEXT        NOT NULL REFERENCES "order"(id) ON DELETE CASCADE,
    salesman_id             TEXT        NOT NULL REFERENCES salesman(id) ON DELETE RESTRICT,
    commission_rate_id      TEXT        REFERENCES commission_rate(id) ON DELETE SET NULL,
    order_total_syp         NUMERIC(14,2) NOT NULL,
    collected_syp           NUMERIC(14,2) NOT NULL DEFAULT 0,
    commission_earned_syp   NUMERIC(14,2) NOT NULL DEFAULT 0,
    clawback_syp            NUMERIC(14,2) NOT NULL DEFAULT 0,
    net_commission_syp      NUMERIC(14,2) NOT NULL DEFAULT 0,
    status                  TEXT        NOT NULL DEFAULT 'pending', -- 'pending','partial','settled','clawed_back'
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE stock_issue_report (
    id              TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    product_id      TEXT        NOT NULL REFERENCES product(id) ON DELETE CASCADE,
    reported_by     TEXT        REFERENCES "user"(id) ON DELETE SET NULL,
    issue_type      TEXT        NOT NULL,
    quantity        INTEGER,
    note            TEXT,
    reported_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at     TIMESTAMPTZ
);


-- ============================================================
-- MODULE: Payments & Returns
-- ============================================================

CREATE TABLE payment_voucher (
    id                  TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    order_id            TEXT        NOT NULL REFERENCES "order"(id) ON DELETE RESTRICT,
    customer_id         TEXT        NOT NULL REFERENCES customer(id) ON DELETE RESTRICT,
    logged_by           TEXT        REFERENCES "user"(id) ON DELETE SET NULL,
    voucher_number      TEXT        NOT NULL UNIQUE,
    amount_syp          NUMERIC(14,2) NOT NULL,
    clears_full_balance BOOLEAN     NOT NULL DEFAULT FALSE,
    payment_date        DATE        NOT NULL,
    method              TEXT        NOT NULL,          -- 'cash','bank_transfer','cheque'
    note                TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE voucher_commission_update (
    id                          TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    voucher_id                  TEXT        NOT NULL REFERENCES payment_voucher(id) ON DELETE CASCADE,
    order_commission_record_id  TEXT        NOT NULL REFERENCES order_commission_record(id) ON DELETE CASCADE,
    amount_applied_syp          NUMERIC(14,2) NOT NULL,
    commission_increment_syp    NUMERIC(14,2) NOT NULL DEFAULT 0,
    created_at                  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE return_request (
    id                      TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    order_id                TEXT        NOT NULL REFERENCES "order"(id) ON DELETE RESTRICT,
    customer_id             TEXT        NOT NULL REFERENCES customer(id) ON DELETE RESTRICT,
    handled_by              TEXT        REFERENCES "user"(id) ON DELETE SET NULL,
    reason                  TEXT,
    status                  TEXT        NOT NULL DEFAULT 'pending',
    total_refund_syp        NUMERIC(14,2) NOT NULL DEFAULT 0,
    restocked_value_syp     NUMERIC(14,2) NOT NULL DEFAULT 0,
    requested_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    resolved_at             TIMESTAMPTZ
);

CREATE TABLE return_item (
    id                  TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    return_request_id   TEXT        NOT NULL REFERENCES return_request(id) ON DELETE CASCADE,
    order_item_id       TEXT        NOT NULL REFERENCES order_item(id) ON DELETE RESTRICT,
    product_id          TEXT        NOT NULL REFERENCES product(id) ON DELETE RESTRICT,
    quantity_returned   INTEGER     NOT NULL CHECK (quantity_returned > 0),
    unit_price_syp      NUMERIC(14,2) NOT NULL,
    line_refund_syp     NUMERIC(14,2) NOT NULL,
    condition           TEXT                           -- 'resalable','damaged','expired'
);


-- ============================================================
-- MODULE: B2B
-- ============================================================

CREATE TABLE b2b_partner (
    id              TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    user_id         TEXT        NOT NULL UNIQUE REFERENCES "user"(id) ON DELETE CASCADE,
    company_name    TEXT        NOT NULL,
    address         TEXT,
    area            TEXT,
    credit_limit    NUMERIC(14,2) NOT NULL DEFAULT 0,
    total_debt_syp  NUMERIC(14,2) NOT NULL DEFAULT 0,
    is_active       BOOLEAN     NOT NULL DEFAULT TRUE
);

CREATE TABLE b2b_partner_debt_transaction (
    id                  TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    partner_id          TEXT        NOT NULL REFERENCES b2b_partner(id) ON DELETE CASCADE,
    transaction_type    TEXT        NOT NULL,
    amount_syp          NUMERIC(14,2) NOT NULL,
    balance_before_syp  NUMERIC(14,2) NOT NULL,
    balance_after_syp   NUMERIC(14,2) NOT NULL,
    reference_id        TEXT,
    reference_type      TEXT,
    logged_by           TEXT        REFERENCES "user"(id) ON DELETE SET NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    note                TEXT
);

CREATE TABLE b2b_pricing_tier (
    id                      TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    partner_id              TEXT        NOT NULL REFERENCES b2b_partner(id) ON DELETE CASCADE,
    agreement_id            TEXT        REFERENCES exclusive_agreement(id) ON DELETE SET NULL,
    category_id             TEXT        REFERENCES category(id) ON DELETE SET NULL,
    partner_discount_pct    NUMERIC(6,4) NOT NULL DEFAULT 0,
    our_net_margin_pct      NUMERIC(6,4),
    valid_from              TIMESTAMPTZ NOT NULL,
    valid_until             TIMESTAMPTZ,
    is_active               BOOLEAN     NOT NULL DEFAULT TRUE
);

CREATE TABLE b2b_order (
    id                          TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    partner_id                  TEXT        NOT NULL REFERENCES b2b_partner(id) ON DELETE RESTRICT,
    handled_by                  TEXT        REFERENCES "user"(id) ON DELETE SET NULL,
    status                      TEXT        NOT NULL DEFAULT 'pending',
    fx_rate_locked              NUMERIC(14,4),
    subtotal_syp                NUMERIC(14,2) NOT NULL DEFAULT 0,
    partner_discount_syp        NUMERIC(14,2) NOT NULL DEFAULT 0,
    total_syp                   NUMERIC(14,2) NOT NULL DEFAULT 0,
    outstanding_syp             NUMERIC(14,2) NOT NULL DEFAULT 0,
    partner_balance_snapshot_syp NUMERIC(14,2),
    notes                       TEXT,
    created_at                  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    confirmed_at                TIMESTAMPTZ,
    dispatched_at               TIMESTAMPTZ
);

CREATE TABLE b2b_order_item (
    id                      TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    b2b_order_id            TEXT        NOT NULL REFERENCES b2b_order(id) ON DELETE CASCADE,
    product_id              TEXT        NOT NULL REFERENCES product(id) ON DELETE RESTRICT,
    pricing_tier_id         TEXT        REFERENCES b2b_pricing_tier(id) ON DELETE SET NULL,
    quantity                INTEGER     NOT NULL CHECK (quantity > 0),
    advised_price_syp       NUMERIC(14,2),
    partner_discount_pct    NUMERIC(6,4) NOT NULL DEFAULT 0,
    partner_price_syp       NUMERIC(14,2) NOT NULL,
    our_margin_pct          NUMERIC(6,4),
    our_margin_syp          NUMERIC(14,2),
    line_total_syp          NUMERIC(14,2) NOT NULL
);

CREATE TABLE b2b_payment_voucher (
    id                  TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    partner_id          TEXT        NOT NULL REFERENCES b2b_partner(id) ON DELETE RESTRICT,
    logged_by           TEXT        REFERENCES "user"(id) ON DELETE SET NULL,
    voucher_number      TEXT        NOT NULL UNIQUE,
    amount_syp          NUMERIC(14,2) NOT NULL,
    clears_full_balance BOOLEAN     NOT NULL DEFAULT FALSE,
    payment_date        DATE        NOT NULL,
    method              TEXT        NOT NULL,
    note                TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ============================================================
-- MODULE: Currency
-- ============================================================

CREATE TABLE currency (
    id      TEXT    PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    code    TEXT    NOT NULL UNIQUE,                   -- 'SYP','USD','EUR'
    name    TEXT    NOT NULL
);

CREATE TABLE exchange_rate (
    id              TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    from_currency_id TEXT       NOT NULL REFERENCES currency(id) ON DELETE CASCADE,
    to_currency_id   TEXT       NOT NULL REFERENCES currency(id) ON DELETE CASCADE,
    rate            NUMERIC(18,6) NOT NULL,
    effective_date  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Back-fill FK on cart_item now that product exists
ALTER TABLE cart_item
    ADD CONSTRAINT fk_cart_item_product FOREIGN KEY (product_id) REFERENCES product(id) ON DELETE CASCADE;


-- ============================================================
-- INDEXES  (covering the most common query patterns)
-- ============================================================

-- Auth
CREATE INDEX idx_token_blacklist_user   ON token_blacklist(user_id);
CREATE INDEX idx_token_blacklist_jti    ON token_blacklist(jti);
CREATE INDEX idx_notification_recipient ON notification(recipient_id, is_read);

-- Customers
CREATE INDEX idx_customer_user          ON customer(user_id);
CREATE INDEX idx_customer_salesman      ON customer(salesman_id);
CREATE INDEX idx_cst_salesman_hist      ON customer_salesman_history(customer_id, salesman_id);
CREATE INDEX idx_cdt_customer           ON customer_debt_transaction(customer_id, created_at DESC);
CREATE INDEX idx_cart_customer          ON cart(customer_id);

-- Products
CREATE INDEX idx_product_supplier       ON product(supplier_id);
CREATE INDEX idx_product_category       ON product(category_id);
CREATE INDEX idx_product_active         ON product(is_active);
CREATE INDEX idx_discount_product       ON discount(product_id, valid_from, valid_until);
CREATE INDEX idx_stock_movement_product ON stock_movement(product_id, created_at DESC);
CREATE INDEX idx_review_product         ON product_review(product_id);
CREATE INDEX idx_supplier_price_sup     ON supplier_price(supplier_id, product_id, is_active);

-- Orders
CREATE INDEX idx_order_customer         ON "order"(customer_id);
CREATE INDEX idx_order_salesman         ON "order"(salesman_id);
CREATE INDEX idx_order_status           ON "order"(status);
CREATE INDEX idx_order_item_order       ON order_item(order_id);
CREATE INDEX idx_order_item_product     ON order_item(product_id);
CREATE INDEX idx_commission_salesman    ON order_commission_record(salesman_id, status);
CREATE INDEX idx_commission_order       ON order_commission_record(order_id);

-- Payments & Returns
CREATE INDEX idx_voucher_order          ON payment_voucher(order_id);
CREATE INDEX idx_voucher_customer       ON payment_voucher(customer_id);
CREATE INDEX idx_vcu_voucher            ON voucher_commission_update(voucher_id);
CREATE INDEX idx_return_req_order       ON return_request(order_id);
CREATE INDEX idx_return_req_customer    ON return_request(customer_id);
CREATE INDEX idx_return_item_request    ON return_item(return_request_id);

-- B2B
CREATE INDEX idx_b2b_order_partner      ON b2b_order(partner_id);
CREATE INDEX idx_b2b_order_status       ON b2b_order(status);
CREATE INDEX idx_b2b_order_item_order   ON b2b_order_item(b2b_order_id);
CREATE INDEX idx_b2b_order_item_product ON b2b_order_item(product_id);
CREATE INDEX idx_b2b_pdt_partner        ON b2b_partner_debt_transaction(partner_id, created_at DESC);
CREATE INDEX idx_b2b_voucher_partner    ON b2b_payment_voucher(partner_id);

-- Currency
CREATE INDEX idx_exchange_rate_pair     ON exchange_rate(from_currency_id, to_currency_id, effective_date DESC);


-- ============================================================
-- SEED: base currencies
-- ============================================================
INSERT INTO currency (id, code, name) VALUES
    (gen_random_uuid()::TEXT, 'SYP', 'Syrian Pound'),
    (gen_random_uuid()::TEXT, 'USD', 'US Dollar'),
    (gen_random_uuid()::TEXT, 'EUR', 'Euro');
