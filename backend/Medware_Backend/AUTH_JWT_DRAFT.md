JWT Authentication draft

Overview

- Endpoints added under `/api/auth/`:
  - `POST /api/auth/register/` — create user and returns `access` and `refresh` JWT tokens.
  - `POST /api/auth/token/` — obtain `access` and `refresh` tokens (username/password).
  - `POST /api/auth/token/refresh/` — exchange `refresh` for a new `access`.

How it works (backend)

- Registration uses `RegisterSerializer` to validate passwords and create a `users.User`.
- If `djangorestframework-simplejwt` is installed, `RegisterView` issues `RefreshToken.for_user(user)` and returns both tokens.
- DRF `DEFAULT_AUTHENTICATION_CLASSES` now include `JWTAuthentication` and `SessionAuthentication`.
- Protected endpoints require authenticated requests with either a valid JWT `Authorization: Bearer <access>` header or an authenticated session cookie.

Frontend instructions

- To register:
  - POST JSON to `/api/auth/register/` with `{ "username", "email", "password", "password2", "role" }`.
  - Store returned `access` and `refresh` tokens securely (e.g., in memory or secure storage; avoid localStorage if XSS is a concern).

- To authenticate (login):
  - POST to `/api/auth/token/` with `username` and `password`.
  - Receive `access` and `refresh` tokens.
  - Include `Authorization: Bearer <access>` on API requests.

- Token refresh:
  - When `access` expires, POST `{ "refresh": "<refresh>" }` to `/api/auth/token/refresh/` to obtain a new `access`.

- Protecting routes:
  - Use the `access` token for API calls; handle refresh flow on 401 responses.
  - For sensitive flows, consider short `access` lifetime and refresh on demand.

Notes / Requirements

- `djangorestframework-simplejwt` must be installed in the server environment.
- Backend returns tokens on registration only if SimpleJWT is available; otherwise registration still succeeds but without tokens.
- Frontend should treat `refresh` tokens carefully: store them more securely than `access` if possible, and rotate on logout.
