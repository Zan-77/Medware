import { HugeiconsIcon } from "@hugeicons/react"
import { CheckmarkCircle01Icon, Edit, Plus, Trash } from "@hugeicons/core-free-icons"
import Button from "../../../components/Button"
import useOpenMenu from "../../../hooks/useOpenMenu"
import Form from "../../../components/Form"
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
import ControlledInput from "../../../components/ControlledInput"
import { ControlledDateInput } from "../../../components/DateInput"
import { ControlledSearchSelectInput } from "../../../components/SearchSelectInput"
import { useParams } from "react-router"
import { getSupplierBillLinesById, postSupplierBillLine, putSupplierBillLine, deleteSupplierBillLine, getInventoryCategories, getInventoryItems } from "../../inventory/services/inventory.service"
import type { SupplierBilllLines } from "../../inventory/types/inventory"

// Form fields are kept as strings because that is what the inputs produce;
// `toBillLinePayload` converts them to the shapes the API expects.
type NewBillLineFields = {
    item: string
    category: string
    quantity: string
    expiry_date: string
    unit_price: string
    discount: string
}

const defaultBillLineValues: NewBillLineFields = {
    item: "",
    category: "",
    quantity: "",
    expiry_date: "",
    unit_price: "",
    discount: "",
}

export const SupplierBillLinesPage = () => {
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
        item: true,
        category: true,
    })

    // query - `billLinesKey` is the single source of truth for this page's cache
    // entry. Every invalidate/setQueryData below reuses it; a bare
    // ["inventoryBillLines"] key matches nothing and left deleted rows on screen.
    const billLinesKey = ["inventoryBillLines", billId] as const
    const { data } = useQuery({
        queryKey: billLinesKey,
        queryFn: () => getSupplierBillLinesById(String(billId)),
        enabled: Boolean(billId),
    })
    const { data: categories = [] } = useQuery({ queryKey: ["inventoryCategories"], queryFn: getInventoryCategories })
    const { data: items = [] } = useQuery({ queryKey: ["inventoryItems"], queryFn: () => getInventoryItems() })

    const categoryOptions = categories.map((category) => ({
        value: String(category.id),
        label: category.name,
    }))
    const itemOptions = items.map((item) => ({
        value: String(item.id),
        label: item.name,
    }))
    const queryClient = useQueryClient()

    const { mutate: addBillLine } = useMutation({
        mutationKey: ["inventoryBillLines", "new"],
        mutationFn: postSupplierBillLine
    })

    const updateBillLine = useMutation({
        mutationKey: ["inventoryBillLines", "update"],
        mutationFn: ({ id, data }: { id: string, data: Omit<SupplierBilllLines, "id"> }) => putSupplierBillLine(id, data),
    })

    const deleteBillLineMutation = useMutation({
        mutationKey: ["inventoryBillLines", "delete"],
        mutationFn: (id: string) => deleteSupplierBillLine(id),
    })

    const { control, reset, setError, clearErrors, handleSubmit, formState: { errors } } = useForm<NewBillLineFields>({
        defaultValues: defaultBillLineValues,
        mode: "all"
    })
    const [editingBillLineId, setEditingBillLineId] = useState<string | null>(null)
    const [deleteTarget, setDeleteTarget] = useState<null | SupplierBilllLines>(null)
    const [successMessage, setSuccessMessage] = useState<string | null>(null)
    const { t } = useTranslation()

    // The API names these after the model fields, and `bill` always comes from
    // the route rather than the form - a line belongs to the bill you are
    // looking at.
    const toBillLinePayload = (fields: NewBillLineFields): Omit<SupplierBilllLines, "id"> => ({
        bill: Number(billId),
        item: fields.item ? Number(fields.item) : null,
        category: fields.category ? Number(fields.category) : null,
        quantity: Number(fields.quantity),
        expiry_date: fields.expiry_date || null,
        unit_price: fields.unit_price === "" ? null : Number(fields.unit_price),
        discount: fields.discount === "" ? null : Number(fields.discount),
    })

    useEffect(() => {
        if (!isOpenAddModel) {
            reset(defaultBillLineValues)
            clearErrors()
            setEditingBillLineId(null)
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

    const onSubmit = (fields: NewBillLineFields) => {
        clearErrors("root.server")
        if (!billId) {
            setError("root.server", { type: "server", message: t("InventoryBillLines.billMissing") })
            return
        }
        const payload = toBillLinePayload(fields)

        if (editingBillLineId) {
            updateBillLine.mutate({ id: editingBillLineId, data: payload }, {
                onError(error) {
                    console.log(error)
                    setError("root.server", { type: "server", message: t("InventoryBillLinesMessages.serverError") })
                },
                onSuccess() {
                    reset(defaultBillLineValues)
                    clearErrors()
                    setEditingBillLineId(null)
                    setIsOpenAddModel(false)
                    setSuccessMessage(t("InventoryBillLinesMessages.updateSuccess"))
                    setIsOpenToast(true)
                    queryClient.invalidateQueries({ queryKey: billLinesKey })
                }
            })
            return
        }

        addBillLine(payload, {

            onError(error) {
                console.log(error);
                setError("root.server", { type: "server", message: t("InventoryBillLinesMessages.serverError") })
            },
            onSuccess() {
                reset(defaultBillLineValues)
                clearErrors()
                setIsOpenAddModel(false)
                setSuccessMessage(t("InventoryBillLinesMessages.createSuccess"))
                setIsOpenToast(true)
                queryClient.invalidateQueries({ queryKey: billLinesKey })
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
                                reset({
                                    item: row.original.item != null ? String(row.original.item) : "",
                                    category: row.original.category != null ? String(row.original.category) : "",
                                    quantity: String(row.original.quantity ?? ""),
                                    expiry_date: row.original.expiry_date ?? "",
                                    unit_price: row.original.unit_price != null ? String(row.original.unit_price) : "",
                                    discount: row.original.discount != null ? String(row.original.discount) : "",
                                });
                                setIsOpenAddModel(true)
                            }}
                            size="xs" variants="ghost" iconOnly={true} leftIcon={<HugeiconsIcon size={18} icon={Edit} />} />}

                </div>
            )

        },
        {
            meta: { filterVariants: "value" },
            id: "item",
            enableSorting: true,
            header: t("item"),
            // `item_name` is supplied by the serializer; the id is the fallback
            // for a line whose item row has since been deleted.
            accessorFn: (row) => row.item_name ?? String(row.item ?? ""),
            cell: ({ row }) => row.original.item_name ?? String(row.original.item ?? ""),
            filterFn: filterFn_includesString
        },
        {
            meta: { filterVariants: "value" },
            id: "category",
            enableSorting: true,
            header: t("category"),
            accessorFn: (row) => row.category_name ?? String(row.category ?? ""),
            cell: ({ row }) => row.original.category_name ?? String(row.original.category ?? ""),
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
            <Model title={editingBillLineId ? t("InventoryBillLines.editLine") : t("InventoryBillLines.newLine")} isOpen={isOpenAddModel} onClick={() => setIsOpenAddModel(false)} ref={AddModelRef}>
                <Form ServerError={errors.root?.server} onSubmit={handleSubmit(onSubmit)} Buttons={<Button type="submit">{t("InventoryBillLines.addLine")}</Button>}>
                    <div className="grid grid-cols-2 gap-x-6">
                        <ControlledSearchSelectInput<NewBillLineFields>
                            control={control}
                            name="item"
                            label={t("item")}
                            rules={{
                                shouldUnregister: true,
                                required: { message: t("InventoryBillLinesMessages.itemRequired"), value: true },
                            }}
                            options={itemOptions}
                            placeholder={t("search") + "..."}
                        />
                        <ControlledSearchSelectInput<NewBillLineFields>
                            control={control}
                            name="category"
                            label={t("category")}
                            rules={{
                                shouldUnregister: true,
                                required: { message: t("InventoryBillLinesMessages.categoryRequired"), value: true },
                            }}
                            options={categoryOptions}
                            placeholder={t("search") + "..."}
                        />
                        <ControlledInput<NewBillLineFields>
                            rules={{
                                shouldUnregister: true,
                                required: { message: t("InventoryBillLinesMessages.quantityRequired"), value: true },
                                min: { message: t("InventoryBillLinesMessages.quantityMin"), value: 1 },
                            }}
                            name="quantity"
                            type="number"
                            control={control}
                        />
                        <ControlledInput<NewBillLineFields>
                            rules={{
                                shouldUnregister: true,
                                min: { message: t("InventoryBillLinesMessages.priceMin"), value: 0 },
                            }}
                            name="unit_price"
                            type="number"
                            control={control}
                        />
                        <ControlledInput<NewBillLineFields>
                            rules={{
                                shouldUnregister: true,
                                min: { message: t("InventoryBillLinesMessages.priceMin"), value: 0 },
                            }}
                            name="discount"
                            type="number"
                            control={control}
                        />
                        <ControlledDateInput<NewBillLineFields>
                            control={control}
                            name="expiry_date"
                            rules={{ shouldUnregister: true }}
                        />
                    </div>
                </Form>
            </Model>
            <Model title={t("InventoryBillLines.deleteTitle")} isOpen={isOpenDeleteModel} onClick={() => setIsOpenDeleteModel(false)} ref={DeleteModelRef}>
                <div className="p-4">
                    <Text>{t("InventoryBillLines.deleteConfirm")}</Text>
                    <div className="flex justify-end gap-x-2 mt-4">
                        <Button variants="ghost" onClick={() => { setIsOpenDeleteModel(false); setDeleteTarget(null) }}>{t("Suppliers.cancel")}</Button>
                        <Button onClick={() => {
                            if (!deleteTarget) return
                            deleteBillLineMutation.mutate(deleteTarget.id, {
                                onError(error) {
                                    console.log(error)
                                    setIsOpenDeleteModel(false)
                                },
                                onSuccess() {
                                    setIsOpenDeleteModel(false)
                                    const deletedId = deleteTarget?.id
                                    setDeleteTarget(null)
                                    setSuccessMessage(t("InventoryBillLinesMessages.deleteSuccess"))
                                    setIsOpenToast(true)
                                    // remove the deleted item from the cached data so UI updates immediately
                                    queryClient.setQueryData(billLinesKey, (old: SupplierBilllLines[] | undefined) => {
                                        if (!old) return old
                                        return old.filter(item => item.id !== deletedId)
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
