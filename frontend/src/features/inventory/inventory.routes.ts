import type { RouteObject } from "react-router";
import { InventoryPage } from "./pages/InventoryPage";

export const inventoryRoutes: RouteObject[] = [

    {
        path:"inventory",
        Component:InventoryPage        
    }


]