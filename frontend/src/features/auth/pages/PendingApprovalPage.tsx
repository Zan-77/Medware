import { Logout05Icon } from "@hugeicons/core-free-icons"
import { HugeiconsIcon } from "@hugeicons/react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useTranslation } from "react-i18next"
import { useNavigate } from "react-router"
import Button from "../../../components/Button"
import Text from "../../../components/Text"
import { setAuthHeader } from "../../../services/api"
import { useBoundStore } from "../../../store/useBoundStore"
import { logout } from "../services/auth.service"

interface PendingApprovalPageProps {
    /** Shown so the user can tell a manager which account to approve. */
    username?: string
    roleLabel?: string
}

/**
 * Shown INSTEAD OF the whole app - navigation included - when a staff account
 * has not been approved yet.
 *
 * The backend refuses every role-gated request from such an account, so without
 * this the user would just collect 403s with no explanation. The navigation is
 * deliberately absent: its header renders the account's name and the role it
 * has not been granted yet, and none of its destinations would load anyway.
 * That makes signing out this screen's own responsibility.
 */
export const PendingApprovalPage = ({ username, roleLabel }: PendingApprovalPageProps) => {
    const { t } = useTranslation()
    const navigate = useNavigate()
    const queryClient = useQueryClient()
    const setIsAuthenticated = useBoundStore(state => state.authSlice.actions.setIsAuthenticated)
    const setIsGuest = useBoundStore(state => state.authSlice.actions.setIsGuest)
    const setUser = useBoundStore(state => state.authSlice.actions.setUser)

    const signOut = useMutation({
        mutationFn: logout,
        // Either way the session is over locally; a failed call must not strand
        // the user on a screen with no way out.
        onSettled() {
            setAuthHeader("")
            setIsGuest(true)
            setIsAuthenticated(false)
            setUser({ id: "", role: "GUEST", email: "", username: "", first_name: "", last_name: "" })
            // Nothing cached belongs to the next account to sign in here.
            queryClient.clear()
            navigate("/app/auth/login", { relative: "path" })
        },
    })

    return (
        <div className="flex h-dvh flex-col items-center justify-center gap-y-4 p-10 text-center">
            <Text weight="medium">{t("Pending.title")}</Text>
            <Text>{t("Pending.body")}</Text>

            {username && (
                <Text className="opacity-70">
                    {username}{roleLabel ? ` — ${roleLabel}` : ""}
                </Text>
            )}

            <div className="flex items-center gap-x-3 mt-2">
                <Button
                    variants="border"
                    // The backend authorises from the row, so approval takes
                    // effect on the next request - no need to sign in again.
                    onClick={() => queryClient.invalidateQueries({ queryKey: ["me"] })}>
                    {t("Pending.recheck")}
                </Button>
                <Button
                    variants="ghost"
                    onClick={() => signOut.mutate()}
                    rightIcon={<HugeiconsIcon size={20} icon={Logout05Icon} />}>
                    {t("logout")}
                </Button>
            </div>
        </div>
    )
}
