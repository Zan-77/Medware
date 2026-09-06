import type { RouteObject } from "react-router";
import { CustomerStatementPage } from "./pages/CustomerStatementPage";
import { FinancePage } from "./pages/FinancePage";

export const financeRoutes: RouteObject[] = [
    {
        path: "finance",
        Component: FinancePage,
    },
    {
        path: "finance/:customerId",
        Component: CustomerStatementPage,
    },
]
