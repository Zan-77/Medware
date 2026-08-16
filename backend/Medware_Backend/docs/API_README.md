# API Handoff README

This document provides test and migration commands and a quick summary for handing API routes to the DB/backend developer.

Prerequisites
- Activate the project's virtual environment: `c:\Medware\backend\Medware\Scripts\Activate.ps1` (PowerShell) or `c:\Medware\backend\Medware\Scripts\activate` (bash)
- Python packages installed in the venv (project `Lib/site-packages` exists in repo). If not, install with `pip install -r requirements.txt`.

Run tests

- Run full test suite:
```bash
c:\Medware\backend\Medware\Scripts\python.exe c:\Medware\backend\Medware_Backend\manage.py test
```

- Run tests for a single app (example `inventory`):
```bash
c:\Medware\backend\Medware\Scripts\python.exe c:\Medware\backend\Medware_Backend\manage.py test inventory
```

- Run a single test case:
```bash
c:\Medware\backend\Medware\Scripts\python.exe c:\Medware\backend\Medware_Backend\manage.py test inventory.tests.InventoryPermissionTests.test_manager_can_create_category
```

Migrations and database

- Make migrations after schema finalization (run from repo root):
```bash
c:\Medware\backend\Medware\Scripts\python.exe c:\Medware\backend\Medware_Backend\manage.py makemigrations
c:\Medware\backend\Medware\Scripts\python.exe c:\Medware\backend\Medware_Backend\manage.py migrate
```

- To create a superuser for admin access:
```bash
c:\Medware\backend\Medware\Scripts\python.exe c:\Medware\backend\Medware_Backend\manage.py createsuperuser
```

Run server (development):
```bash
c:\Medware\backend\Medware\Scripts\python.exe c:\Medware\backend\Medware_Backend\manage.py runserver
```

Notes for DB/backend developer

- The API surface and route-to-role mapping lives in `docs/endpoint_role_matrix.csv`.
- Finalize model fields and run `makemigrations` to generate real migrations for each app: `orders`, `inventory`, `finance`, `audit`, `website`.
- Ensure `related_name` values are unique across apps to avoid reverse accessor clashes (we fixed one: `inventory.SupplierBill.supplier` uses `inventory_bills`).
- Business logic that must be implemented in transactional code (atomic operations): order finalization, return approval adjustments, supplier bill processing, commission calculations.
- Audit/logging: persist `AuditLog` and `RequestTransition` records for every workflow transition.

Handoff artifacts
- `/docs/endpoint_role_matrix.csv` — endpoint → HTTP method → allowed roles
- This `API_README.md` — test and migration commands plus notes

If you want, I can also auto-generate an OpenAPI (Swagger) spec from the current viewsets as a draft for frontend integration. Request that and I'll add it as `docs/openapi.json`.
