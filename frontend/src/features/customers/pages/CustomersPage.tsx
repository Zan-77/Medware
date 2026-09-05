import { HugeiconsIcon } from "@hugeicons/react"
import { CheckmarkCircle01Icon, Edit, Plus, Trash, ViewIcon } from "@hugeicons/core-free-icons"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { filterFn_includesString, filterFn_inNumberRange, type ColumnDef, type ColumnFiltersState, type ColumnVisibilityState, type GroupingState, type SortingState, type TableFeatures } from "@tanstack/react-table"
import { useEffect, useState } from "react"
import { useForm } from "react-hook-form"
import { useTranslation } from "react-i18next"
import Button from "../../../components/Button"
import ControlledInput from "../../../components/ControlledInput"
import ControlledTextArea from "../../../components/ControlledTextArea"
import DebouncedInput from "../../../components/DebouncedInput"
import Form from "../../../components/Form"
import Model from "../../../components/Model"
import { Table } from "../../../components/Table"
import TableFilter from "../../../components/TableFilter"
import TableSettings from "../../../components/TableSettings"
import Text from "../../../components/Text"
import Toast from "../../../components/Toast"
import useOpenMenu from "../../../hooks/useOpenMenu"
import { useBoundStore } from "../../../store/useBoundStore"
import { hasPermission } from "../../auth"
import { approveCustomer, deleteCustomer, getCustomers, postCustomer, putCustomer, rejectCustomer } from "../services/customers.service"
import type { Customer } from "../types/customers"

type CustomerFields = { name: string; phone: string; address: string; notes: string }
type RejectFields = { notes: string }

const emptyCustomer: CustomerFields = { name: "", phone: "", address: "", notes: "" }

export const CustomersPage = () => {
    const user = useBoundStore(state => state.authSlice.user)
    const { t } = useTranslation()
    const queryClient = useQueryClient()

    const { isOpen: isOpenAddModel, setIsOpen: setIsOpenAddModel, ref: addRef } = useOpenMenu()
    const { isOpen: isOpenDeleteModel, setIsOpen: setIsOpenDeleteModel, ref: deleteRef } = useOpenMenu()
    const { isOpen: isOpenRejectModel, setIsOpen: setIsOpenRejectModel, ref: rejectRef } = useOpenMenu()
    const { isOpen: isOpenToast, setIsOpen: setIsOpenToast, ref: toastRef } = useOpenMenu()

    const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([])
    const [sorting, setSorting] = useState<SortingState>([])
    const [grouping, setGrouping] = useState<GroupingState>([])
    const [globalFilter, setGlobalFilter] = useState('')
    const [columnVisibility, setColumnVisibility] = useState<ColumnVisibilityState>({
        id: true, name: true, status: true,
    })
    const [editingId, setEditingId] = useState<string | null>(null)
    const [deleteTarget, setDeleteTarget] = useState<Customer | null>(null)
    const [rejectTarget, setRejectTarget] = useState<Customer | null>(null)
    const [successMessage, setSuccessMessage] = useState<string | null>(null)

    const { data } = useQuery({ queryKey: ["customers"], queryFn: () => getCustomers() })

    const { control, handleSubmit, reset, setError, clearErrors, formState: { errors } } =
        useForm<CustomerFields>({ defaultValues: emptyCustomer, mode: "all" })

    const rejectForm = useForm<RejectFields>({ defaultValues: { notes: "" }, mode: "all" })

    const invalidate = () => queryClient.invalidateQueries({ queryKey: ["customers"] })

    const create = useMutation({ mutationFn: postCustomer })
    const update = useMutation({
        mutationFn: ({ id, values }: { id: string; values: CustomerFields }) => putCustomer(id, values),
    })
    const remove = useMutation({ mutationFn: (id: string) => deleteCustomer(id) })
    const approve = useMutation({
        mutationFn: (id: string) => approveCustomer(id),
        onSuccess() {
            setSuccessMessage(t("Customers_.approveSuccess")); setIsOpenToast(true); invalidate()
        },
        onError() { setError("root.server", { type: "server", message: t("Customers_.serverError") }) },
    })
    const rejectMutation = useMutation({
        mutationFn: ({ id, notes }: { id: string; notes: string }) => rejectCustomer(id, notes),
        onSuccess() {
            setIsOpenRejectModel(false); setRejectTarget(null); rejectForm.reset({ notes: "" })
            setSuccessMessage(t("Customers_.rejectSuccess")); setIsOpenToast(true); invalidate()
        },
        onError() {
            rejectForm.setError("root.server", { type: "server", message: t("Customers_.serverError") })
        },
    })

    useEffect(() => {
        if (!isOpenAddModel) { reset(emptyCustomer); clearErrors(); setEditingId(null) }
    }, [isOpenAddModel, clearErrors, reset])

    useEffect(() => {
        if (!isOpenToast) return
        const id = window.setTimeout(() => { setIsOpenToast(false); setSuccessMessage(null) }, 3000)
        return () => window.clearTimeout(id)
    }, [isOpenToast, setIsOpenToast])

    const onSubmit = (values: CustomerFields) => {
        clearErrors("root.server")
        const onError = () => setError("root.server", { type: "server", message: t("Customers_.serverError") })
        const onDone = (message: string) => {
            setIsOpenAddModel(false); setSuccessMessage(message); setIsOpenToast(true); invalidate()
        }
        if (editingId) {
            update.mutate({ id: editingId, values }, {
                onError, onSuccess: () => onDone(t("Customers_.updateSuccess")),
            })
            return
        }
        create.mutate(values, { onError, onSuccess: () => onDone(t("Customers_.createSuccess")) })
    }

    // Mirrors the server rule: a manager may edit anything, a salesman only
    // their own record and only while it is still pending.
    const canEdit = (row: Customer) =>
        hasPermission(user, "customerApproval", "update") ||
        (hasPermission(user, "customers", "update") &&
            String(row.created_by ?? "") === String(user.id) &&
            row.status === "PENDING")

    const columns: Array<ColumnDef<TableFeatures, Customer>> = [
        {
            id: "actions",
            enableColumnFilter: false, enableCellSelection: false,
            enableSorting: false, enableGrouping: false,
            header: t("actions"),
            cell: ({ row }) => (
                <div className="flex justify-center gap-x-2">
                    {hasPermission(user, "customerApproval", "update") && row.original.status === "PENDING" && <>
                        <Button
                            className="dark:text-accent-medium text-accent-dark"
                            size="xs" variants="ghost"
                            onClick={() => approve.mutate(row.original.id)}
                            leftIcon={<HugeiconsIcon size={18} icon={ViewIcon} />}>{t("approve")}</Button>
                        <Button
                            className="dark:text-error text-error"
                            size="xs" variants="ghost"
                            onClick={() => { setRejectTarget(row.original); setIsOpenRejectModel(true) }}>
                            {t("reject")}
                        </Button>
                    </>}
                    {hasPermission(user, "customers", "delete") &&
                        <Button
                            className="dark:text-error text-error dark:hover:text-dark-text-error-hover hover:text-light-text-error-hover"
                            onClick={() => { setDeleteTarget(row.original); setIsOpenDeleteModel(true) }}
                            size="xs" variants="ghost" iconOnly
                            leftIcon={<HugeiconsIcon size={18} icon={Trash} />} />}
                    {canEdit(row.original) &&
                        <Button
                            className="dark:text-accent-light text-accent-extraDark dark:hover:text-accent-extraLight hover:text-accent-dark"
                            onClick={() => {
                                setEditingId(row.original.id)
                                reset({
                                    name: row.original.name, phone: row.original.phone,
                                    address: row.original.address, notes: row.original.notes,
                                })
                                setIsOpenAddModel(true)
                            }}
                            size="xs" variants="ghost" iconOnly
                            leftIcon={<HugeiconsIcon size={18} icon={Edit} />} />}
                </div>
            ),
        },
        {
            meta: { filterVariants: "value" }, id: "name", enableSorting: true,
            header: t("name"), accessorKey: "name", filterFn: filterFn_includesString,
        },
        {
            meta: { filterVariants: "value" }, id: "phone", enableSorting: true,
            header: t("phone_"), accessorKey: "phone", filterFn: filterFn_includesString,
        },
        {
            meta: { filterVariants: "value" }, id: "status", enableSorting: true,
            header: t("status"),
            accessorFn: (row) => t(`CustomerStatus.${row.status}`),
            cell: ({ row }) => t(`CustomerStatus.${row.original.status}`),
            filterFn: filterFn_includesString,
        },
        {
            meta: { filterVariants: "value" }, id: "created_by", enableSorting: true,
            header: t("createdBy"),
            accessorFn: (row) => row.created_by_name ?? "",
            cell: ({ row }) => row.original.created_by_name ?? "",
            filterFn: filterFn_includesString,
        },
        {
            meta: { filterVariants: "range" }, id: "id", enableGrouping: false,
            enableSorting: true, header: t("id"), accessorKey: "id",
            filterFn: filterFn_inNumberRange,
        },
    ]

    return (
        <div>
            <Model title={editingId ? t("Customers_.editCustomer") : t("Customers_.newCustomer")}
                isOpen={isOpenAddModel} onClick={() => setIsOpenAddModel(false)} ref={addRef}>
                <Form ServerError={errors.root?.server} onSubmit={handleSubmit(onSubmit)}
                    Buttons={<Button type="submit">{t("Customers_.addCustomer")}</Button>}>
                    <div className="grid grid-cols-2 gap-x-6">
                        <ControlledInput<CustomerFields>
                            name="name" control={control}
                            rules={{ shouldUnregister: true, required: { message: t("Customers_.nameRequired"), value: true } }} />
                        <ControlledInput<CustomerFields> name="phone" control={control}
                            rules={{ shouldUnregister: true }} />
                    </div>
                    <ControlledTextArea<CustomerFields> name="address" control={control}
                        placeholder={t("address")} rules={{ shouldUnregister: true }} />
                    <ControlledTextArea<CustomerFields> name="notes" control={control}
                        placeholder={t("notes")} rules={{ shouldUnregister: true }} />
                    {!hasPermission(user, "customerApproval", "update") &&
                        <Text className="mt-2">{t("Customers_.pendingHint")}</Text>}
                </Form>
            </Model>

            <Model title={t("Customers_.rejectTitle")} isOpen={isOpenRejectModel}
                onClick={() => setIsOpenRejectModel(false)} ref={rejectRef}>
                <Form ServerError={rejectForm.formState.errors.root?.server}
                    onSubmit={rejectForm.handleSubmit((values) => {
                        if (!rejectTarget) return
                        rejectMutation.mutate({ id: rejectTarget.id, notes: values.notes })
                    })}
                    Buttons={<Button type="submit">{t("reject")}</Button>}>
                    <ControlledTextArea<RejectFields> name="notes" control={rejectForm.control}
                        placeholder={t("Customers_.rejectReason")}
                        rules={{ shouldUnregister: true, required: { message: t("Customers_.rejectReasonRequired"), value: true } }} />
                </Form>
            </Model>

            <Model title={t("Customers_.deleteTitle")} isOpen={isOpenDeleteModel}
                onClick={() => setIsOpenDeleteModel(false)} ref={deleteRef}>
                <div className="p-4">
                    <Text>{t("Customers_.deleteConfirm")}</Text>
                    <div className="flex justify-end gap-x-2 mt-4">
                        <Button variants="ghost" onClick={() => { setIsOpenDeleteModel(false); setDeleteTarget(null) }}>
                            {t("Suppliers.cancel")}
                        </Button>
                        <Button onClick={() => {
                            if (!deleteTarget) return
                            remove.mutate(deleteTarget.id, {
                                onSuccess() {
                                    setIsOpenDeleteModel(false); setDeleteTarget(null)
                                    setSuccessMessage(t("Customers_.deleteSuccess")); setIsOpenToast(true); invalidate()
                                },
                                onError() { setIsOpenDeleteModel(false) },
                            })
                        }}>{t("Suppliers.confirm")}</Button>
                    </div>
                </div>
            </Model>

            <Toast onClick={() => { setIsOpenToast(false); setSuccessMessage(null) }} isOpen={isOpenToast} ref={toastRef}>
                {successMessage && <div className="flex items-center gap-x-2">
                    <HugeiconsIcon className="*:fill-ok *:stroke-white" size={24} icon={CheckmarkCircle01Icon} />
                    <Text>{successMessage}</Text>
                </div>}
            </Toast>

            <div>
                <div className="flex items-center gap-x-3 mb-8">
                    {hasPermission(user, "customers", "create") &&
                        <Button onClick={() => setIsOpenAddModel(true)} variants="border" size="sm" iconOnly
                            leftIcon={<HugeiconsIcon size={16} icon={Plus} />} />}
                    <TableSettings<Customer> columns={columns}
                        columnVisibility={columnVisibility} setColumnVisibility={setColumnVisibility}
                        grouping={grouping} setGrouping={setGrouping} />
                    <TableFilter<Customer> columns={columns}
                        columnFilters={columnFilters} setColumnFilters={setColumnFilters} />
                    <DebouncedInput fieldset={false} rounded="full" className="w-44"
                        placeholder={t("search") + "..."} value={globalFilter} onChange={setGlobalFilter} />
                </div>
                {errors.root?.server && <Text className="mb-3 text-error">{errors.root.server.message}</Text>}
                {data ? <Table<Customer>
                    columns={columns} data={data} tableKey="customers"
                    columnFilters={columnFilters} setColumnFilters={setColumnFilters}
                    columnVisibility={columnVisibility} setColumnVisibility={setColumnVisibility}
                    sorting={sorting} setSorting={setSorting}
                    grouping={grouping} setGrouping={setGrouping}
                    globalFilter={globalFilter} setGlobalFilter={setGlobalFilter}
                /> : <Text>{t("Orders_.emptyInbox")}</Text>}
            </div>
        </div>
    )
}
