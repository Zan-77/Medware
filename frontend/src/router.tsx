import { createBrowserRouter } from "react-router";
import AppShell from "./AppShell";
import { authRoutes } from "./features/auth";
import { inventoryRoutes } from "./features/inventory";
import { appLayout } from "./layouts/appLayout";
import { peoductsRoutes } from "./features/products";
import { ordersRoutes } from "./features/orders";
import { approvalsRoutes } from "./features/approvals";
import { customersRoutes } from "./features/customers";
import { financeRoutes } from "./features/finance";

export const router = createBrowserRouter([
    {
        Component: AppShell,
        path: "/",
        children: [
            ...authRoutes,
            {
                path: "/app",
                Component:appLayout,
                children:[
                    ...inventoryRoutes,
                    ...peoductsRoutes,
                    ...ordersRoutes,
                    ...customersRoutes,
                    ...financeRoutes,
                    ...approvalsRoutes
                ]
            },
            {
                path: "/store"

            },
            {
                path: "dpa"
            },
            {
                path: "tos"
            }
        ]
    },

]);