import type { RouteObject } from "react-router";
import { ApprovalsPage } from "./pages/ApprovalsPage";

export const approvalsRoutes: RouteObject[] = [
    {
        path: "approvals",
        Component: ApprovalsPage,
    },
]
