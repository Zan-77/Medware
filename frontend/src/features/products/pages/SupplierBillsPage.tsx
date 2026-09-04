import { HugeiconsIcon } from "@hugeicons/react"
import { CheckmarkCircle01Icon, Edit, Plus, Trash, ViewIcon } from "@hugeicons/core-free-icons"
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
import { useNavigate, useSearchParams } from "react-router"
import TableFilter from "../../../components/TableFilter"
import TableSettings from "../../../components/TableSettings"
import DebouncedInput from "../../../components/DebouncedInput"
import { ControlledDateInput } from "../../../components/DateInput"
import { ControlledSearchSelectInput } from "../../../components/SearchSelectInput"
import { getSuppliers } from "../services/products.service"
import { getInventoryBills, postInventoryBill, putInventoryBill, deleteInventoryBill } from "../../inventory/services/inventory.service"
import type { SupplierBillls } from "../../inventory/types/inventory"
import ControlledTextArea from "../../../components/ControlledTextArea"

// Form fields, not the API shape: the inputs hold strings and
// `toSupplierBillPayload` converts them to what SupplierBillSerializer expects.
type NewSupplierFieldsValueState = {
    supplierId: string
    managerId: string
    date: string
    notes: string
}

const defaultProductValues: NewSupplierFieldsValueState = {
    supplierId: "",
    managerId: "",
    date: "",
    notes: "",
}

export const SupplierBillsPage = () => {
    //store
    const user = useBoundStore(state => state.authSlice.user)
    //menu state
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
    // `?supplier=` narrows the list to one supplier's bills - that is what the
    // id link on the suppliers table opens. The parameter is part of the query
    // key so switching suppliers refetches instead of showing the previous set.
    const [searchParams] = useSearchParams()
    const navigate = useNavigate()
    const supplierFilter = searchParams.get("supplier") ?? undefined
    const { data } = useQuery({
        queryKey: ["inventoryBills", supplierFilter ?? null],
        queryFn: () => getInventoryBills(supplierFilter)
    })
    const { data: suppliers = [] } = useQuery({
        queryKey: ["suppliersList"],
        queryFn: getSuppliers,
    })
    const supplierOptions = suppliers.map((supplier) => ({
        value: String(supplier.id),
        label: supplier.name,
    }))

    // Bills carry `supplier_name` from the serializer. This used to issue one
    // `getSuppliersById` request per distinct supplier in the table - and that
    // endpoint returned every supplier anyway, so the name was resolved by
    // scanning the whole list on the client.
    const supplierNameMap = new Map<string, string>(
        suppliers.map((supplier) => [String(supplier.id), supplier.name])
    )
    const queryClient = useQueryClient()

    const { mutate: addSupplier } = useMutation({
        mutationKey: ["inventoryBills", "new"],
        mutationFn: postInventoryBill
    })

    const updateSupplier = useMutation({
        mutationKey: ["inventoryBills", "update"],
        mutationFn: ({ id, data }: { id: string, data: Omit<SupplierBillls, "id"> }) => putInventoryBill(id, data),
    })

    const deleteSupplierMutation = useMutation({
        mutationKey: ["inventoryBills", "delete"],
        mutationFn: (id: string) => deleteInventoryBill(id),
    })

    const { control, handleSubmit, reset, setError, clearErrors, formState: { errors } } = useForm<NewSupplierFieldsValueState>({
        defaultValues: {
            ...defaultProductValues,
            managerId: user?.id ?? "",
        },
        mode: "all"
    })
    const [editingSupplierId, setEditingSupplierId] = useState<string | null>(null)
    const [deleteTarget, setDeleteTarget] = useState<null | SupplierBillls>(null)
    const [successMessage, setSuccessMessage] = useState<string | null>(null)
    const { t } = useTranslation()

    // Field names here are the serializer's, not the form's.
    const toSupplierBillPayload = (data: NewSupplierFieldsValueState): Omit<SupplierBillls, "id"> => ({
        supplier: data.supplierId ? Number(data.supplierId) : null,
        manager: data.managerId || user?.id || null,
        date: data.date,
        notes: data.notes ?? "",
    })

    useEffect(() => {
        if (!isOpenAddModel) {
            reset(defaultProductValues)
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

    const onSubmit = (data: NewSupplierFieldsValueState) => {
        clearErrors("root.server")
        const payload = toSupplierBillPayload(data)

        if (editingSupplierId) {
            updateSupplier.mutate({ id: editingSupplierId, data: payload }, {
                onError(error) {
                    console.log(error)
                    setError("root.server", { type: "server", message: t("InventoryBillsMessages.serverError") })
                },
                onSuccess() {
                    reset(defaultProductValues)
                    clearErrors()
                    setEditingSupplierId(null)
                    setIsOpenAddModel(false)
                    setSuccessMessage(t("InventoryBillsMessages.updateSuccess"))
                    setIsOpenToast(true)
                    queryClient.invalidateQueries({ queryKey: ["inventoryBills"] })
                }
            })
            return
        }

        addSupplier(payload, {

            onError(error) {
                console.log(error);
                setError("root.server", { type: "server", message: t("InventoryBillsMessages.serverError") })
            },
            onSuccess() {
                reset({
                    ...defaultProductValues,
                    managerId: user?.id ?? "",
                })
                clearErrors()
                setIsOpenAddModel(false)
                setSuccessMessage(t("InventoryBillsMessages.createSuccess"))
                setIsOpenToast(true)
                queryClient.invalidateQueries({ queryKey: ["inventoryBills"] })
            },
        })
    }
    const columns: Array<ColumnDef<TableFeatures, SupplierBillls>> = [
        {
            id: "actions",
            enableColumnFilter: false,
            enableCellSelection: false,
            enableSorting: false,
            enableGrouping: false,
            header: t("actions"),
            cell: ({ row }) => (
                <div className="flex justify-center gap-x-2">
                    {hasPermission(user, "supplierBillLines", "read")
                        &&
                        <Button
                            className="dark:text-accent-medium text-accent-dark dark:hover:text-accent-extraLight hover:text-accent-dark"
                            onClick={() => {
                                navigate(`/app/supplier/bills/${row.original.id}/`, {
                                    state: { location: "billDetails", details: row.original.supplier_name ?? "" },
                                })
                            }}
                            size="xs" variants="ghost"
                            leftIcon={<HugeiconsIcon size={18} icon={ViewIcon} />}>{t("details")}</Button>}
                    {hasPermission(user, "supplierBills", "delete")
                        &&
                        <Button
                            className="dark:text-error text-error dark:hover:text-dark-text-error-hover hover:text-light-text-error-hover"
                            onClick={() => {
                                setDeleteTarget(row.original);
                                setIsOpenDeleteModel(true)
                            }}
                            size="xs" variants="ghost" iconOnly={true}
                            leftIcon={<HugeiconsIcon size={18} icon={Trash} />} />}
                    {hasPermission(user, "supplierBills", "update")
                        &&
                        <Button
                        className="dark:text-accent-light text-accent-extraDark dark:hover:text-accent-extraLight hover:text-accent-dark"
                            onClick={() => {
                                setEditingSupplierId(row.original.id);
                                reset({
                                    supplierId: row.original.supplier != null ? String(row.original.supplier) : "",
                                    managerId: row.original.manager != null ? String(row.original.manager) : "",
                                    date: row.original.date,
                                    notes: row.original.notes,
                                });
                                setIsOpenAddModel(true)
                            }}
                            size="xs" variants="ghost" iconOnly={true} leftIcon={<HugeiconsIcon size={18} icon={Edit} />} />}

                </div>
            )

        },
        {
            meta: { filterVariants: "value" },
            id: "notes",
            enableSorting: true,
            header: t("notes"),
            accessorFn: (row) => row.notes?.trim() ? row.notes : t("noNotes"),
            cell: ({ row }) => row.original.notes?.trim() ? row.original.notes : t("noNotes"),
            filterFn: filterFn_includesString
        },

        {
            meta: { filterVariants: "value" },
            id: "supplierId",
            enableSorting: true,
            header: t("supplier"),
            accessorFn: (row) => row.supplier_name ?? supplierNameMap.get(String(row.supplier)) ?? String(row.supplier ?? ""),
            cell: ({ row }) => row.original.supplier_name ?? supplierNameMap.get(String(row.original.supplier)) ?? String(row.original.supplier ?? ""),
            filterFn: filterFn_includesString
        },

        {
            meta: { filterVariants: "value" },
            id: "date",
            enableSorting: true,
            header: t("date"),
            accessorKey: "date",
            filterFn: filterFn_includesString
        },
        {
            meta: {
                filterVariants: "range"
            },
            id: "id",
            enableGrouping: false,
            enableSorting: true,
            header: t("id"),
            accessorKey: "id",
            // The ID is data, not navigation. Bill details open from the
            // "details" action in the actions column.
            filterFn: filterFn_inNumberRange
        },

    ]

    return (
        <div>
            <Model title={t("InventoryBills.newBill")} isOpen={isOpenAddModel} onClick={() => setIsOpenAddModel(false)} ref={AddModelRef}>
                <Form ServerError={errors.root?.server} onSubmit={handleSubmit(onSubmit)} Buttons={<Button type="submit">{t("InventoryBills.addBill")}</Button>}>
                    <div className="grid grid-cols-2 gap-x-6">
                        <ControlledSearchSelectInput<NewSupplierFieldsValueState>
                            control={control}
                            name="supplierId"
                            label={t("supplier")}
                            rules={{
                                shouldUnregister: true,
                                required: { message: t("SuppliersMessages.nameRequired"), value: true },
                            }}
                            options={supplierOptions}
                            placeholder={t("search") + "..."}
                        />

                        <ControlledDateInput<NewSupplierFieldsValueState>
                            control={control}
                            name="date"
                            rules={{
                                shouldUnregister: true,
                                required: { message: t("SuppliersMessages.nameRequired"), value: true },
                            }}
                        />
                    </div>
                    <ControlledTextArea<NewSupplierFieldsValueState>
                        rules={{
                            shouldUnregister: true,
                        }}
                        placeholder={t("notes")}
                        name="notes"
                        control={control}
                    />

                </Form>
            </Model>
            <Model title={t("InventoryBills.deleteTitle")} isOpen={isOpenDeleteModel} onClick={() => setIsOpenDeleteModel(false)} ref={DeleteModelRef}>
                <div className="p-4">
                    <Text>{t("InventoryBills.deleteConfirm")}</Text>
                    <div className="flex justify-end gap-x-2 mt-4">
                        <Button variants="ghost" onClick={() => { setIsOpenDeleteModel(false); setDeleteTarget(null) }}>{t("Suppliers.cancel")}</Button>
                        <Button onClick={() => {
                            if (!deleteTarget) return
                            deleteSupplierMutation.mutate(deleteTarget.id, {
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
                                    queryClient.setQueryData(["inventoryBills", supplierFilter ?? null], (old: SupplierBillls[] | undefined) => {
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
                    {hasPermission(user, "suppliers", "create") && <Button onClick={() => { setIsOpenAddModel(true) }} variants="border" size="sm" iconOnly leftIcon={<HugeiconsIcon size={16} icon={Plus} />} />}
                    <TableSettings<SupplierBillls>
                        columns={columns}
                        columnVisibility={columnVisibility} setColumnVisibility={setColumnVisibility}
                        grouping={grouping} setGrouping={setGrouping} />
                    <TableFilter<SupplierBillls> columns={columns} columnFilters={columnFilters} setColumnFilters={setColumnFilters} />
                    <DebouncedInput
                        fieldset={false}
                        rounded="full"
                        className="w-44"
                        placeholder={t("search") + "..."}
                        value={globalFilter}
                        onChange={setGlobalFilter}
                    />
                </div>
                {data ? <Table<SupplierBillls>
                    columns={columns}
                    data={data}
                    tableKey="inventoryBills"
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
