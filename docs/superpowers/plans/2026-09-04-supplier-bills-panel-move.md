# Supplier Bills Panel Move — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the supplier-bills list and its bill-line details out of the inventory panel into the suppliers panel, and open a bill's lines from a "details" action in its row instead of from the bill's ID link.

**Architecture:** Both pages move from `features/inventory/pages/` to `features/products/pages/` and are renamed after the models they show (`SupplierBillsPage`, `SupplierBillLinesPage`). Their routes move from `inventory.routes.ts` to `products.routes.ts`, so the URLs become `/app/supplier/bills` and `/app/supplier/bills/:billId`. The service functions stay in `features/inventory/services/inventory.service.ts` because they mirror the backend `inventory` app whose endpoints are unchanged — the pages import across features, which is the pattern already in use (the bills page imports `products.service` today). Navigation gains a Suppliers dropdown and loses both of its inventory-side bills entries.

**Tech Stack:** React 19, React Router 8, TanStack Query 5, TanStack Table 9, react-hook-form, i18next (Arabic only), TypeScript 6, Vite 8.

**Spec:** No spec document — this is the bounded path of `superpowers:brainstorming`. The requirement is captured in "Requirement" and "Assumption on file" below; this plan is the artifact to approve or redirect.

**Requirement (user's words):** "the bill details should be in the suppliers panel, its now in the inventory panel… the details of the bill which is the bill line should be shown when clicking on 'details' in the bill in the bills list rather clicking on the bill shown ID as it is right now."

## Assumption on file — read this before executing

The user was asked whether "move it to the suppliers panel" meant the URLs too or only the navigation, and had not answered when this plan was written. **This plan implements the full move (URLs + files + navigation).** If the answer turns out to be "navigation only":

- Skip Task 1 entirely, and in Tasks 3 and 4 keep every URL as `/app/inventory/bills…` — only the nav entry moves under Suppliers.
- Task 2 is unaffected either way.

A second open point, deliberately **not** implemented here: the supplier row's ID cell on the suppliers page still navigates (to that supplier's bills). The user only asked to change the trigger on the *bills* row. Task 3 retargets that link but leaves it an ID link. Raise it if the same "details" treatment is wanted there.

## Global Constraints

- **No backend changes.** The API already serves everything these pages need: `/api/inventory/bills/?supplier=<id>`, `/api/inventory/bill-lines/?bill=<id>`, and the `supplier_name`/`item_name`/`category_name` labels. Do not touch `backend/`.
- **Keep the existing layer design.** Pages call service functions, service functions call `ax`. Do not introduce a store, a context, or a data-fetching abstraction.
- **Match the existing UI.** New controls reuse `Button` with `variants="ghost"`, `size="xs"`, `iconOnly`, and a `HugeiconsIcon` — identical to the Edit and Trash actions already in the same cell.
- **Every user-facing string goes through `t(...)`**, with the key added to `src/i18n/ar.ts`. A missing key renders the raw English identifier in the UI.
- **There is no frontend test runner in this repo** (no vitest, no jest, no `test` script). Do not add one — that is a separate decision. The verification gate for every task is: `npx tsc -b` clean, `npm run build` clean, the grep guard in Task 3, and the manual click-path in Task 5.
- All frontend commands run from `c:\Medware\frontemd\frontend`.
- `frontemd/` is a nested git repository. Commit inside `frontemd/`, not from `c:\Medware`.

## File Structure

| File | Responsibility | Change |
|---|---|---|
| `src/features/products/pages/SupplierBillsPage.tsx` | Bills list: filter by supplier, create/edit/delete a bill, open a bill's details | Created (moved from `features/inventory/pages/InventoryBillPage.tsx`) |
| `src/features/products/pages/SupplierBillLinesPage.tsx` | One bill's lines: list, create, edit, delete | Created (moved from `features/inventory/pages/InventoryBillLinesPage.tsx`) |
| `src/features/products/products.routes.ts` | Suppliers-panel routes | Gains `supplier/bills` and `supplier/bills/:billId` |
| `src/features/inventory/inventory.routes.ts` | Inventory-panel routes | Loses `bills` and `bills/:billId` |
| `src/features/inventory/services/inventory.service.ts` | HTTP calls to the backend `inventory` app | **Unchanged** — endpoints did not move |
| `src/features/products/pages/SupplierPage.tsx` | Suppliers list | Bills link retargeted |
| `src/features/auth/pages/LoginPage.tsx` | Sign-in | Post-login landing path retargeted |
| `src/features/auth/pages/registerWizard/Step2.tsx` | Registration final step | Post-register landing path retargeted |
| `src/components/Navigation.tsx` | Side nav | Suppliers becomes a dropdown; bills leaves both inventory-side dropdowns |
| `src/i18n/ar.ts` | Arabic strings | Gains `details`, `suppliersList`, `supplierBills` |

---

### Task 1: Move both bill pages into the suppliers feature

Moves the files and the routes together, because a page whose route still points at the old path is not independently testable. After this task `/app/supplier/bills` renders the list and `/app/inventory/bills` renders nothing.

**Files:**
- Create: `src/features/products/pages/SupplierBillsPage.tsx` (content of `src/features/inventory/pages/InventoryBillPage.tsx`)
- Create: `src/features/products/pages/SupplierBillLinesPage.tsx` (content of `src/features/inventory/pages/InventoryBillLinesPage.tsx`)
- Delete: `src/features/inventory/pages/InventoryBillPage.tsx`
- Delete: `src/features/inventory/pages/InventoryBillLinesPage.tsx`
- Modify: `src/features/products/products.routes.ts`
- Modify: `src/features/inventory/inventory.routes.ts`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: `SupplierBillsPage` and `SupplierBillLinesPage`, both named exports from `src/features/products/pages/`. Routes `/app/supplier/bills` and `/app/supplier/bills/:billId` (route param name stays `billId`). Tasks 2–4 rely on all of these.

- [ ] **Step 1: Move the two files with git, preserving history**

```bash
cd c:/Medware/frontemd
git mv frontend/src/features/inventory/pages/InventoryBillPage.tsx \
       frontend/src/features/products/pages/SupplierBillsPage.tsx
git mv frontend/src/features/inventory/pages/InventoryBillLinesPage.tsx \
       frontend/src/features/products/pages/SupplierBillLinesPage.tsx
```

- [ ] **Step 2: Rename the component in `SupplierBillsPage.tsx`**

The directory depth is identical (`features/X/pages/`), so imports reaching `../../../components`, `../../../hooks`, `../../../store` and `../../auth` all still resolve. Only the two feature-relative imports change.

In `src/features/products/pages/SupplierBillsPage.tsx`:

```tsx
// was: import { getSuppliers } from "../../products/services/products.service"
import { getSuppliers } from "../services/products.service"
// was: import { getInventoryBills, postInventoryBill, putInventoryBill, deleteInventoryBill } from "../services/inventory.service"
import { getInventoryBills, postInventoryBill, putInventoryBill, deleteInventoryBill } from "../../inventory/services/inventory.service"
// was: import type { SupplierBillls } from "../types/inventory"
import type { SupplierBillls } from "../../inventory/types/inventory"
```

and rename the component:

```tsx
// was: export const InventoryBillPage = () => {
export const SupplierBillsPage = () => {
```

- [ ] **Step 3: Rename the component in `SupplierBillLinesPage.tsx`**

In `src/features/products/pages/SupplierBillLinesPage.tsx`:

```tsx
// was: import { getSupplierBillLinesById, postSupplierBillLine, putSupplierBillLine, deleteSupplierBillLine, getInventoryCategories, getInventoryItems } from "../services/inventory.service"
import { getSupplierBillLinesById, postSupplierBillLine, putSupplierBillLine, deleteSupplierBillLine, getInventoryCategories, getInventoryItems } from "../../inventory/services/inventory.service"
// was: import type { SupplierBilllLines } from "../types/inventory"
import type { SupplierBilllLines } from "../../inventory/types/inventory"
```

and rename the component:

```tsx
// was: export const InventoryBillLinesPage = () => {
export const SupplierBillLinesPage = () => {
```

- [ ] **Step 4: Add the routes to the suppliers panel**

Replace the whole of `src/features/products/products.routes.ts` with:

```ts
import type { RouteObject } from "react-router";
import { ProductsPage } from "./pages/ProductsPage";
import { SupplierPage } from "./pages/SupplierPage";
import { SupplierDetails } from "./pages/SupplierDetails";
import { SupplierBillsPage } from "./pages/SupplierBillsPage";
import { SupplierBillLinesPage } from "./pages/SupplierBillLinesPage";

export const peoductsRoutes: RouteObject[] = [

    {
        path: "products",
        Component: ProductsPage
    },
    {
        path: "supplier",
        Component: SupplierPage,
    },
    // Static segments outrank dynamic ones in React Router's ranking, so
    // `supplier/bills` wins over `supplier/:supplierId` for /app/supplier/bills.
    // Keep it listed first anyway so the intent is obvious to a reader.
    {
        path: "supplier/bills",
        Component: SupplierBillsPage,
    },
    {
        path: "supplier/bills/:billId",
        Component: SupplierBillLinesPage,
    },
    {
        path: "supplier/:supplierId",
        Component: SupplierDetails
    }


]
```

- [ ] **Step 5: Remove the routes from the inventory panel**

Replace the whole of `src/features/inventory/inventory.routes.ts` with:

```ts
import type { RouteObject } from "react-router";
import InventoryItemsDetails from "./pages/InventoryItemsDetails";
import { InventoryCategoriesPage } from "./pages/InventoryCategoriesPage";

export const inventoryRoutes: RouteObject[] = [

    {
        path: "inventory",
        children: [
            {
                path: "categories",
                Component: InventoryCategoriesPage,
            },
            {
                // The categories table links here. It used to be a bare
                // `:categoryId`, so `/app/inventory/categories/3/` matched no
                // route and the drill-down rendered nothing - while
                // `/app/inventory/items` (the nav button) matched it instead
                // and opened the details page with categoryId="items".
                path: "categories/:categoryId/",
                Component: InventoryItemsDetails
            },
            {
                path: "items",
                Component: InventoryItemsDetails
            },
        ]
    },


]
```

- [ ] **Step 6: Verify the move compiles**

```bash
cd c:/Medware/frontemd/frontend
npx tsc -b
```

Expected: no output, exit 0. If it reports `Cannot find module './pages/InventoryBillPage'` you missed a route import; if it reports a missing `../services/inventory.service` you missed one of the two import rewrites.

- [ ] **Step 7: Commit**

```bash
cd c:/Medware/frontemd
git add frontend/src/features/products/pages/SupplierBillsPage.tsx \
        frontend/src/features/products/pages/SupplierBillLinesPage.tsx \
        frontend/src/features/products/products.routes.ts \
        frontend/src/features/inventory/inventory.routes.ts \
        frontend/src/features/inventory/pages/
git commit -m "refactor: move supplier bills pages into the suppliers panel"
```

---

### Task 2: Open bill details from a "details" action instead of the ID link

**Files:**
- Modify: `src/features/products/pages/SupplierBillsPage.tsx` (actions column, `id` column, imports)
- Modify: `src/i18n/ar.ts`

**Interfaces:**
- Consumes: `SupplierBillsPage` from Task 1, and the route `/app/supplier/bills/:billId` it registers.
- Produces: nothing later tasks depend on.

- [ ] **Step 1: Add the `details` string**

In `src/i18n/ar.ts`, immediately after the line `actions:"أفعال",`, add:

```ts
    details: "تفاصيل",
```

- [ ] **Step 2: Import the icon and the navigate hook**

In `src/features/products/pages/SupplierBillsPage.tsx`, extend the two existing imports. `ViewIcon` is confirmed present in `@hugeicons/core-free-icons`.

```tsx
// was: import { CheckmarkCircle01Icon, Edit, Plus, Trash } from "@hugeicons/core-free-icons"
import { CheckmarkCircle01Icon, Edit, Plus, Trash, ViewIcon } from "@hugeicons/core-free-icons"
// was: import { Link, useSearchParams } from "react-router"
import { useNavigate, useSearchParams } from "react-router"
```

`Link` is no longer used in this file once Step 4 lands — leaving it imported fails `tsc` with TS6133, which is the intended signal that Step 4 was done.

- [ ] **Step 3: Get a navigate function in the component body**

Directly below the existing `const [searchParams] = useSearchParams()` line, add:

```tsx
    const navigate = useNavigate()
```

- [ ] **Step 4: Add the details button and make the ID plain text**

In the `columns` array, add the details button as the **first** control in the actions cell, so it reads details → delete → edit left to right. Replace the opening of that cell:

```tsx
            cell: ({ row }) => (
                <div className="flex justify-center gap-x-2">
                    {hasPermission(user, "supplierBillLines", "read")
                        &&
                        <Button
                            className="dark:text-accent-medium text-accent-dark dark:hover:text-accent-extraLight hover:text-accent-dark"
                            title={t("details")}
                            onClick={() => {
                                navigate(`/app/supplier/bills/${row.original.id}/`, {
                                    state: { location: "billDetails", details: row.original.supplier_name ?? "" },
                                })
                            }}
                            size="xs" variants="ghost" iconOnly={true}
                            leftIcon={<HugeiconsIcon size={18} icon={ViewIcon} />} />}
                    {hasPermission(user, "supplierBills", "delete")
```

Leave the rest of the cell (the delete and edit buttons) exactly as it is.

Then replace the `id` column's `cell` so the ID is no longer a link:

```tsx
        {
            meta: {
                filterVariants: "range"
            },
            id: "id",
            enableGrouping: false,
            enableSorting: true,
            header: t("id"),
            accessorKey: "id",
            // The ID is data, not navigation. Bill details open from the
            // "details" action in the actions column.
            filterFn: filterFn_inNumberRange
        },
```

(That is the whole column object — the `cell` property is deleted, so the table renders the raw value.)

- [ ] **Step 5: Verify it compiles**

```bash
cd c:/Medware/frontemd/frontend
npx tsc -b
```

Expected: no output, exit 0. A `TS6133: 'Link' is declared but its value is never read` here means Step 4's `id` column edit was missed.

- [ ] **Step 6: Commit**

```bash
cd c:/Medware/frontemd
git add frontend/src/features/products/pages/SupplierBillsPage.tsx frontend/src/i18n/ar.ts
git commit -m "feat: open bill details from a details action instead of the id link"
```

---

### Task 3: Retarget every inbound link to the new path

Three places still send the user to `/app/inventory/bills`. Two of them are the post-login and post-registration landing pages, so leaving them would drop every signed-in user onto a dead route.

**Files:**
- Modify: `src/features/products/pages/SupplierPage.tsx:209`
- Modify: `src/features/auth/pages/LoginPage.tsx:59`
- Modify: `src/features/auth/pages/registerWizard/Step2.tsx:73`
- Modify: `src/i18n/ar.ts`

**Interfaces:**
- Consumes: the route `/app/supplier/bills` from Task 1.
- Produces: nothing later tasks depend on.

- [ ] **Step 1: Add the header string for the bills list**

In `src/i18n/ar.ts`, immediately after the `details: "تفاصيل",` line added in Task 2, add:

```ts
    supplierBills: "فواتير الموردين",
```

Both auth redirects currently pass `state: { location: "inventory/bills" }`, and no such key exists — the header renders the raw text `inventory/bills`. They switch to this key.

- [ ] **Step 2: Retarget the suppliers-table link**

In `src/features/products/pages/SupplierPage.tsx`, replace the `id` column's `cell` body. The four comment lines above the `return` describe the old inventory path and are replaced too:

```tsx
            cell: ({ row }) => {
                // The supplier id opens that supplier's bills, filtered by the
                // `?supplier=` query the bills page reads.
                return hasPermission(user, "supplierBills", "read") ? <Link className="dark:text-accent-medium text-accent-dark" to={`/app/supplier/bills?supplier=${row.original.id}`} state={{ location: "supplierBills", details: row.original.name }}>{row.original.id}</Link> : row.original.id
            },
```

- [ ] **Step 3: Retarget the post-login landing page**

In `src/features/auth/pages/LoginPage.tsx`:

```tsx
// was: navigate("/app/inventory/bills", { state: { location: "inventory/bills" } })
navigate("/app/supplier/bills", { state: { location: "supplierBills" } })
```

- [ ] **Step 4: Retarget the post-registration landing page**

In `src/features/auth/pages/registerWizard/Step2.tsx`:

```tsx
// was: navigate("/app/inventory/bills", { state: { location: "inventory/bills" } })
navigate("/app/supplier/bills", { state: { location: "supplierBills" } })
```

- [ ] **Step 5: Run the stale-link guard**

This is the automated check that replaces a unit test for this task. It is the exact class of bug already found in this codebase — a link pointing at a route that no longer exists.

```bash
cd c:/Medware/frontemd/frontend
grep -rn "app/inventory/bills" src/ ; echo "matches above; exit=$?"
```

Expected: no matches printed (`exit=1` from grep means "nothing found", which is the pass condition here). Any line printed is a link still pointing at the removed route — fix it before continuing.

- [ ] **Step 6: Verify it compiles**

```bash
cd c:/Medware/frontemd/frontend
npx tsc -b
```

Expected: no output, exit 0.

- [ ] **Step 7: Commit**

```bash
cd c:/Medware/frontemd
git add frontend/src/features/products/pages/SupplierPage.tsx \
        frontend/src/features/auth/pages/LoginPage.tsx \
        frontend/src/features/auth/pages/registerWizard/Step2.tsx \
        frontend/src/i18n/ar.ts
git commit -m "fix: point every bills link at the suppliers panel route"
```

---

### Task 4: Re-home the navigation

Bills currently appears in the side nav **twice**: once as `purchaseBills` in the `inventory` dropdown, and once as `bills` in the `Orders` dropdown — that second dropdown is a verbatim copy of the first. Both entries go, and Suppliers becomes a dropdown holding the suppliers list and the bills list.

**Out of scope, flag only:** the `Orders` dropdown still contains `categories` and `items` entries duplicated from the `inventory` dropdown after this task. That is a pre-existing copy/paste and fixing it is a separate decision — do not restructure it here, but mention it when reporting the task complete.

**Files:**
- Modify: `src/components/Navigation.tsx`
- Modify: `src/i18n/ar.ts`

**Interfaces:**
- Consumes: the route `/app/supplier/bills` from Task 1 and the `supplierBills` string from Task 3.
- Produces: nothing later tasks depend on.

- [ ] **Step 1: Add the suppliers-list string**

In `src/i18n/ar.ts`, immediately after the `supplierBills: "فواتير الموردين",` line added in Task 3, add:

```ts
    suppliersList: "قائمة الموردين",
```

- [ ] **Step 2: Add a menu-state hook for the new dropdown**

In `src/components/Navigation.tsx`, next to the existing `isOpenWareHouse` / `isOpenOrders` lines, add:

```tsx
  const { isOpen: isOpenSuppliers, setIsOpen: setIsOpenSuppliers } = useOpenMenu()
```

- [ ] **Step 3: Turn the Suppliers button into a dropdown**

Replace the single Suppliers line (the one containing `t('Supplier')` and `navigarte("/app/supplier"`) with:

```tsx
        <div>
          <Button size='sm'
            onClick={() => { setIsOpenSuppliers(!isOpenSuppliers) }}
            className={`w-full justify-start`}
            leftIcon={<HugeiconsIcon size={22} icon={Trolley02Icon} />}
            rightIcon={<HugeiconsIcon className={` transition-all ease-in-out ${isOpenSuppliers ? "rotate-0" : "rotate-180"}`} size={22} icon={ArrowDown01Icon} />}
            variants='ghost'>{t('Supplier')}</Button>
          <Dropdown isOpen={isOpenSuppliers}>
            <Button
              size='sm'
              className={`w-full justify-start`}
              variants='ghost'
              active={location.pathname === "/app/supplier"}
              leftIcon={<HugeiconsIcon size={22} icon={Trolley02Icon} />}
              onClick={() => { navigarte("/app/supplier", { state: { location: "Supplier" } }); }}
            >
              {t('suppliersList')}
            </Button>
            <Button
              size='sm'
              className={`w-full justify-start`}
              variants='ghost'
              active={location.pathname.includes("supplier/bills")}
              leftIcon={<HugeiconsIcon size={22} icon={Invoice03Icon} />}
              onClick={() => { navigarte("/app/supplier/bills", { state: { location: "supplierBills" } }); }}
            >
              {t('supplierBills')}
            </Button>
          </Dropdown>
        </div>
```

`active={location.pathname === "/app/supplier"}` is an exact match on purpose: `.includes("supplier")` would light up the suppliers-list entry while the user is on `/app/supplier/bills`.

- [ ] **Step 4: Delete the bills entry from the inventory dropdown**

Remove this whole `<Button>` element (the one inside the `isOpenWareHouse` dropdown, labelled `t('purchaseBills')`):

```tsx
            <Button
              size='sm'
              className={`w-full justify-start`}
              variants='ghost'
              active={location.pathname.includes("inventory/bills")}
              leftIcon={<HugeiconsIcon size={22} icon={Invoice03Icon} />}
              onClick={() => { navigarte("/app/inventory/bills", { state: { location: "purchaseBills" } }); }}
            >
              {t('purchaseBills')}
            </Button>
```

- [ ] **Step 5: Delete the bills entry from the Orders dropdown**

Remove this whole `<Button>` element (the one inside the `isOpenOrders` dropdown, labelled `t('bills')`):

```tsx
            <Button
              size='sm'
              className={`w-full justify-start`}
              variants='ghost'
              active={location.pathname.includes("inventory/bills")}
              leftIcon={<HugeiconsIcon size={22} icon={Invoice03Icon} />}
              onClick={() => { navigarte("/app/inventory/bills", { state: { location: "inventory_bills" } }); }}
            >
              {t('bills')}
            </Button>
```

- [ ] **Step 6: Re-run the stale-link guard and compile**

```bash
cd c:/Medware/frontemd/frontend
grep -rn "app/inventory/bills" src/
npx tsc -b
npm run build
```

Expected: the grep prints nothing, `tsc` prints nothing, and the build ends with `✓ built in …`. If `tsc` reports `'Invoice03Icon' is declared but its value is never read`, both dropdown entries were removed but Step 3's new bills entry was not added.

- [ ] **Step 7: Commit**

```bash
cd c:/Medware/frontemd
git add frontend/src/components/Navigation.tsx frontend/src/i18n/ar.ts
git commit -m "feat: move the bills entry from inventory into a suppliers dropdown"
```

---

### Task 5: Verify the click paths in the running app

There is no test runner, so this is the acceptance gate. Do not mark the work complete without running it.

**Files:** none modified.

**Interfaces:**
- Consumes: everything from Tasks 1–4.
- Produces: nothing.

- [ ] **Step 1: Start both servers**

```bash
# terminal 1
cd c:/Medware/backend/Medware_Backend && python manage.py runserver
# terminal 2
cd c:/Medware/frontemd/frontend && npm run dev
```

- [ ] **Step 2: Walk the paths and confirm each one**

Sign in as a MANAGER or ACCOUNTANT — those are the only roles the backend allows to read bills (`SupplierBillViewSet.allowed_roles_by_method`), so a SALESMAN will correctly see 403s here.

- [ ] Signing in lands on `/app/supplier/bills` and the header reads فواتير الموردين, not `inventory/bills`.
- [ ] The side nav's Suppliers entry expands to two items; clicking فواتير الموردين opens the bills list.
- [ ] The inventory dropdown no longer offers bills, and neither does the Orders dropdown.
- [ ] In the bills table the ID column is plain text — not a link.
- [ ] The details (eye) icon in a bill's row opens `/app/supplier/bills/<that id>/` and the table shows **only that bill's lines**.
- [ ] From the suppliers list, clicking a supplier's ID opens `/app/supplier/bills?supplier=<id>` and lists only that supplier's bills.
- [ ] Adding a line from the details page saves and the new row appears without a manual refresh.
- [ ] Visiting `/app/inventory/bills` directly now renders nothing — the route is gone, as intended.

- [ ] **Step 3: Report**

Report which checks passed, and include the Orders-dropdown duplication flagged in Task 4 as a known remaining issue.

---

## Self-Review

**Spec coverage.** "Bill details in the suppliers panel" → Tasks 1, 3, 4. "Details shown by clicking 'details' rather than the ID" → Task 2. Both requirements have tasks.

**Placeholder scan.** No TBDs. Every code step carries the literal code to write. The one deliberate uncertainty — full move vs navigation-only — is isolated in "Assumption on file" with the exact instruction for the other branch, rather than left vague inside a task.

**Type consistency.** `SupplierBillsPage` and `SupplierBillLinesPage` are the names used in Task 1's route file, Task 2's edits, and the file-structure table. The route param stays `billId`, which is what `SupplierBillLinesPage` reads via `useParams<{ billId: string }>()` — unchanged from the file it was moved from. The i18n keys `details`, `supplierBills`, `suppliersList` are each added once (Tasks 2, 3, 4) and consumed only after they are added.

**Known gap.** No automated test asserts that a link resolves to a live route; the grep guard in Task 3 Step 5 and the manual walk in Task 5 stand in for it. Adding vitest plus a route-resolution test would close this properly and is worth its own conversation.
