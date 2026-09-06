import { Outlet } from "react-router"
import { Relogin } from "./features/auth"

const AppShell = () => {
    return (
        <Relogin>
            <Outlet />
        </Relogin>
    )
}

export default AppShell