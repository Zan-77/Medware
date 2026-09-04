import { HugeiconsIcon } from "@hugeicons/react"
import { Plus, ViewIcon } from "@hugeicons/core-free-icons"
import { useQuery } from "@tanstack/react-query"
import { filterFn_includesString, filterFn_inNumberRange, type ColumnDef, type ColumnFiltersState, type ColumnVisibilityState, type GroupingState, type SortingState, type TableFeatures } from "@tanstack/react-table"
import { useState } from "react"
import { useTranslation } from "react-i18next"
import { useNavigate } from "react-router"
import Button from "../../../components/Button"
import DebouncedInput from "../../../components/DebouncedInput"
import { Table } from "../../../components/Table"
import TableFilter from "../../../components/TableFilter"
import TableSettings from "../../../components/TableSettings"
import Text from "../../../components/Text"
import { useBoundStore } from "../../../store/useBoundStore"
import { hasPermission } from "../../auth"
import { getOrders } from "../services/orders.service"
import type { OrderRequest } from "../types/orders"

export const OrdersPage = () => {
    const user = useBoundStore(state => state.authSlice.user)
    const navigate = useNavigate()
    const { t } = useTranslation()

    const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([])
    const [sorting, setSorting] = useState<SortingState>([])
    const [grouping, setGrouping] = useState<GroupingState>([])
    const [globalFilter, setGlobalFilter] = useState('')
    const [columnVisibility, setColumnVisibility] = useState<ColumnVisibilityState>({
        id: true,
        customer: true,
        status: true,
    })

    const { data } = useQuery({ queryKey: ["orders"], queryFn: () => getOrders() })

    const columns: Array<ColumnDef<TableFeatures, OrderRequest>> = [
        {
            id: "actions",
            enableColumnFilter: false,
            enableCellSelection: false,
            enableSorting: false,
            enableGrouping: false,
            header: t("actions"),
            cell: ({ row }) => (
                <div className="flex justify-center gap-x-2">
                    <Button
                        className="dark:text-accent-medium text-accent-dark dark:hover:text-accent-extraLight hover:text-accent-dark"
                        onClick={() => navigate(`/app/orders/${row.original.id}/`, {
                            state: { location: "orders", details: row.original.customer_name ?? "" },
                        })}
                        size="xs" variants="ghost"
                        leftIcon={<HugeiconsIcon size={18} icon={ViewIcon} />}>{t("details")}</Button>
                </div>
            )
        },
        {
            meta: { filterVariants: "value" },
            id: "customer",
            enableSorting: true,
            header: t("customer"),
            accessorFn: (row) => row.customer_name ?? String(row.customer ?? ""),
            cell: ({ row }) => row.original.customer_name ?? String(row.original.customer ?? ""),
            filterFn: filterFn_includesString
        },
        {
            meta: { filterVariants: "value" },
            id: "salesman",
            enableSorting: true,
            header: t("salesman"),
            accessorFn: (row) => row.salesman_name ?? "",
            cell: ({ row }) => row.original.salesman_name ?? "",
            filterFn: filterFn_includesString
        },
        {
            meta: { filterVariants: "value" },
            id: "status",
            enableSorting: true,
            header: t("status"),
            accessorFn: (row) => t(`OrderStatus.${row.status}`),
            cell: ({ row }) => t(`OrderStatus.${row.original.status}`),
            filterFn: filterFn_includesString
        },
        {
            meta: { filterVariants: "range" },
            id: "total",
            enableSorting: true,
            header: t("orderTotal"),
            accessorKey: "total",
            filterFn: filterFn_inNumberRange
        },
        {
            meta: { filterVariants: "range" },
            id: "id",
            enableGrouping: false,
            enableSorting: true,
            header: t("id"),
            accessorKey: "id",
            filterFn: filterFn_inNumberRange
        },
    ]

    return (
        <div>
            <div className="flex items-center gap-x-3 mb-8">
                {hasPermission(user, "orders", "create") &&
                    <Button onClick={() => navigate("/app/orders/new", { state: { location: "newOrder" } })}
                        variants="border" size="sm" iconOnly
                        leftIcon={<HugeiconsIcon size={16} icon={Plus} />} />}
                <TableSettings<OrderRequest>
                    columns={columns}
                    columnVisibility={columnVisibility} setColumnVisibility={setColumnVisibility}
                    grouping={grouping} setGrouping={setGrouping} />
                <TableFilter<OrderRequest> columns={columns} columnFilters={columnFilters} setColumnFilters={setColumnFilters} />
                <DebouncedInput
                    fieldset={false}
                    rounded="full"
                    className="w-44"
                    placeholder={t("search") + "..."}
                    value={globalFilter}
                    onChange={setGlobalFilter}
                />
            </div>
            {data && data.length > 0 ? <Table<OrderRequest>
                columns={columns}
                data={data}
                tableKey="orders"
                columnFilters={columnFilters} setColumnFilters={setColumnFilters}
                columnVisibility={columnVisibility}
                setColumnVisibility={setColumnVisibility}
                sorting={sorting}
                setSorting={setSorting}
                grouping={grouping}
                setGrouping={setGrouping}
                globalFilter={globalFilter}
                setGlobalFilter={setGlobalFilter}
            /> : <Text>{t("Orders_.emptyInbox")}</Text>}
        </div>
    )
}
