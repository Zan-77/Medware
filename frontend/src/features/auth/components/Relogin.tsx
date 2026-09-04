import { useMutation } from "@tanstack/react-query"
import { useLocation, useNavigate } from "react-router"
import { useEffect, useRef, useState } from "react"
import { logout, relogin } from "../services/auth.service"
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
    // The silent-refresh attempt has finished (either way). Until it has, the
    // app is not rendered: a page mounted mid-refresh fires its queries with
    // no Authorization header and every one of them comes back 401.
    const [hasSettled, setHasSettled] = useState(false)

    const mutation = useMutation({
        mutationKey: ["auth", "relogin"],
        mutationFn: relogin,
        onError: async() => {
            try {
                await logout()
            } catch {
                // Already signed out server-side - never let this swallow the
                // redirect below.
            }
            if (hasAttemptedRelogin.current) {
                if (location.pathname.includes("store")) {
                    navigate("/store/")
                } else {
                    navigate("/app/auth/login", { relative: "path" })
                }
            }
            setHasSettled(true)
        },
        onSuccess: (data) => {
            const accessPayload = decodeAccessToken(data.access)
            if (accessPayload) {
                setAuthHeader(data.access)
                setIsGuest(false)
                setIsAuthenticated(true)
                setUser({ id: accessPayload.user_id, role: accessPayload.role, email: accessPayload.email, username: "", first_name: accessPayload.first_name, last_name: accessPayload.last_name })
            }
            setHasSettled(true)
        }
    })

    const { mutate } = mutation

    useEffect(() => {
        if (isAuthenticated) {
            setHasSettled(true)
            return
        }
        if (!hasAttemptedRelogin.current) {
            hasAttemptedRelogin.current = true
            mutate()
        }
        // `mutation` is a fresh object every render; depending on it re-ran
        // this effect continuously. Only the authentication state matters.
    }, [isAuthenticated, mutate])

    // Render the app once the refresh has settled - previously this was
    // `mutation.isPending && children`, so the entire app was mounted only
    // while the refresh was in flight and unmounted the moment it finished.
    return (
        <>{hasSettled ? children : null}</>
    )
}

