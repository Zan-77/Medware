import { CheckmarkCircle01Icon } from "@hugeicons/core-free-icons"
import { HugeiconsIcon } from "@hugeicons/react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useEffect, useState } from "react"
import { useTranslation } from "react-i18next"
import Button from "../../../components/Button"
import SelectInput from "../../../components/SelectInput"
import Text from "../../../components/Text"
import Toast from "../../../components/Toast"
import useOpenMenu from "../../../hooks/useOpenMenu"
import { useBoundStore } from "../../../store/useBoundStore"
import { getAccounts, patchAccount } from "../services/approvals.service"
import type { Account } from "../types/approvals"

const ASSIGNABLE_ROLES = [
    "MANAGER", "ACCOUNTANT", "SALESMAN", "WAREHOUSE_WORKER", "CUSTOMER", "GUEST",
]

/**
 * The manager's approval queue for new registrations.
 *
 * Signing up now always succeeds and lands unverified, so this is where those
 * accounts become real. A role is inert until approved, which is what makes the
 * permissive signup safe - and why the manager can correct the requested role
 * here before granting it.
 */
export const ApprovalsPage = () => {
    const user = useBoundStore(state => state.authSlice.user)
    const { t } = useTranslation()
    const queryClient = useQueryClient()
    const { isOpen: isOpenToast, setIsOpen: setIsOpenToast, ref: toastRef } = useOpenMenu()

    const [showAll, setShowAll] = useState(false)
    const [successMessage, setSuccessMessage] = useState<string | null>(null)
    const [errorMessage, setErrorMessage] = useState<string | null>(null)

    const { data = [], isLoading, isError } = useQuery({
        queryKey: ["accounts"],
        queryFn: getAccounts,
    })

    const update = useMutation({
        mutationFn: ({ id, changes }: { id: string; changes: { role?: string; is_verified?: boolean } }) =>
            patchAccount(id, changes),
        onSuccess() {
            setErrorMessage(null)
            setSuccessMessage(t("Approvals.updateSuccess"))
            setIsOpenToast(true)
            queryClient.invalidateQueries({ queryKey: ["accounts"] })
            // The signed-in user's own verification may have moved.
            queryClient.invalidateQueries({ queryKey: ["me"] })
        },
        onError() {
            // 403 when the target is the acting manager or a superuser.
            setErrorMessage(t("Approvals.serverError"))
        },
    })

    useEffect(() => {
        if (!isOpenToast) return
        const id = window.setTimeout(() => { setIsOpenToast(false); setSuccessMessage(null) }, 3000)
        return () => window.clearTimeout(id)
    }, [isOpenToast, setIsOpenToast])

    // Mirrors the server guards, so a row that would 403 renders read-only
    // rather than failing on click.
    const canAct = (row: Account) =>
        String(row.id) !== String(user.id) && !row.is_superuser

    const rows = showAll ? data : data.filter((account) => !account.is_verified)

    if (isLoading) return <Text>{t("Approvals.loading")}</Text>
    if (isError) return <Text className="text-error">{t("Approvals.serverError")}</Text>

    return (
        <div>
            <Toast onClick={() => { setIsOpenToast(false); setSuccessMessage(null) }} isOpen={isOpenToast} ref={toastRef}>
                {successMessage && <div className="flex items-center gap-x-2">
                    <HugeiconsIcon className="*:fill-ok *:stroke-white" size={24} icon={CheckmarkCircle01Icon} />
                    <Text>{successMessage}</Text>
                </div>}
            </Toast>

            <div className="flex items-center gap-x-3 mb-6">
                <Button size="sm" variants={showAll ? "ghost" : "border"}
                    onClick={() => setShowAll(false)}>{t("Approvals.pendingOnly")}</Button>
                <Button size="sm" variants={showAll ? "border" : "ghost"}
                    onClick={() => setShowAll(true)}>{t("Approvals.allAccounts")}</Button>
            </div>

            {errorMessage && <Text className="mb-3 text-error">{errorMessage}</Text>}

            {rows.length === 0
                ? <Text>{t("Approvals.empty")}</Text>
                : <div className="space-y-3">
                    {rows.map((account) => (
                        <div key={account.id}
                            className="flex flex-wrap items-center justify-between gap-3 p-4 rounded-xl border border-light-border-secondary dark:border-dark-border-tertiary">
                            <div className="min-w-40">
                                <Text>{account.username}</Text>
                                <Text className="text-xs opacity-70">{account.email}</Text>
                            </div>

                            <div className="w-44">
                                {canAct(account)
                                    ? <SelectInput
                                        value={account.role}
                                        onChange={(event) => update.mutate({
                                            id: account.id, changes: { role: event.target.value },
                                        })}>
                                        {ASSIGNABLE_ROLES.map((role) => (
                                            <option key={role} value={role}>{t(role)}</option>
                                        ))}
                                    </SelectInput>
                                    : <Text>{t(account.role)}</Text>}
                            </div>

                            <Text className="opacity-70">
                                {account.is_verified ? t("Approvals.verified") : t("Approvals.awaiting")}
                            </Text>

                            {canAct(account) && (
                                account.is_verified
                                    ? <Button size="xs" variants="ghost"
                                        className="dark:text-error text-error"
                                        onClick={() => update.mutate({
                                            id: account.id, changes: { is_verified: false },
                                        })}>{t("Approvals.revoke")}</Button>
                                    : <Button size="xs"
                                        onClick={() => update.mutate({
                                            id: account.id, changes: { is_verified: true },
                                        })}>{t("Approvals.approve")}</Button>
                            )}
                        </div>
                    ))}
                </div>}
        </div>
    )
}
