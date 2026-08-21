import { createBrowserRouter } from "react-router";
import AppShell from "./AppShell";
import { authRoutes } from "./features/auth";

export const router = createBrowserRouter([
    {
        Component: AppShell,
        path: "/",
        children: [
            ...authRoutes,
            {
                path: "app",
                children: [

                ]
            },
            {
                path: "store",
                children: [
                 
                ]
            },
            {
                path:"dpa"
            },
            {
                path:"tos"
            }
        ]
    },

]);