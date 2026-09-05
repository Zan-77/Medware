import type { RouteObject } from "react-router";
import { CustomersPage } from "./pages/CustomersPage";

export const customersRoutes: RouteObject[] = [
    {
        path: "customers",
        Component: CustomersPage,
    },
]
