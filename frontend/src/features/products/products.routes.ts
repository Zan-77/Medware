import type { RouteObject } from "react-router";
import { ProductsPage } from "./pages/ProductsPage";
import { SupplierPage } from "./pages/SupplierPage";
import { SupplierDetails } from "./pages/SupplierDetails";

export const peoductsRoutes: RouteObject[] = [

    {
        path: "products",
        Component: ProductsPage
    },
    {
        path: "supplier",
        Component: SupplierPage,
    },
    {   
        path:"supplier/:supplierId",
        Component:SupplierDetails
    }


]