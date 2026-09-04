import type { RouteObject } from "react-router";
import { InventoryBillPage } from "./pages/InventoryBillPage";
import InventoryItemsDetails from "./pages/InventoryItemsDetails";
import { InventoryCategoriesPage } from "./pages/InventoryCategoriesPage";
import { InventoryBillLinesPage } from "./pages/InventoryBillLinesPage";

export const inventoryRoutes: RouteObject[] = [

    {
        path: "inventory",
        children: [
            {
                path: "bills",
                Component: InventoryBillPage,
            },
            {
                path: "bills/:billId/",
                Component: InventoryBillLinesPage
            },
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
