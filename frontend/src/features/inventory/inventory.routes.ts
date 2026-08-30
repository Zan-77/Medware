import type { RouteObject } from "react-router";
import { InventoryBillPage } from "./pages/InventoryBillPage";

export const inventoryRoutes: RouteObject[] = [

    {
        path: "inventory",
        Component: InventoryBillPage
    }, 
    {
        path: "inventory/bills",
        Component: InventoryBillPage
    }, 
    {
        path: "inventory/categories",
        Component: InventoryBillPage
    }


]