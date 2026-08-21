import type { RouteObject } from "react-router";
import { AuthLayout } from "./AuthLayout";
import { LoginPage } from "./pages/LoginPage";
import { Step1 } from "./pages/registerWizard/Step1";
import { Step2 } from "./pages/registerWizard/Step2";


export const authRoutes: RouteObject[] = [
    {
        path: "/app/auth",
        Component: AuthLayout,
        children: [
            {
                path: "login",
                Component: LoginPage
            },
            {
                path: "register",
                children: [
                    {
                        index: true,
                        Component: Step1
                    },
                    {
                        path: "step2",
                        Component: Step2
                    }

                ]
            }
        ]
    },
    {
        path: "/store/auth",
        Component: AuthLayout,
        children: [
            {
                path: "login",
                Component: LoginPage

            },
            {
                path: "register",
                children: [
                    {
                        index: true,
                        Component: Step1
                    },
                    {
                        path: "step2",
                        Component: Step2
                    }

                ]
            }
        ]
    },

]