import { HugeiconsIcon } from "@hugeicons/react"
import { CheckmarkCircle01Icon, Edit, FilterHorizontalIcon, FilterMailIcon, Plus, Trash } from "@hugeicons/core-free-icons"
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
import { getSuppliers, postSuppliers } from "../../inventory/services/products.service"
import { putSupplier, deleteSupplier } from "../../inventory/services/products.service"
import { Table } from "../../../components/Table"
import type { ColumnDef, TableFeatures } from "@tanstack/react-table"
import Toast from "../../../components/Toast"
import Text from "../../../components/Text"
import { hasPermission } from "../../auth"
import { useBoundStore } from "../../../store/useBoundStore"

type NewSupplierFieldsValueState = Omit<Suppliers, "id">

const defaultProductValues: NewSupplierFieldsValueState = {
    name: "",
    phone: "",
}

export const SupplierPage = () => {
    const user = useBoundStore(state => state.authSlice.user)
    const { isOpen: isOpenAddModel, setIsOpen: setIsOpenAddModel, ref: AddModelRef } = useOpenMenu()
    const { isOpen: isOpenDeleteModel, setIsOpen: setIsOpenDeleteModel, ref: DeleteModelRef } = useOpenMenu()
    const { isOpen: isOpenToast, setIsOpen: setIsOpenToast, ref: toastRef } = useOpenMenu()
    const { data } = useQuery({
        queryKey: ["supplers"],
        queryFn: getSuppliers
    })
    const queryClient = useQueryClient()

    const { mutate: addSupplier } = useMutation({
        mutationKey: ["supplers", "new"],
        mutationFn: postSuppliers
    })

    const updateSupplier = useMutation({
        mutationKey: ["supplers", "update"],
        mutationFn: ({ id, data }: { id: string, data: Omit<NewSupplierFieldsValueState, "id"> }) => putSupplier(id, data),
    })

    const deleteSupplierMutation = useMutation({
        mutationKey: ["supplers", "delete"],
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
                    queryClient.invalidateQueries(["supplers"])
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
                queryClient.invalidateQueries(["supplers"])
            },
        })
    }
    const columns: Array<ColumnDef<TableFeatures, Suppliers>> = [
        {
            id: "actions",
            enableColumnFilter: false,
            enableCellSelection: false,
            header: t("actions"),
            cell: ({ row }) => (
                <div className="flex justify-center gap-x-2">
                    {hasPermission(user, "suppliers", "create") && <Button onClick={() => { setDeleteTarget(row.original); setIsOpenDeleteModel(true) }} size="xs" variants="ghost" iconOnly={true} leftIcon={<HugeiconsIcon size={18} icon={Trash} />} />}
                    {hasPermission(user, "suppliers", "create") && <Button onClick={() => { setEditingSupplierId(row.original.id); reset({ name: row.original.name, phone: row.original.phone }); setIsOpenAddModel(true) }} size="xs" variants="ghost" iconOnly={true} leftIcon={<HugeiconsIcon size={18} icon={Edit} />} />}
                </div>
            )

        },

        {
            header: t("phone"),
            accessorKey: "phone",
        },
        {
            header: t("name"),
            accessorKey: "name",
        },
        {
            header: t("id"),
            accessorKey: "id",
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
                                    queryClient.setQueryData(["supplers"], (old: Suppliers[] | undefined) => {
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
                <div className="flex gap-x-3 mb-8">
                    {hasPermission(user, "suppliers", "create") && <Button onClick={() => { setIsOpenAddModel(true) }} variants="border" size="sm" iconOnly leftIcon={<HugeiconsIcon size={16} icon={Plus} />} />}
                    <Button variants="border" size="sm" iconOnly leftIcon={<HugeiconsIcon size={16} icon={FilterHorizontalIcon} />} />
                    <Button variants="border" size="sm" iconOnly leftIcon={<HugeiconsIcon size={16} icon={FilterMailIcon} />} />
                </div>
                <Table<Suppliers> columns={columns} data={data as any ?? []} tableKey="products" />
            </div>
        </div>
    )
}
