import { useQueryClient } from "@tanstack/react-query"
import { useTranslation } from "react-i18next"
import Button from "../../../components/Button"
import Text from "../../../components/Text"

interface PendingApprovalPageProps {
    /** Shown so the user can tell a manager which account to approve. */
    username?: string
    roleLabel?: string
}

/**
 * Shown instead of the app when a staff account has not been approved yet.
 *
 * Without this the account simply gets 403 from every endpoint with no
 * explanation - the backend enforces verification, so the UI has to say why.
 */
export const PendingApprovalPage = ({ username, roleLabel }: PendingApprovalPageProps) => {
    const { t } = useTranslation()
    const queryClient = useQueryClient()

    return (
        <div className="flex h-full flex-col items-center justify-center gap-y-4 p-10 text-center">
            <Text weight="medium">{t("Pending.title")}</Text>
            <Text>{t("Pending.body")}</Text>

            {username && (
                <Text className="opacity-70">
                    {username}{roleLabel ? ` — ${roleLabel}` : ""}
                </Text>
            )}

            <Button
                variants="border"
                // The backend authorises from the row, so approval takes effect
                // on the next request - no need to sign out and back in.
                onClick={() => queryClient.invalidateQueries({ queryKey: ["me"] })}>
                {t("Pending.recheck")}
            </Button>
        </div>
    )
}
