import type { RouteObject } from "react-router";
import { redirect } from "react-router";
import { InventoryCategoriesPage } from "./pages/InventoryCategoriesPage";
import InventoryItemsDetails from "./pages/InventoryItemsDetails";

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
            {
                // `/app/inventory/bills` was the post-login landing page until the bills
                // feature moved under the suppliers panel. Existing users have it in
                // their history and bookmarks, so send them on rather than dead-ending
                // them on the router's 404 screen.
                path: "bills",
                loader: () => redirect("/app/supplier/bills"),
            },
            {
                path: "bills/:billId",
                loader: ({ params }) => redirect(`/app/supplier/bills/${params.billId}/`),
            },
        ]
    },


]
