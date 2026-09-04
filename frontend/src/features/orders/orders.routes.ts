import type { RouteObject } from "react-router";
import { OrdersPage } from "./pages/OrdersPage";
import { OrderDetailsPage } from "./pages/OrderDetailsPage";

export const ordersRoutes: RouteObject[] = [
    {
        path: "orders",
        Component: OrdersPage,
    },
    {
        path: "orders/:orderId",
        Component: OrderDetailsPage,
    },
]
