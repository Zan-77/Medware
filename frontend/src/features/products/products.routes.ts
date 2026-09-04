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