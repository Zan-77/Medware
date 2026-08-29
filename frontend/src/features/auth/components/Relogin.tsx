import { useMutation } from "@tanstack/react-query"
import { useLocation, useNavigate } from "react-router"
import { useEffect, useRef } from "react"
import { relogin } from "../services/auth.service"
import { setAuthHeader } from "../../../services/api"
import { decodeAccessToken } from "../utility/decodeAccessToken"
import { useBoundStore } from "../../../store/useBoundStore"

interface ReloginProps { children: React.ReactNode }

export const Relogin = ({ children }: ReloginProps) => {
    const location = useLocation()
    const navigate = useNavigate()
    const isAuthenticated = useBoundStore(state => state.authSlice.isAuthenticated)
    const setIsAuthenticated = useBoundStore(state => state.authSlice.actions.setIsAuthenticated)
    const setIsGuest = useBoundStore(state => state.authSlice.actions.setIsGuest)
    const setUser = useBoundStore(state => state.authSlice.actions.setUser)
    const hasAttemptedRelogin = useRef(false)

    const mutation = useMutation({
        mutationKey: ["auth", "relogin"],
        mutationFn: relogin,
        onError: () => {
            if (hasAttemptedRelogin.current) {
                if (location.pathname.includes("store")) {
                    navigate("/store/")
                } else {
                    navigate("/app/auth/login", { relative: "path" })
                }
            }
        },
        onSuccess: (data) => {
            const accessPayload = decodeAccessToken(data.access)
            if (accessPayload) {
                setAuthHeader(data.access)
                setIsGuest(false)
                setIsAuthenticated(true)
                setUser({ id: accessPayload.user_id, role: accessPayload.role, email: accessPayload.email, username: "", first_name: accessPayload.first_name, last_name: accessPayload.last_name })
                if (accessPayload.role === "CUSTOMER" || (accessPayload.role === "GUEST" && !isAuthenticated))
                    navigate("/store/")
                else
                    navigate("/app/inventory", { state: { location: "inventory" } })
            }
        }
    })

    useEffect(() => {
        if (!isAuthenticated && !hasAttemptedRelogin.current) {
            hasAttemptedRelogin.current = true
            mutation.mutate()
        }
    }, [isAuthenticated, mutation])

    return (
        <>{mutation.isPending && children}</>
    )
}

