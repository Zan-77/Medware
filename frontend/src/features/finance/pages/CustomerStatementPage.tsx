import { useQuery } from "@tanstack/react-query"
import { filterFn_includesString, filterFn_inNumberRange, type ColumnDef, type SortingState, type TableFeatures } from "@tanstack/react-table"
import { useState } from "react"
import { useTranslation } from "react-i18next"
import { useParams } from "react-router"
import { Table } from "../../../components/Table"
import Text from "../../../components/Text"
import { getCustomerStatement } from "../services/finance.service"
import type { StatementOrder, StatementVoucher } from "../types/finance"

const Figure = ({ label, value }: { label: string; value: React.ReactNode }) => (
    <div className="flex flex-col">
        <Text muted className="text-xs">{label}</Text>
        <Text weight="medium">{value}</Text>
    </div>
)

/**
 * One customer's account history: the approved orders that raised their
 * balance and the vouchers that brought it back down.
 *
 * Both tables come from a single `/statement/` call so the two halves and the
 * totals above them are always the same snapshot - fetching them separately
 * would let the figures disagree with the rows meant to explain them.
 */
export const CustomerStatementPage = () => {
    const { customerId } = useParams<{ customerId: string }>()
    const { t } = useTranslation()
    const [orderSorting, setOrderSorting] = useState<SortingState>([])
    const [voucherSorting, setVoucherSorting] = useState<SortingState>([])

    const { data: statement, isLoading } = useQuery({
        queryKey: ["customerStatement", customerId],
        queryFn: () => getCustomerStatement(String(customerId)),
        enabled: Boolean(customerId),
    })

    const orderColumns: Array<ColumnDef<TableFeatures, StatementOrder>> = [
        {
            meta: { filterVariants: "range" }, id: "id", header: t("id"),
            accessorKey: "id", filterFn: filterFn_inNumberRange,
        },
        {
            meta: { filterVariants: "value" }, id: "date", header: t("date"),
            // The API sends a timestamp; only the day is meaningful here.
            accessorFn: (row) => row.date?.slice(0, 10) ?? "",
            cell: ({ row }) => row.original.date?.slice(0, 10) ?? "",
            filterFn: filterFn_includesString,
        },
        {
            meta: { filterVariants: "value" }, id: "salesman", header: t("salesman"),
            accessorFn: (row) => row.salesman_name ?? "",
            cell: ({ row }) => row.original.salesman_name ?? t("none"),
            filterFn: filterFn_includesString,
        },
        {
            meta: { filterVariants: "value" }, id: "status", header: t("status"),
            accessorFn: (row) => t(`OrderStatus.${row.status}`),
            cell: ({ row }) => t(`OrderStatus.${row.original.status}`),
            filterFn: filterFn_includesString,
        },
        {
            meta: { filterVariants: "range" }, id: "total", header: t("orderTotal"),
            accessorKey: "total", filterFn: filterFn_inNumberRange,
        },
    ]

    const voucherColumns: Array<ColumnDef<TableFeatures, StatementVoucher>> = [
        {
            meta: { filterVariants: "range" }, id: "id", header: t("Finance.voucherId"),
            accessorKey: "id", filterFn: filterFn_inNumberRange,
        },
        {
            meta: { filterVariants: "value" }, id: "number", header: t("Finance.voucherNumber"),
            accessorKey: "number", filterFn: filterFn_includesString,
        },
        {
            meta: { filterVariants: "value" }, id: "date", header: t("Finance.voucherDate"),
            accessorKey: "date", filterFn: filterFn_includesString,
        },
        {
            meta: { filterVariants: "range" }, id: "amount", header: t("Finance.amount"),
            accessorKey: "amount", filterFn: filterFn_inNumberRange,
        },
        {
            meta: { filterVariants: "value" }, id: "reference", header: t("Finance.reference"),
            accessorKey: "reference", filterFn: filterFn_includesString,
        },
    ]

    if (isLoading) return <Text>{t("Approvals.loading")}</Text>
    if (!statement) return <Text>{t("Finance.noCustomers")}</Text>

    return (
        <div className="flex flex-col gap-y-8">
            <div className="flex flex-wrap gap-x-10 gap-y-4">
                <Figure label={t("customer")} value={statement.customer_name} />
                <Figure label={t("salesman")} value={statement.salesman_name ?? t("none")} />
                <Figure label={t("Finance.totalOrdered")} value={statement.total_ordered} />
                <Figure label={t("Finance.totalPaid")} value={statement.total_paid} />
                <Figure label={t("Finance.outstanding")} value={statement.outstanding} />
            </div>

            <div>
                <Text weight="medium" className="mb-3">{t("Finance.ordersHistory")}</Text>
                {statement.orders.length > 0
                    ? <Table<StatementOrder>
                        columns={orderColumns} data={statement.orders} tableKey="statementOrders"
                        sorting={orderSorting} setSorting={setOrderSorting} />
                    : <Text>{t("Finance.noOrders")}</Text>}
            </div>

            <div>
                <Text weight="medium" className="mb-3">{t("Finance.vouchersHistory")}</Text>
                {statement.vouchers.length > 0
                    ? <Table<StatementVoucher>
                        columns={voucherColumns} data={statement.vouchers} tableKey="statementVouchers"
                        sorting={voucherSorting} setSorting={setVoucherSorting} />
                    : <Text>{t("Finance.noVouchers")}</Text>}
            </div>
        </div>
    )
}
