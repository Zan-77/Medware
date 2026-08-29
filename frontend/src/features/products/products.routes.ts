import type { RouteObject } from "react-router";
import { ProductsPage } from "./pages/ProductsPage";
import { SupplierPage } from "./pages/SupplierPage";

export const peoductsRoutes: RouteObject[] = [

    {
        path: "products",
        Component: ProductsPage
    },
    {
        path: "supplier",
        Component: SupplierPage
    }


]