import { HugeiconsIcon } from "@hugeicons/react"
import { CheckmarkCircle01Icon, Edit, Plus, Trash } from "@hugeicons/core-free-icons"
import Button from "../../../components/Button"
import useOpenMenu from "../../../hooks/useOpenMenu"
import Form from "../../../components/Form"
import ControlledInput from "../../../components/ControlledInput"
import { useForm } from "react-hook-form"
import type { Suppliers } from "../types/products"
import { useTranslation } from "react-i18next"
import { useEffect, useState } from "react"
import Model from "../../../components/Model"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { getSuppliers, postSuppliers } from "../services/products.service"
import { putSupplier, deleteSupplier } from "../services/products.service"
import { Table } from "../../../components/Table"
import { filterFn_includesString, filterFn_inNumberRange, type ColumnDef, type ColumnFiltersState, type ColumnVisibilityState, type GroupingState, type SortingState, type TableFeatures } from "@tanstack/react-table"
import Toast from "../../../components/Toast"
import Text from "../../../components/Text"
import { hasPermission } from "../../auth"
import { useBoundStore } from "../../../store/useBoundStore"
import { Link } from "react-router"
import TableFilter from "../../../components/TableFilter"
import TableSettings from "../../../components/TableSettings"
import DebouncedInput from "../../../components/DebouncedInput"

type NewSupplierFieldsValueState = Omit<Suppliers, "id">

const defaultProductValues: NewSupplierFieldsValueState = {
    name: "",
    phone: "",
}

export const SupplierPage = () => {
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
    const { data } = useQuery({
        queryKey: ["suppliers"],
        queryFn: getSuppliers
    })
    const queryClient = useQueryClient()

    const { mutate: addSupplier } = useMutation({
        mutationKey: ["suppliers", "new"],
        mutationFn: postSuppliers
    })

    const updateSupplier = useMutation({
        mutationKey: ["suppliers", "update"],
        mutationFn: ({ id, data }: { id: string, data: Omit<NewSupplierFieldsValueState, "id"> }) => putSupplier(id, data),
    })

    const deleteSupplierMutation = useMutation({
        mutationKey: ["suppliers", "delete"],
        mutationFn: (id: string) => deleteSupplier(id),
    })

    const { control, handleSubmit, reset, setError, clearErrors, formState: { errors } } = useForm<NewSupplierFieldsValueState>({
        defaultValues: defaultProductValues,
        mode: "all"
    })
    const [editingSupplierId, setEditingSupplierId] = useState<string | null>(null)
    const [deleteTarget, setDeleteTarget] = useState<null | Suppliers>(null)
    const [successMessage, setSuccessMessage] = useState<string | null>(null)
    const { t } = useTranslation()

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
        if (editingSupplierId) {
            updateSupplier.mutate({ id: editingSupplierId, data }, {
                onError(error) {
                    console.log(error)
                    setError("root.server", { type: "server", message: t("SuppliersMessages.serverError") })
                },
                onSuccess() {
                    reset(defaultProductValues)
                    clearErrors()
                    setEditingSupplierId(null)
                    setIsOpenAddModel(false)
                    setSuccessMessage(t("SuppliersMessages.updateSuccess"))
                    setIsOpenToast(true)
                    //@ts-ignore
                    queryClient.invalidateQueries(["suppliers"])
                }
            })
            return
        }

        addSupplier(data, {

            onError(error) {
                console.log(error);
                setError("root.server", { type: "server", message: t("SuppliersMessages.serverError") })
            },
            onSuccess() {
                reset(defaultProductValues)
                clearErrors()
                setIsOpenAddModel(false)
                setSuccessMessage(t("SuppliersMessages.createSuccess"))
                setIsOpenToast(true)
                //@ts-ignore
                queryClient.invalidateQueries(["suppliers"])
            },
        })
    }
    const columns: Array<ColumnDef<TableFeatures, Suppliers>> = [
        {
            id: "actions",
            enableColumnFilter: false,
            enableCellSelection: false,
            enableSorting: false,
            enableGrouping: false,
            header: t("actions"),
            cell: ({ row }) => (
                <div className="flex justify-center gap-x-2">
                    {hasPermission(user, "suppliers", "delete")
                        &&
                        <Button
                            className="dark:text-error text-error dark:hover:text-dark-text-error-hover hover:text-light-text-error-hover"
                            onClick={() => {
                                setDeleteTarget(row.original);
                                setIsOpenDeleteModel(true)
                            }}
                            size="xs" variants="ghost" iconOnly={true}
                            leftIcon={<HugeiconsIcon size={18} icon={Trash} />} />}
                    {hasPermission(user, "suppliers", "update")
                        &&
                        <Button
                            className="dark:text-accent-light text-accent-extraDark dark:hover:text-accent-extraLight hover:text-accent-dark"
                            onClick={() => {
                                setEditingSupplierId(row.original.id);
                                reset({ name: row.original.name, phone: row.original.phone });
                                setIsOpenAddModel(true)
                            }}
                            size="xs" variants="ghost" iconOnly={true} leftIcon={<HugeiconsIcon size={18} icon={Edit} />} />}
                </div>
            )

        },

        {
            meta: {
                filterVariants: "value"
            },
            id: "phone",
            enableSorting: true,
            header: t("phone"),
            accessorKey: "phone",
            filterFn: filterFn_includesString
        },
        {
            meta: {
                filterVariants: "value"
            },
            id: "name",
            enableSorting: true,
            header: t("name"),
            accessorKey: "name",
            filterFn: filterFn_includesString
        },
        {
            meta: {
                filterVariants: "range"
            },
            id: "id",
            enableSorting: true,
            header: t("id"),
            accessorKey: "id",
            //aggregationFn:"count",
            //footer: ({ column }) => column.getAggregationValue<string>().toLocaleString(),
            cell: ({ row }) => {
                // The supplier id opens that supplier's bills, filtered by the
                // `?supplier=` query the bills page reads.
                return hasPermission(user, "supplierBills", "read") ? <Link className="dark:text-accent-medium text-accent-dark" to={`/app/supplier/bills?supplier=${row.original.id}`} state={{ location: "supplierBills", details: row.original.name }}>{row.original.id}</Link> : row.original.id
            },
            filterFn: filterFn_inNumberRange
        },
        /*{
            id: "select-col",
            enableColumnFilter: false,
            enableCellSelection: false,
            header: ({ table }) => (
                <div className="flex justify-center">
                    <CheckBox
                        checked={table.getIsAllRowsSelected()}
                        indeterminate={table.getIsSomeRowsSelected()}
                        onClick={(e) => { table.getToggleAllRowsSelectedHandler()(e) }}
                    />
                </div>
            ),
            cell: ({ row }) => (
                <div className="flex justify-center">
                    <CheckBox
                        checked={
                            row.getIsSelected() ||
                            (row.getCanSelectSubRows() && row.getIsAllSubRowsSelected())
                        }
                        //disabled={!row.getCanSelect()}
                        indeterminate={row.getIsSomeSelected()}
                        onClick={(e) => { row.getToggleSelectedHandler()(e) }}
                    />
                </div>
            ),

        },*/
    ]

    return (
        <div>
            <Model title={t("Suppliers.newSuppliers")} isOpen={isOpenAddModel} onClick={() => setIsOpenAddModel(false)} ref={AddModelRef}>
                <Form ServerError={errors.root?.server} onSubmit={handleSubmit(onSubmit)} Buttons={<Button type="submit">{t("Suppliers.addSupplier")}</Button>}>
                    <div className="grid grid-cols-2 gap-x-6">
                        <ControlledInput<NewSupplierFieldsValueState>
                            rules={{
                                shouldUnregister: true,
                                required: { message: t("SuppliersMessages.nameRequired"), value: true },
                            }}
                            name="name"
                            control={control}
                        />
                        <ControlledInput<NewSupplierFieldsValueState>
                            rules={{
                                shouldUnregister: true,
                                required: { message: t("SuppliersMessages.phoneRequired"), value: true },
                                minLength: { message: t("SuppliersMessages.phoneMin"), value: 10 },
                            }}
                            name="phone"
                            control={control}
                        />

                    </div>
                </Form>
            </Model>
            <Model title={t("Suppliers.deleteTitle")} isOpen={isOpenDeleteModel} onClick={() => setIsOpenDeleteModel(false)} ref={DeleteModelRef}>
                <div className="p-4">
                    <Text>{t("Suppliers.deleteConfirm")}</Text>
                    <div className="flex justify-end gap-x-2 mt-4">
                        <Button variants="ghost" onClick={() => { setIsOpenDeleteModel(false); setDeleteTarget(null) }}>{t("Suppliers.cancel")}</Button>
                        <Button onClick={() => {
                            if (!deleteTarget) return
                            //@ts-ignore
                            deleteSupplierMutation.mutate(deleteTarget.id, {
                                onError(error) {
                                    console.log(error)
                                    setIsOpenDeleteModel(false)
                                },
                                onSuccess() {
                                    setIsOpenDeleteModel(false)
                                    const deletedId = deleteTarget?.id
                                    setDeleteTarget(null)
                                    setSuccessMessage(t("SuppliersMessages.deleteSuccess"))
                                    setIsOpenToast(true)
                                    // remove the deleted item from the queued/cache data so UI updates immediately
                                    //@ts-ignore
                                    queryClient.setQueryData(["suppliers"], (old: Suppliers[] | undefined) => {
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
                    <TableSettings<Suppliers>
                        columns={columns}
                        columnVisibility={columnVisibility} setColumnVisibility={setColumnVisibility}
                        grouping={grouping} setGrouping={setGrouping} />
                    <TableFilter<Suppliers> columns={columns} columnFilters={columnFilters} setColumnFilters={setColumnFilters} />
                    <DebouncedInput
                        fieldset={false}
                        rounded="full"
                        className="w-44"
                        placeholder={t("search") + "..."}
                        value={globalFilter}
                        onChange={setGlobalFilter}
                    />
                </div>
                {data ? <Table<Suppliers>
                    columns={columns}
                    data={data}
                    tableKey="suppliers"
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
