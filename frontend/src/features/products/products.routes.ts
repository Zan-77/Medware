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
    {
        path: "supplier/bills",
        Component: SupplierBillsPage,
    },
    {
        path: "supplier/:supplierId/bills",
        Component: SupplierBillsPage,
    },
    {
        path: "supplier/:supplierId/bills/:billId",
        Component: SupplierBillLinesPage,
    },
        {
        path: "supplier/:supplierId",
        Component: SupplierDetails
    }


]