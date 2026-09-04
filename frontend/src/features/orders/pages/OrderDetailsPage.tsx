import { HugeiconsIcon } from "@hugeicons/react"
import { CheckmarkCircle01Icon } from "@hugeicons/core-free-icons"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { useTranslation } from "react-i18next"
import { useParams } from "react-router"
import Button from "../../../components/Button"
import ControlledTextArea from "../../../components/ControlledTextArea"
import Form from "../../../components/Form"
import Model from "../../../components/Model"
import { Table } from "../../../components/Table"
import Text from "../../../components/Text"
import Toast from "../../../components/Toast"
import useOpenMenu from "../../../hooks/useOpenMenu"
import { useBoundStore } from "../../../store/useBoundStore"
import { hasPermission } from "../../auth"
import { approveOrder, getOrderById, rejectOrder } from "../services/orders.service"
import type { ColumnDef, SortingState, TableFeatures } from "@tanstack/react-table"
import type { OrderItem } from "../types/orders"

type RejectFields = { notes: string }

export const OrderDetailsPage = () => {
    const { orderId } = useParams<{ orderId: string }>()
    const user = useBoundStore(state => state.authSlice.user)
    const { t } = useTranslation()
    const queryClient = useQueryClient()
    const [sorting, setSorting] = useState<SortingState>([])
    const [successMessage, setSuccessMessage] = useState<string | null>(null)
    const { isOpen: isOpenReject, setIsOpen: setIsOpenReject, ref: rejectRef } = useOpenMenu()
    const { isOpen: isOpenToast, setIsOpen: setIsOpenToast, ref: toastRef } = useOpenMenu()

    const orderKey = ["orders", orderId] as const
    const { data: order } = useQuery({
        queryKey: orderKey,
        queryFn: () => getOrderById(String(orderId)),
        enabled: Boolean(orderId),
    })

    const { control, handleSubmit, reset, setError, formState: { errors } } = useForm<RejectFields>({
        defaultValues: { notes: "" },
        mode: "all",
    })

    const approve = useMutation({
        mutationFn: () => approveOrder(String(orderId)),
        onSuccess() {
            setSuccessMessage(t("Orders_.approveSuccess"))
            setIsOpenToast(true)
            queryClient.invalidateQueries({ queryKey: ["orders"] })
        },
        onError() {
            // 409 when another manager already decided this order. Without
            // this the button is a silent no-op and the manager cannot tell
            // whether the click registered.
            setError("root.server", { type: "server", message: t("Orders_.serverError") })
        },
    })

    const rejectMutation = useMutation({
        mutationFn: (notes: string) => rejectOrder(String(orderId), notes),
        onSuccess() {
            setIsOpenReject(false)
            reset({ notes: "" })
            setSuccessMessage(t("Orders_.rejectSuccess"))
            setIsOpenToast(true)
            queryClient.invalidateQueries({ queryKey: ["orders"] })
        },
        onError() {
            setError("root.server", { type: "server", message: t("Orders_.serverError") })
        },
    })

    const columns: Array<ColumnDef<TableFeatures, OrderItem>> = [
        {
            id: "product",
            header: t("item"),
            accessorFn: (row) => row.product_name ?? String(row.product ?? ""),
            cell: ({ row }) => row.original.product_name ?? String(row.original.product ?? ""),
            enableSorting: true,
        },
        { id: "quantity", header: t("quantity"), accessorKey: "quantity", enableSorting: true },
        { id: "sell_price", header: t("unit_price"), accessorKey: "sell_price", enableSorting: true },
        {
            id: "line_total",
            header: t("lineTotal"),
            accessorFn: (row) => Number(row.quantity) * Number(row.sell_price),
            cell: ({ row }) => Number(row.original.quantity) * Number(row.original.sell_price),
            enableSorting: true,
        },
        { id: "note", header: t("note"), accessorKey: "note", enableSorting: false },
    ]

    if (!order) return <Text>{t("Orders_.emptyInbox")}</Text>

    const canDecide = hasPermission(user, "orderApproval", "update") && order.status === "PENDING"

    return (
        <div>
            <Model title={t("Orders_.rejectTitle")} isOpen={isOpenReject} onClick={() => setIsOpenReject(false)} ref={rejectRef}>
                <Form
                    ServerError={errors.root?.server}
                    onSubmit={handleSubmit((values) => rejectMutation.mutate(values.notes))}
                    Buttons={<Button type="submit">{t("reject")}</Button>}>
                    <ControlledTextArea<RejectFields>
                        rules={{
                            shouldUnregister: true,
                            required: { message: t("Orders_.rejectReasonRequired"), value: true },
                        }}
                        placeholder={t("Orders_.rejectReason")}
                        name="notes"
                        control={control}
                    />
                </Form>
            </Model>

            <Toast onClick={() => { setIsOpenToast(false); setSuccessMessage(null) }} isOpen={isOpenToast} ref={toastRef}>
                {successMessage && <div className="flex items-center gap-x-2">
                    <HugeiconsIcon className="*:fill-ok *:stroke-white" size={24} icon={CheckmarkCircle01Icon} />
                    <Text>{successMessage}</Text>
                </div>}
            </Toast>

            <div className="grid grid-cols-2 gap-x-6 mb-6">
                <Text>{t("customer")}: {order.customer_name}</Text>
                <Text>{t("salesman")}: {order.salesman_name ?? ""}</Text>
                <Text>{t("status")}: {t(`OrderStatus.${order.status}`)}</Text>
                <Text>{t("date")}: {order.created_at?.slice(0, 10)}</Text>
            </div>

            <Table<OrderItem> tableKey="orderItems" columns={columns} data={order.items}
                sorting={sorting} setSorting={setSorting} />

            <div className="mt-6 grid grid-cols-3 gap-x-6">
                <Text>{t("orderTotal")}: {order.total}</Text>
                <Text>{t("previousBalance")}: {order.previous_balance ?? "-"}</Text>
                <Text>{t("newBalance")}: {order.new_balance ?? "-"}</Text>
            </div>

            {errors.root?.server && <Text className="mb-3 text-error">{errors.root.server.message}</Text>}

            {canDecide && <div className="mt-6 flex gap-x-3">
                <Button onClick={() => approve.mutate()}>{t("approve")}</Button>
                <Button variants="ghost"
                    className="dark:text-error text-error"
                    onClick={() => setIsOpenReject(true)}>{t("reject")}</Button>
            </div>}
        </div>
    )
}
