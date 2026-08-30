# Graph Report - Medware  (2026-08-30)

## Corpus Check
- Corpus is ~22,281 words - fits in a single context window. You may not need a graph.

## Summary
- 727 nodes · 1339 edges · 74 communities (47 shown, 27 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 157 edges (avg confidence: 0.93)
- Token cost: 31,200 input · 9,400 output

## Community Hubs (Navigation)
- Users, Roles & Permissions
- Inventory Domain Models
- Frontend Runtime Dependencies
- Frontend Build Tooling
- Orders & Returns Domain
- Inventory Feature Pages
- Audit Trail App
- Project Docs & Diagramming
- JWT Auth Flow Design
- Product Service Layer
- Auth Screens & Routes
- App TypeScript Config
- Website Public Catalog
- Form Input Components
- Node TypeScript Config
- Finance Records App
- Navigation & Access Control
- Role & Permission Types
- User Role Access Tests
- Shared UI Primitives
- Inventory Permission Tests
- Zustand Store Slices
- Order Auth Tests
- Role Required Mixin
- DRF Exception Handling
- Backend Manage Entrypoint
- Audit App Config
- Finance App Config
- Django Manage Entrypoint
- Django Settings Module
- Orders App Config
- Products App Config
- Users App Config
- Website App Config
- TypeScript Project References
- Audit Initial Migration
- Finance Initial Migration
- Inventory Initial Migration
- Supplier Bill Migration
- ASGI Entrypoint
- Root URL Configuration
- WSGI Entrypoint
- Orders Initial Migration
- Products Initial Migration
- Product Supplier Migration
- Users Initial Migration
- Unique Email Migration
- Website Initial Migration
- Website Catalog Table

## God Nodes (most connected - your core abstractions)
1. `RoleMethodPermission` - 35 edges
2. `useBoundStore` - 19 edges
3. `compilerOptions` - 18 edges
4. `SecurityRegressionTests` - 16 edges
5. `User` - 15 edges
6. `compilerOptions` - 15 edges
7. `Button()` - 14 edges
8. `UserRoleAccessTest` - 13 edges
9. `Text()` - 13 edges
10. `InventoryItem` - 12 edges

## Surprising Connections (you probably didn't know these)
- `HttpOnly Refresh Cookie` --semantically_similar_to--> `Client Token Storage Guidance`  [INFERRED] [semantically similar]
  4th-8-commit.txt → backend/AUTH_JWT_DRAFT.md
- `Users and Role API` --shares_data_with--> `users_user Table`  [INFERRED]
  backend/README.md → DB_ERD.md
- `django-cors-headers 4.9.0` --conceptually_related_to--> `React + TypeScript + Vite Template`  [INFERRED]
  backend/requirements.txt → frontemd/frontend/README.md
- `SVG Icon Sprite Sheet` --conceptually_related_to--> `Dark Mode Design Tokens`  [AMBIGUOUS]
  frontemd/frontend/public/icons.svg → frontemd/frontend/index.html
- `React + TypeScript + Vite Template` --conceptually_related_to--> `Auth API (/api/auth/)`  [INFERRED]
  frontemd/frontend/README.md → backend/README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **JWT Auth Token Lifecycle** — backend_auth_jwt_draft_register_endpoint, backend_auth_jwt_draft_token_endpoint, backend_auth_jwt_draft_token_refresh_endpoint, 4th_8_commit_cookie_refresh_flow, 4th_8_commit_logout_endpoint, 4th_8_commit_httponly_refresh_cookie [EXTRACTED 1.00]
- **Order-to-Cash Financial Flow** — db_erd_orders_orderrequest, db_erd_orders_orderitem, db_erd_orders_orderfinalization, db_erd_finance_paymentrecord, db_erd_finance_commissionrecord, db_erd_finance_customerbalance, db_erd_orders_returnrequest [INFERRED 0.95]
- **Supplier Bill to Stock Flow** — db_erd_products_supplier, db_erd_inventory_supplierbill, db_erd_inventory_supplierbillline, db_erd_inventory_stockentry, db_erd_inventory_inventoryitem [INFERRED 0.95]

## Communities (74 total, 27 thin omitted)

### Community 0 - "Users, Roles & Permissions"
Cohesion: 0.06
Nodes (40): AbstractUser, api_view, APIView, role_required(), Meta, Role, User, HasRole (+32 more)

### Community 1 - "Inventory Domain Models"
Cohesion: 0.11
Nodes (32): InventoryConfig, AppConfig, InventoryCategory, InventoryItem, StockEntry, SupplierBill, SupplierBillLine, InventoryCategorySerializer (+24 more)

### Community 2 - "Frontend Runtime Dependencies"
Cohesion: 0.04
Nodes (49): @capacitor/android, @capacitor/core, @capacitor/ios, @dnd-kit/react, dependencies, @capacitor/android, @capacitor/core, @capacitor/ios (+41 more)

### Community 3 - "Frontend Build Tooling"
Cohesion: 0.04
Nodes (46): @capacitor/cli, eslint, @eslint/js, eslint-plugin-react-hooks, eslint-plugin-react-refresh, devDependencies, @capacitor/cli, eslint (+38 more)

### Community 4 - "Orders & Returns Domain"
Cohesion: 0.16
Nodes (30): OrderFinalization, OrderItem, OrderRequest, OrderReview, PackagingTask, ReturnApproval, ReturnAssessment, ReturnRequest (+22 more)

### Community 5 - "Inventory Feature Pages"
Cohesion: 0.09
Nodes (23): AppShell(), InventoryListView(), inventoryRoutes, InventoryBillsPage(), InventoryCategoriesPage(), InventoryItemsPage(), money(), InventoryPage() (+15 more)

### Community 6 - "Audit Trail App"
Cohesion: 0.09
Nodes (15): AuditLog, RequestTransition, AuditLogSerializer, Meta, RequestTransitionSerializer, AppendOnlyViewSet, AuditLogViewSet, List/retrieve/create only. An audit trail that can be edited or deleted through… (+7 more)

### Community 7 - "Project Docs & Diagramming"
Cohesion: 0.06
Nodes (36): Copilot Mermaid Instruction Pointer, Mermaid Diagram Workflow, Mermaid Sync Cooperation Rule, Validate-Before-Present Rule, Atomic Transactional Business Logic, Audit Persistence Requirement, Django App Split, Endpoint Role Matrix (+28 more)

### Community 8 - "JWT Auth Flow Design"
Cohesion: 0.07
Nodes (31): Auth Flow Regression Tests, Cookie-Based Refresh Flow, Email-Based Login, HttpOnly Refresh Cookie, Logout Endpoint, Refresh Cookie Rotation, Dual JWT and Session Authentication, JWT Authentication (+23 more)

### Community 9 - "Product Service Layer"
Cohesion: 0.18
Nodes (20): Model, Toast, ToastProps, hasPermission(), deleteProduct(), deleteSupplier(), getProducts(), getSuppliers() (+12 more)

### Community 10 - "Auth Screens & Routes"
Cohesion: 0.20
Nodes (17): authRoutes, AuthLayout(), Relogin(), ReloginProps, LoginPage(), Step1(), getPasswordStrength(), Step2() (+9 more)

### Community 11 - "App TypeScript Config"
Cohesion: 0.08
Nodes (23): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+15 more)

### Community 12 - "Website Public Catalog"
Cohesion: 0.23
Nodes (12): PublicReadRoleWritePermission, Anonymous read, role-checked write. For genuinely public content (the…, WebsiteCatalog, WebsiteCatalogItem, WebsiteCustomerProfile, Meta, WebsiteCatalogItemSerializer, WebsiteCatalogSerializer (+4 more)

### Community 13 - "Form Input Components"
Cohesion: 0.18
Nodes (15): baseControlledInputStyle, ControlledInput(), ControlledInputProps, ControlledInputStyleVariants, Form(), FormProps, baseInputStyle, Input() (+7 more)

### Community 14 - "Node TypeScript Config"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+11 more)

### Community 15 - "Finance Records App"
Cohesion: 0.35
Nodes (13): CommissionRecord, CustomerBalance, PaymentRecord, Voucher, CommissionRecordSerializer, CustomerBalanceSerializer, Meta, PaymentRecordSerializer (+5 more)

### Community 16 - "Navigation & Access Control"
Cohesion: 0.23
Nodes (10): Dropdown(), DropdownProps, Navigation, NavigationProps, logout(), canReadInventory(), INVENTORY_READ_ROLES, InventorySection (+2 more)

### Community 17 - "Role & Permission Types"
Cohesion: 0.24
Nodes (10): Step1FieldValues, Actions, Permissions, PermissionsCheck, ROLES, RoleWithPermissions, Roles, User (+2 more)

### Community 19 - "Shared UI Primitives"
Cohesion: 0.20
Nodes (10): baseButtonStyle, Button(), ButtonProps, ButtonVariants, CheckBox(), CheckBoxProps, features, Table() (+2 more)

### Community 21 - "Zustand Store Slices"
Cohesion: 0.33
Nodes (7): AuthSliceSate, createAuthSlice(), RegisterFieldsValues, UserWithoutPassword, AppSliceState, createAppSlice(), StoreState

### Community 22 - "Order Auth Tests"
Cohesion: 0.33
Nodes (3): OrderAuthTests, TestCase, Unauthenticated requests to order-requests should return 401

### Community 24 - "DRF Exception Handling"
Cohesion: 0.50
Nodes (3): api_exception_handler(), Project-wide DRF exception handling., Turn delete-integrity errors into 409 instead of a 500. Several models are…

## Ambiguous Edges - Review These
- `Auth API (/api/auth/)` → `Token Route 404 Failure`  [AMBIGUOUS]
  backend/Medware_Backend/scripts/smoke_result.txt · relation: conceptually_related_to
- `Dark Mode Design Tokens` → `SVG Icon Sprite Sheet`  [AMBIGUOUS]
  frontemd/frontend/public/icons.svg · relation: conceptually_related_to

## Knowledge Gaps
- **147 isolated node(s):** `Migration`, `Migration`, `Migration`, `Migration`, `Migration` (+142 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **27 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Auth API (/api/auth/)` and `Token Route 404 Failure`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `Dark Mode Design Tokens` and `SVG Icon Sprite Sheet`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `RoleMethodPermission` connect `Orders & Returns Domain` to `Users, Roles & Permissions`, `Inventory Domain Models`, `Audit Trail App`, `Website Public Catalog`, `Finance Records App`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **Why does `User` connect `Users, Roles & Permissions` to `Inventory Domain Models`, `Orders & Returns Domain`, `Audit Trail App`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **Are the 23 inferred relationships involving `RoleMethodPermission` (e.g. with `AuditLogViewSet` and `RequestTransitionViewSet`) actually correct?**
  _`RoleMethodPermission` has 23 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Migration`, `Migration`, `Migration` to the rest of the system?**
  _147 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Users, Roles & Permissions` be split into smaller, more focused modules?**
  _Cohesion score 0.06174863387978142 - nodes in this community are weakly interconnected._