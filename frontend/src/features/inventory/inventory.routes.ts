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
                path: ":categoryId/",
                Component: InventoryItemsDetails
            },
        ]
    },


]