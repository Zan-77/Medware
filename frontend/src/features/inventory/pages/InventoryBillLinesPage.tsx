import { HugeiconsIcon } from "@hugeicons/react"
import { CheckmarkCircle01Icon, Edit, Plus, Trash } from "@hugeicons/core-free-icons"
import Button from "../../../components/Button"
import useOpenMenu from "../../../hooks/useOpenMenu"
import { useForm } from "react-hook-form"
import { useTranslation } from "react-i18next"
import { useEffect, useState } from "react"
import Model from "../../../components/Model"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Table } from "../../../components/Table"
import { filterFn_includesString, filterFn_inNumberRange, type ColumnDef, type ColumnFiltersState, type ColumnVisibilityState, type GroupingState, type SortingState, type TableFeatures } from "@tanstack/react-table"
import Toast from "../../../components/Toast"
import Text from "../../../components/Text"
import { hasPermission } from "../../auth"
import { useBoundStore } from "../../../store/useBoundStore"
import TableFilter from "../../../components/TableFilter"
import TableSettings from "../../../components/TableSettings"
import DebouncedInput from "../../../components/DebouncedInput"
import { useParams } from "react-router"
import { getSupplierBillLineById, postSupplierBillLine, putSupplierBillLine, deleteSupplierBillLine, getInventoryCategories } from "../services/inventory.service"
import type { SupplierBilllLines } from "../types/inventory"

type NewBillLineFields = Omit<SupplierBilllLines, "id">

const defaultBillLineValues: NewBillLineFields = {
    billId: "",
    itemId: "",
    categoryId: "",
    quantity: 0,  
    expiry_date: "",
    unit_price: 0,
    discount: 0,
}

export const InventoryBillLinesPage = () => {
    const { billId } = useParams<{ billId: string }>()
    const user = useBoundStore(state => state.authSlice.user)
    const { isOpen: isOpenAddModel, setIsOpen: setIsOpenAddModel, ref: AddModelRef } = useOpenMenu()
    const { isOpen: isOpenDeleteModel, setIsOpen: setIsOpenDeleteModel, ref: DeleteModelRef } = useOpenMenu()
    const { isOpen: isOpenToast, setIsOpen: setIsOpenToast, ref: toastRef } = useOpenMenu()
    //table state
    const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([])
    const [sorting, setSorting] = useState<SortingState>([])
    const [grouping, setGrouping] = useState<GroupingState>([])
    const [globalFilter, setGlobalFilter] = useState('')
    const [columnVisibility, setColumnVisibility] = useState<ColumnVisibilityState>({
        id: true,
        phone: true,
        name: true
    })
    
    // query
    const { data } = useQuery({
        queryKey: ["inventoryBillLines", billId],
        queryFn: () => getSupplierBillLineById(String(billId ?? "")),
        enabled: Boolean(billId),
    })
    const { data: categories = [] } = useQuery({ queryKey: ["inventoryCategories"], queryFn: getInventoryCategories })

    const categoryMap = new Map<string, string>(categories.map(c => [String(c.id), c.name]))
    const queryClient = useQueryClient()

    const { mutate: addBillLine } = useMutation({
        mutationKey: ["inventoryBillLines", "new"],
        mutationFn: postSupplierBillLine
    })

    const updateBillLine = useMutation({
        mutationKey: ["inventoryBillLines", "update"],
        mutationFn: ({ id, data }: { id: string, data: Omit<NewBillLineFields, "id"> }) => putSupplierBillLine(id, data),
    })

    const deleteBillLineMutation = useMutation({
        mutationKey: ["inventoryBillLines", "delete"],
        mutationFn: (id: string) => deleteSupplierBillLine(id),
    })

    const { reset, setError, clearErrors, handleSubmit, formState: { errors } } = useForm<NewBillLineFields>({
        defaultValues: {
            ...defaultBillLineValues,
        },
        mode: "all"
    })
    const [editingBillLineId, setEditingBillLineId] = useState<string | null>(null)
    const [deleteTarget, setDeleteTarget] = useState<null | SupplierBilllLines>(null)
    const [successMessage, setSuccessMessage] = useState<string | null>(null)
    const { t } = useTranslation()

    const toBillLinePayload = (data: NewBillLineFields) => ({
        bill: data.billId ? Number(data.billId) : null,
        item: data.itemId ? Number(data.itemId) : null,
        category: data.categoryId ? Number(data.categoryId) : null,
        quantity: data.quantity,
        expiry_date: data.expiry_date,
        unit_price: data.unit_price,
        discount: data.discount,
    })

    useEffect(() => {
        if (!isOpenAddModel) {
            reset(defaultBillLineValues)
            clearErrors()
        }
    }, [isOpenAddModel, clearErrors, reset])

    useEffect(() => {
        if (!isOpenToast) return

        const timeoutId = window.setTimeout(() => {
            setIsOpenToast(false)
            setSuccessMessage(null)
        }, 3000)

        return () => window.clearTimeout(timeoutId)
    }, [isOpenToast, setIsOpenToast, setSuccessMessage])

    const onSubmit = (data: NewBillLineFields) => {
        clearErrors("root.server")
        const payload = toBillLinePayload(data)

        if (editingBillLineId) {
            updateBillLine.mutate({ id: editingBillLineId, data: payload as any }, {
                onError(error) {
                    console.log(error)
                    setError("root.server", { type: "server", message: t("InventoryBillsMessages.serverError") })
                },
                onSuccess() {
                    reset(defaultBillLineValues)
                    clearErrors()
                    setEditingBillLineId(null)
                    setIsOpenAddModel(false)
                    setSuccessMessage(t("InventoryBillsMessages.updateSuccess"))
                    setIsOpenToast(true)
                    //@ts-ignore
                    queryClient.invalidateQueries(["inventoryBillLines"])
                }
            })
            return
        }

        addBillLine(payload as any, {

            onError(error) {
                console.log(error);
                setError("root.server", { type: "server", message: t("InventoryBillsMessages.serverError") })
            },
            onSuccess() {
                reset({
                    ...defaultBillLineValues,
                })
                clearErrors()
                setIsOpenAddModel(false)
                setSuccessMessage(t("InventoryBillsMessages.createSuccess"))
                setIsOpenToast(true)
                //@ts-ignore
                queryClient.invalidateQueries(["inventoryBillLines"])
            },
        })
    }
    const columns: Array<ColumnDef<TableFeatures, SupplierBilllLines>> = [
        {
            id: "actions",
            enableColumnFilter: false,
            enableCellSelection: false,
            enableSorting: false,
            enableGrouping: false,
            header: t("actions"),
            cell: ({ row }) => (
                <div className="flex justify-center gap-x-2">
                    {hasPermission(user, "supplierBillLines", "delete")
                        &&
                        <Button
                            className="dark:text-error text-error dark:hover:text-dark-text-error-hover hover:text-light-text-error-hover"
                            onClick={() => {
                                setDeleteTarget(row.original);
                                setIsOpenDeleteModel(true)
                            }}
                            size="xs" variants="ghost" iconOnly={true}
                            leftIcon={<HugeiconsIcon size={18} icon={Trash} />} />}
                    {hasPermission(user, "supplierBillLines", "update")
                        &&
                        <Button
                        className="dark:text-accent-light text-accent-extraDark dark:hover:text-accent-extraLight hover:text-accent-dark"
                            onClick={() => {
                                setEditingBillLineId(row.original.id);
                                reset({ billId: row.original.billId, itemId: row.original.itemId, categoryId: row.original.categoryId, quantity: row.original.quantity, expiry_date: row.original.expiry_date, unit_price: row.original.unit_price, discount: row.original.discount });
                                setIsOpenAddModel(true)
                            }}
                            size="xs" variants="ghost" iconOnly={true} leftIcon={<HugeiconsIcon size={18} icon={Edit} />} />}

                </div>
            )

        },
        {
            meta: { filterVariants: "value" },
            id: "itemId",
            enableSorting: true,
            header: t("item"),
            accessorKey: "itemId",
            filterFn: filterFn_includesString
        },
        {
            meta: { filterVariants: "value" },
            id: "categoryId",
            enableSorting: true,
            header: t("category"),
            accessorFn: (row) => categoryMap.get(String(row.categoryId)) ?? String(row.categoryId ?? ""),
            cell: ({ row }) => categoryMap.get(String(row.original.categoryId)) ?? String(row.original.categoryId ?? ""),
            filterFn: filterFn_includesString
        },
        
        {
            meta: { filterVariants: "range" },
            id: "quantity",
            enableSorting: true,
            header: t("quantity"),
            accessorKey: "quantity",
            filterFn: filterFn_inNumberRange
        },
        {
            meta: { filterVariants: "range" },
            id: "unit_price",
            enableSorting: true,
            header: t("unit_price"),
            accessorKey: "unit_price",
            filterFn: filterFn_inNumberRange
        },
        {
            meta: { filterVariants: "range" },    
            id: "discount",
            enableSorting: true,
            header: t("discount"),
            accessorKey: "discount",
            filterFn: filterFn_inNumberRange
        },
        {
            meta: { filterVariants: "value" },
            id: "expiry_date",
            enableSorting: true,
            header: t("expiry_date"),
            accessorKey: "expiry_date",
            filterFn: filterFn_includesString
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
            <Model title={t("InventoryBills.newBill")} isOpen={isOpenAddModel} onClick={() => setIsOpenAddModel(false)} ref={AddModelRef}>
                <form onSubmit={handleSubmit(onSubmit)} className="p-4">
                    <div>{t("InventoryBills.createEditNotImplemented") || "Create/Edit bill lines is not implemented yet."}</div>
                    {errors.root?.server && <Text className="mt-2 text-error">{errors.root.server.message}</Text>}
                </form>
            </Model>
            <Model title={t("InventoryBills.deleteTitle")} isOpen={isOpenDeleteModel} onClick={() => setIsOpenDeleteModel(false)} ref={DeleteModelRef}>
                <div className="p-4">
                    <Text>{t("InventoryBills.deleteConfirm")}</Text>
                    <div className="flex justify-end gap-x-2 mt-4">
                        <Button variants="ghost" onClick={() => { setIsOpenDeleteModel(false); setDeleteTarget(null) }}>{t("Suppliers.cancel")}</Button>
                        <Button onClick={() => {
                            if (!deleteTarget) return
                            //@ts-ignore
                            deleteBillLineMutation.mutate(deleteTarget.id, {
                                onError(error) {
                                    console.log(error)
                                    setIsOpenDeleteModel(false)
                                },
                                onSuccess() {
                                    setIsOpenDeleteModel(false)
                                    const deletedId = deleteTarget?.id
                                    setDeleteTarget(null)
                                    setSuccessMessage(t("InventoryBillsMessages.deleteSuccess"))
                                    setIsOpenToast(true)
                                    // remove the deleted item from the queued/cache data so UI updates immediately
                                    //@ts-ignore
                                    queryClient.setQueryData(["inventoryBillLines"], (old: SupplierBilllLines[] | undefined) => {
                                        if (!old) return old
                                        return old.filter(item => (item as any).id !== deletedId)
                                    })
                                }
                            })
                        }}>{t("Suppliers.confirm")}</Button>
                    </div>
                </div>
            </Model>
            <Toast onClick={() => { setIsOpenToast(false); setSuccessMessage(null) }} isOpen={isOpenToast} ref={toastRef}>
                {successMessage && <div className="flex items-center gap-x-2 "><HugeiconsIcon className="*:fill-ok *:stroke-white" size={24} icon={CheckmarkCircle01Icon} /> <Text>{successMessage}</Text></div>}
            </Toast>
            <div>
                <div className="flex items-center gap-x-3 mb-8">
                    {hasPermission(user, "supplierBillLines", "create") && <Button onClick={() => { setIsOpenAddModel(true) }} variants="border" size="sm" iconOnly leftIcon={<HugeiconsIcon size={16} icon={Plus} />} />}
                    <TableSettings<SupplierBilllLines>
                        columns={columns}
                        columnVisibility={columnVisibility} setColumnVisibility={setColumnVisibility}
                        grouping={grouping} setGrouping={setGrouping} />
                    <TableFilter<SupplierBilllLines> columns={columns} columnFilters={columnFilters} setColumnFilters={setColumnFilters} />
                    <DebouncedInput
                        fieldset={false}
                        rounded="full"
                        className="w-44"
                        placeholder={t("search") + "..."}
                        value={globalFilter}
                        onChange={setGlobalFilter}
                    />
                </div>
                {data ? <Table<SupplierBilllLines>
                    columns={columns}
                    data={data}
                    tableKey="inventoryBillLines"
                    columnFilters={columnFilters} setColumnFilters={setColumnFilters}
                    columnVisibility={columnVisibility}
                    setColumnVisibility={setColumnVisibility}
                    sorting={sorting}
                    setSorting={setSorting}
                    grouping={grouping}
                    setGrouping={setGrouping}
                    globalFilter={globalFilter}
                    setGlobalFilter={setGlobalFilter}
                /> : <Text>no items</Text>}
            </div>
        </div>
    )
}
