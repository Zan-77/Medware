import { createBrowserRouter } from "react-router";
import AppShell from "./AppShell";
import { authRoutes } from "./features/auth";
import { inventoryRoutes } from "./features/inventory";
import { appLayout } from "./layouts/appLayout";
import { peoductsRoutes } from "./features/products";
import { ordersRoutes } from "./features/orders";

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
                    ...ordersRoutes
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