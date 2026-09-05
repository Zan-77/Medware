import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useTranslation } from "react-i18next"
import { useNavigate } from "react-router"
import Button from "../../../components/Button"
import Text from "../../../components/Text"
import { getInbox, markNotificationRead } from "../services/orders.service"

export const RequestsPage = () => {
    const { t } = useTranslation()
    const navigate = useNavigate()
    const queryClient = useQueryClient()

    // Polled rather than pushed: the project has no websockets, and adding
    // Channels would be an infrastructure change of its own.
    const { data } = useQuery({
        queryKey: ["ordersInbox"],
        queryFn: getInbox,
        refetchInterval: 30000,
    })

    const dismiss = useMutation({
        mutationFn: markNotificationRead,
        onSuccess() {
            queryClient.invalidateQueries({ queryKey: ["ordersInbox"] })
        },
    })

    if (!data || data.count === 0) return <Text>{t("Orders_.emptyInbox")}</Text>

    return (
        <div className="space-y-3">
            {data.items.map((item) => {
                const title = item.order
                    ? `${item.order.customer_name ?? ""} — ${t("orderTotal")}: ${item.order.total}`
                    : `${t("customer")}: ${item.customer?.name ?? ""}`
                // Customer rows are actioned on the customers page; order rows
                // open the order itself.
                const target = item.order
                    ? `/app/orders/${item.order.id}/`
                    : "/app/customers"
                const locationKey = item.order ? "orders" : "customers"

                return (
                    <div key={`${item.kind}-${item.order?.id ?? item.customer?.id ?? ""}-${item.notification_id ?? "q"}`}
                        className="flex items-center justify-between gap-x-4 p-4 rounded-xl border border-light-border-secondary dark:border-dark-border-tertiary">
                        <div>
                            <Text>{title}</Text>
                            {item.message && <Text>{item.message}</Text>}
                        </div>
                        <div className="flex gap-x-2">
                            <Button size="xs" variants="ghost"
                                onClick={() => navigate(target, { state: { location: locationKey } })}>
                                {t("details")}
                            </Button>
                            {item.notification_id !== null &&
                                <Button size="xs" variants="ghost"
                                    onClick={() => dismiss.mutate(item.notification_id as number)}>
                                    {t("Suppliers.confirm")}
                                </Button>}
                        </div>
                    </div>
                )
            })}
        </div>
    )
}
