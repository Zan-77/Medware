import { useEffect } from "react"
import { Outlet } from "react-router"

const AppShell = () => {
    if (import.meta.env.VITE_DEV)
        useEffect(() => {
            const html = document.documentElement
            html.classList.add("dark")
            
            const onKeyDown = (e: KeyboardEvent) => {
                const key = e.key

                if (key === "1") {
                    html.classList.add("dark")
                    html.classList.remove("light")
                } else if (key === "2") {
                    html.classList.add("light")
                    html.classList.remove("dark")
                }
            }

            window.addEventListener("keydown", onKeyDown)
            return () => {
                window.removeEventListener("keydown", onKeyDown)
            }
        }, [])

    return (
        <Outlet />
    )
}

export default AppShell