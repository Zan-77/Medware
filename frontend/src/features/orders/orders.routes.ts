import type { RouteObject } from "react-router";
import { OrdersPage } from "./pages/OrdersPage";
import { OrderDetailsPage } from "./pages/OrderDetailsPage";
import { OrderCreatePage } from "./pages/OrderCreatePage";

export const ordersRoutes: RouteObject[] = [
    {
        path: "orders",
        Component: OrdersPage,
    },
    {
        path: "orders/new",
        Component: OrderCreatePage,
    },
    {
        path: "orders/:orderId",
        Component: OrderDetailsPage,
    },
]
