# Fourth Year Project Backend API Documentation

## Overview

This backend exposes REST API endpoints for user role management and product/supply chain operations. All endpoints are mounted under `/api/`.

NOTE: Authentication is required for all endpoints. The current backend uses Django authentication and role-based permissions. If your frontend uses session authentication, ensure the user's session is established before calling protected endpoints.

## Base URL

- `http://<HOST>:<PORT>/api/`

## Users / Role Endpoints

### Current user

- `GET /api/users/me/`
  - Returns current authenticated user details.
  - Response fields: `id`, `username`, `email`, `role`, `role_display`, `is_staff`, `is_superuser`.

### Authentication

- `POST /api/auth/register/`
  - Registers a new user and returns JWT `access` and `refresh` tokens.
  - Required request fields: `username`, `email`, `password`, `password2`, `role`.

- `POST /api/auth/token/`
  - Returns JWT tokens for existing users.
  - Required request fields: `username`, `password`.

- `POST /api/auth/token/refresh/`
  - Returns a new `access` token for a valid `refresh` token.
  - Required request field: `refresh`.

### Available roles

- `GET /api/users/roles/`
  - Returns all available user roles.
  - Response: `roles` array with `key` and `label`.

### Role access checks

- `GET /api/users/access/manager/`
- `GET /api/users/access/accountant/`
- `GET /api/users/access/salesman/`
- `GET /api/users/access/customer/`

These endpoints return a success message only if the authenticated user has the required role.

### Role-based user viewsets

Each of the following endpoints is a DRF viewset that returns the current user when they have the required role.

- `GET /api/users/manager/`
- `GET /api/users/accountant/`
- `GET /api/users/salesman/`
- `GET /api/users/customer/`

These endpoints are useful for the frontend to confirm role-specific access for managers, accountants, salesmen, and customers.

## Products API Endpoints

### Categories

- `GET /api/products/categories/`
  - List all categories.
- `POST /api/products/categories/`
  - Create a new category. Manager-only.
- `PUT /api/products/categories/{id}/`
- `PATCH /api/products/categories/{id}/`
- `DELETE /api/products/categories/{id}/`
  - Update/delete categories. Manager-only.

### Suppliers

- `GET /api/products/suppliers/`
  - List suppliers.
- `POST /api/products/suppliers/`
  - Create supplier. Manager-only.
- `PUT /api/products/suppliers/{id}/`
- `PATCH /api/products/suppliers/{id}/`
- `DELETE /api/products/suppliers/{id}/`
  - Update/delete supplier. Manager-only.
- `GET /api/products/suppliers/{id}/categories/`
  - Returns categories supplied by the supplier.

### Supplier Categories

- `GET /api/products/supplier-categories/`
- `POST /api/products/supplier-categories/`
- `PUT /api/products/supplier-categories/{id}/`
- `PATCH /api/products/supplier-categories/{id}/`
- `DELETE /api/products/supplier-categories/{id}/`
  - All actions require manager role.
- `GET /api/products/supplier-categories/by_category/?category_id=<id>`
- `GET /api/products/supplier-categories/by_supplier/?supplier_id=<id>`

### Products

- `GET /api/products/products/`
  - List products.
- `POST /api/products/products/`
- `PUT /api/products/products/{id}/`
- `PATCH /api/products/products/{id}/`
- `DELETE /api/products/products/{id}/`
  - Create/update/delete products. Manager-only.
- `GET /api/products/products/by_category/?category_id=<id>`
  - Filter products by category.

### Bills

- `GET /api/products/bills/`
- `POST /api/products/bills/`
- `GET /api/products/bills/{id}/`
- `PUT /api/products/bills/{id}/`
- `PATCH /api/products/bills/{id}/`
- `DELETE /api/products/bills/{id}/`
  - All bill actions require manager role.
- `GET /api/products/bills/by_supplier/?supplier_id=<id>&start_date=<YYYY-MM-DD>&end_date=<YYYY-MM-DD>`
  - Filter bills by supplier and optional date range.
- `GET /api/products/bills/by_category/?category_id=<id>`
  - Filter bills containing products in a category.
- `POST /api/products/bills/{id}/mark_received/`
  - Mark bill as received. Manager-only.
- `GET /api/products/bills/{id}/history/`
  - Returns bill details plus supplier and category history.

### Bill Items

- `GET /api/products/bill-items/`
- `POST /api/products/bill-items/`
- `GET /api/products/bill-items/{id}/`
- `PUT /api/products/bill-items/{id}/`
- `PATCH /api/products/bill-items/{id}/`
- `DELETE /api/products/bill-items/{id}/`
  - All actions require manager role.
- `GET /api/products/bill-items/?bill_id=<id>`
  - List items for a specific bill.
- `POST /api/products/bill-items/bulk_create/`
  - Bulk create bill items. Use request body with `bill_id` and `items` array.

### Inventory

- `GET /api/products/inventory/`
  - List inventory records.
- `GET /api/products/inventory/low_stock/`
  - List inventory items below reorder level.
- `GET /api/products/inventory/by_category/?category_id=<id>`
  - List inventory items for a category.

## Notes for Frontend

- All `/api/products/` routes require authentication.
- Manager-only routes require the authenticated user to have role `MANAGER`.
- If a user does not have the required role, the API returns a `403 Forbidden` response.
- For frontend role checks, use both the `users/access/.../` endpoints and the corresponding role-specific viewset endpoints.

## Running Locally

1. Activate the virtual environment.
2. Install dependencies from `requirements.txt`.
3. Run migrations: `python manage.py migrate`.
4. Start the server: `python manage.py runserver`.

## Example request headers

- `Authorization: Token <token>` or use session authentication depending on your backend auth setup.
- `Content-Type: application/json`
