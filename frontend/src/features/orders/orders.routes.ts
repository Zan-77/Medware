import type { RouteObject } from "react-router";
import { OrderDetailsPage } from "./pages/OrderDetailsPage";
import { RequestsPage } from "./pages/RequestsPage";
import { OrdersPage } from "./pages/OrdersPage";

export const ordersRoutes: RouteObject[] = [
    {
        path: "orders",
        Component: OrdersPage,
    },
    {
        path: "orders/:orderId",
        Component: OrderDetailsPage,
    },
    {
        path: "requests",
        Component: RequestsPage,
    },
]
