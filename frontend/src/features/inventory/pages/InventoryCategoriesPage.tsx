import { HugeiconsIcon } from "@hugeicons/react"
import { CheckmarkCircle01Icon, Edit, Plus, Trash } from "@hugeicons/core-free-icons"
import Button from "../../../components/Button"
import useOpenMenu from "../../../hooks/useOpenMenu"
import Form from "../../../components/Form"
import ControlledInput from "../../../components/ControlledInput"
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
import { Link } from "react-router"
import TableFilter from "../../../components/TableFilter"
import TableSettings from "../../../components/TableSettings"
import DebouncedInput from "../../../components/DebouncedInput"
import { getInventoryCategories, postInventoryCategory, putInventoryCategory, deleteInventoryCategory } from "../services/inventory.service"
import type { InventoryCategories } from "../types/inventory"

type NewSupplierFieldsValueState = Omit<InventoryCategories, "id">

const defaultProductValues: NewSupplierFieldsValueState = {
    name: "",
    description: "",
}

export const InventoryCategoriesPage = () => {
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
        queryKey: ["inventoryCategories"],
        queryFn: getInventoryCategories
    })
    const queryClient = useQueryClient()

    const { mutate: addSupplier } = useMutation({
        mutationKey: ["inventoryCategories", "new"],
        mutationFn: postInventoryCategory
    })

    const updateSupplier = useMutation({
        mutationKey: ["inventoryCategories", "update"],
        mutationFn: ({ id, data }: { id: string, data: Omit<NewSupplierFieldsValueState, "id"> }) => putInventoryCategory(id, data),
    })

    const deleteSupplierMutation = useMutation({
        mutationKey: ["inventoryCategories", "delete"],
        mutationFn: (id: string) => deleteInventoryCategory(id),
    })

    const { control, handleSubmit, reset, setError, clearErrors, formState: { errors } } = useForm<NewSupplierFieldsValueState>({
        defaultValues: defaultProductValues,
        mode: "all"
    })
    const [editingSupplierId, setEditingSupplierId] = useState<string | null>(null)
    const [deleteTarget, setDeleteTarget] = useState<null | InventoryCategories>(null)
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
                    setError("root.server", { type: "server", message: t("InventoryCategoriesMessages.serverError") })
                },
                onSuccess() {
                    reset(defaultProductValues)
                    clearErrors()
                    setEditingSupplierId(null)
                    setIsOpenAddModel(false)
                    setSuccessMessage(t("InventoryCategoriesMessages.updateSuccess"))
                    setIsOpenToast(true)
                    //@ts-ignore
                    queryClient.invalidateQueries(["inventoryCategories"])
                }
            })
            return
        }

        addSupplier(data, {

            onError(error) {
                console.log(error);
                setError("root.server", { type: "server", message: t("InventoryCategoriesMessages.serverError") })
            },
            onSuccess() {
                reset(defaultProductValues)
                clearErrors()
                setIsOpenAddModel(false)
                setSuccessMessage(t("InventoryCategoriesMessages.createSuccess"))
                setIsOpenToast(true)
                //@ts-ignore
                queryClient.invalidateQueries(["inventoryCategories"])
            },
        })
    }
    const columns: Array<ColumnDef<TableFeatures, InventoryCategories>> = [
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
                            onClick={() => {
                                setDeleteTarget(row.original);
                                setIsOpenDeleteModel(true)
                            }}
                            size="xs" variants="ghost" iconOnly={true}
                            leftIcon={<HugeiconsIcon size={18} icon={Trash} />} />}
                    {hasPermission(user, "suppliers", "update")
                        &&
                        <Button
                            onClick={() => {
                                setEditingSupplierId(row.original.id);
                                reset({ name: row.original.name, description: row.original.description });
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
            id: "name",
            enableSorting: true,
            header: t("name"),
            accessorKey: "name",
            filterFn: filterFn_includesString
        },
        {
            meta: {
                filterVariants: "value"
            },
            id: "description",
            enableSorting: false,
            enableGrouping:false,
            header: t("description"),
            accessorKey: "description",
            filterFn: filterFn_includesString
        },
        {
            meta: {
                filterVariants: "range"
            },
            id: "id",
            enableGrouping:false,
            enableSorting: true,
            header: t("id"),
            accessorKey: "id",
                cell: ({ row }) => {
                // Matches the `inventory/categories/:categoryId` route. This
                // used to be the only link to it, and no route matched it.
                return <Link className="dark:text-accent-medium text-accent-dark" to={`/app/inventory/categories/${row.original.id}/`} state={{location:"categoryDetails" , details:row.original.name}}>{row.original.id}</Link>
            },
            filterFn: filterFn_inNumberRange
        },

    ]

    return (
        <div>
            <Model title={t("InventoryCategories.newCategory")} isOpen={isOpenAddModel} onClick={() => setIsOpenAddModel(false)} ref={AddModelRef}>
                <Form ServerError={errors.root?.server} onSubmit={handleSubmit(onSubmit)} Buttons={<Button type="submit">{t("InventoryCategories.addCategory")}</Button>}>
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
                                required: { message: t("SuppliersMessages.nameRequired"), value: false },
                            }}
                            name="description"
                            control={control}
                        />

                    </div>
                </Form>
            </Model>
            <Model title={t("InventoryCategories.deleteTitle")} isOpen={isOpenDeleteModel} onClick={() => setIsOpenDeleteModel(false)} ref={DeleteModelRef}>
                <div className="p-4">
                    <Text>{t("InventoryCategories.deleteConfirm")}</Text>
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
                                    setSuccessMessage(t("InventoryCategoriesMessages.deleteSuccess"))
                                    setIsOpenToast(true)
                                    // remove the deleted item from the queued/cache data so UI updates immediately
                                    //@ts-ignore
                                    queryClient.setQueryData(["inventoryCategories"], (old: InventoryCategories[] | undefined) => {
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
                    <TableSettings<InventoryCategories>
                        columns={columns}
                        columnVisibility={columnVisibility} setColumnVisibility={setColumnVisibility}
                        grouping={grouping} setGrouping={setGrouping} />
                    <TableFilter<InventoryCategories> columns={columns} columnFilters={columnFilters} setColumnFilters={setColumnFilters} />
                    <DebouncedInput
                        fieldset={false}
                        rounded="full"
                        className="w-44"
                        placeholder={t("search")+"..."}
                        value={globalFilter}
                        onChange={setGlobalFilter}
                    />
                </div>
                {data ? <Table<InventoryCategories>
                    columns={columns}
                    data={data}
                    tableKey="inventoryCategories"
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
