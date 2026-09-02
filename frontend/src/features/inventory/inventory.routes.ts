import type { RouteObject } from "react-router";
import { InventoryBillPage } from "./pages/InventoryBillPage";
import InventoryItemsDetails from "./pages/InventoryItemsDetails";
import { InventoryCategoriesPage } from "./pages/InventoryCategoriesPage";

export const inventoryRoutes: RouteObject[] = [

    {
        path: "inventory",
        children: [

            {
                path: "bills",
                Component: InventoryBillPage,
                children: [
                    {
                        path: ":supplierId/",
                        Component: InventoryBillPage
                    }
                ]
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