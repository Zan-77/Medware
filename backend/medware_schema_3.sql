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

-- Create Supplier table
CREATE TABLE Supplier (
    supplierId INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20)
);

-- Create Product table
CREATE TABLE Product (
    productId INT PRIMARY KEY AUTO_INCREMENT,
    wholePrice DECIMAL(10,2),
    retailPrice DECIMAL(10,2),
    name VARCHAR(100) NOT NULL,
    imageUrl VARCHAR(255)
);

-- Create Voucher table
CREATE TABLE Voucher (
    voucherId INT PRIMARY KEY AUTO_INCREMENT,
    value DECIMAL(10,2),
    date DATE,
    salesmanValue DECIMAL(10,2)
);

-- Create Archive table
CREATE TABLE Archive (
    archiveId INT PRIMARY KEY AUTO_INCREMENT,
    customerId INT,
    salesmanId INT,
    FOREIGN KEY (customerId) REFERENCES User(userId),
    FOREIGN KEY (salesmanId) REFERENCES User(userId)
);

-- Create Bill table
CREATE TABLE Bill (
    billId INT PRIMARY KEY AUTO_INCREMENT,
    supplierId INT,
    date DATE,
    FOREIGN KEY (supplierId) REFERENCES Supplier(supplierId)
);

-- Create ProductSupplier table
CREATE TABLE ProductSupplier (
    productSupplierId INT PRIMARY KEY AUTO_INCREMENT,
    productId INT,
    billId INT,
    category VARCHAR(50),
    quantity INT,
    discount DECIMAL(5,2),
    FOREIGN KEY (productId) REFERENCES Product(productId),
    FOREIGN KEY (billId) REFERENCES Bill(billId)
);

-- Create Order table
CREATE TABLE `Order` (
    orderId INT PRIMARY KEY AUTO_INCREMENT,
    archiveId INT,
    date DATE,
    packagingDate DATE,
    recieveDate DATE,
    salesmanRate DECIMAL(5,2),
    FOREIGN KEY (archiveId) REFERENCES Archive(archiveId)
);

-- Create OrderProduct table
CREATE TABLE OrderProduct (
    orderProductId INT PRIMARY KEY AUTO_INCREMENT,
    orderId INT,
    productId INT,
    quantity INT,
    sellPrice DECIMAL(10,2),
    returnQuantity INT,
    FOREIGN KEY (orderId) REFERENCES `Order`(orderId),
    FOREIGN KEY (productId) REFERENCES Product(productId)
);

-- Create OrderVoucher table
CREATE TABLE OrderVoucher (
    orderVoucherId INT PRIMARY KEY AUTO_INCREMENT,
    orderId INT,
    voucherId INT,
    FOREIGN KEY (orderId) REFERENCES `Order`(orderId),
    FOREIGN KEY (voucherId) REFERENCES Voucher(voucherId)
);