import { HugeiconsIcon } from "@hugeicons/react"
import { CheckmarkCircle01Icon, Edit, Plus, Trash } from "@hugeicons/core-free-icons"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useEffect, useState } from "react"
import { useForm } from "react-hook-form"
import { useTranslation } from "react-i18next"
import Button from "../../../components/Button"
import ControlledInput from "../../../components/ControlledInput"
import { ControlledSearchSelectInput } from "../../../components/SearchSelectInput"
import Form from "../../../components/Form"
import Model from "../../../components/Model"
import { Table } from "../../../components/Table"
import Text from "../../../components/Text"
import Toast from "../../../components/Toast"
import useOpenMenu from "../../../hooks/useOpenMenu"
import { hasPermission } from "../../auth"
import { useBoundStore } from "../../../store/useBoundStore"
import { filterFn_includesString, type ColumnDef, type TableFeatures } from "@tanstack/react-table"
import {
    deleteInventoryItem,
    getInventoryCategories,
    getInventoryItems,
    postInventoryItem,
    putInventoryItem,
} from "../services/inventory.service"
import type { InventoryCategories, InventoryItemInput, InventoryItems } from "../types/inventory"

type InventoryItemForm = {
    category: string
    name: string
    sku: string
    whole_price: string
    retail_price: string
    image_url: string
}

const defaultValues: InventoryItemForm = {
    category: "",
    name: "",
    sku: "",
    whole_price: "",
    retail_price: "",
    image_url: "",
}

const toPayload = (values: InventoryItemForm): InventoryItemInput => ({
    category: Number(values.category),
    name: values.name,
    sku: values.sku || null,
    whole_price: values.whole_price === "" ? null : Number(values.whole_price),
    retail_price: values.retail_price === "" ? null : Number(values.retail_price),
    image_url: values.image_url,
})

export const InventoryItemsDetails = () => {
    const { t } = useTranslation()
    const user = useBoundStore((state) => state.authSlice.user)
    const queryClient = useQueryClient()
    const { isOpen: isOpenAddModel, setIsOpen: setIsOpenAddModel, ref: addModelRef } = useOpenMenu()
    const { isOpen: isOpenDeleteModel, setIsOpen: setIsOpenDeleteModel, ref: deleteModelRef } = useOpenMenu()
    const { isOpen: isOpenToast, setIsOpen: setIsOpenToast, ref: toastRef } = useOpenMenu()
    const [editingId, setEditingId] = useState<string | null>(null)
    const [deleteTarget, setDeleteTarget] = useState<InventoryItems | null>(null)
    const [successMessage, setSuccessMessage] = useState<string | null>(null)

    const { data: items = [] } = useQuery<InventoryItems[]>({
        queryKey: ["inventoryItems"],
        queryFn: () => getInventoryItems(),
    })
    const { data: categories = [] } = useQuery<InventoryCategories[]>({
        queryKey: ["inventoryCategories"],
        queryFn: getInventoryCategories,
    })
    const categoryOptions = categories.map((category) => ({ value: String(category.id), label: category.name }))
    const categoryNames = new Map(categories.map((category) => [String(category.id), category.name]))

    const createItem = useMutation({ mutationFn: postInventoryItem })
    const updateItem = useMutation({ mutationFn: ({ id, data }: { id: string; data: InventoryItemInput }) => putInventoryItem(id, data) })
    const deleteItem = useMutation({ mutationFn: deleteInventoryItem })
    const { control, handleSubmit, reset, setError, clearErrors, formState: { errors } } = useForm<InventoryItemForm>({
        defaultValues,
        mode: "all",
    })

    useEffect(() => {
        if (!isOpenAddModel) {
            reset(defaultValues)
            clearErrors()
            setEditingId(null)
        }
    }, [isOpenAddModel, reset, clearErrors])

    useEffect(() => {
        if (!isOpenToast) return
        const timeout = window.setTimeout(() => {
            setIsOpenToast(false)
            setSuccessMessage(null)
        }, 3000)
        return () => window.clearTimeout(timeout)
    }, [isOpenToast, setIsOpenToast])

    const onSubmit = (values: InventoryItemForm) => {
        clearErrors("root.server")
        const data = toPayload(values)
        const request = editingId
            ? updateItem.mutateAsync({ id: editingId, data })
            : createItem.mutateAsync(data)

        request.then(() => {
            reset(defaultValues)
            setEditingId(null)
            setIsOpenAddModel(false)
            setSuccessMessage(editingId ? t("InventoryItems.updateSuccess") : t("InventoryItems.createSuccess"))
            setIsOpenToast(true)
            queryClient.invalidateQueries({ queryKey: ["inventoryItems"] })
        }).catch((error) => {
            console.log(error)
            setError("root.server", { type: "server", message: t("InventoryItems.serverError") })
        })
    }

    const columns: Array<ColumnDef<TableFeatures, InventoryItems>> = [
        {
            id: "actions",
            enableColumnFilter: false,
            enableSorting: false,
            header: t("actions"),
            cell: ({ row }) => (
                <div className="flex justify-center gap-x-2">
                    {hasPermission(user, "inventory", "delete") && <Button size="xs" variants="ghost" iconOnly onClick={() => { setDeleteTarget(row.original); setIsOpenDeleteModel(true) }} leftIcon={<HugeiconsIcon size={18} icon={Trash} />} />}
                    {hasPermission(user, "inventory", "update") && <Button size="xs" variants="ghost" iconOnly onClick={() => { setEditingId(row.original.id); reset({ category: String(row.original.category), name: row.original.name, sku: row.original.sku ?? "", whole_price: row.original.whole_price == null ? "" : String(row.original.whole_price), retail_price: row.original.retail_price == null ? "" : String(row.original.retail_price), image_url: row.original.image_url }); setIsOpenAddModel(true) }} leftIcon={<HugeiconsIcon size={18} icon={Edit} />} />}
                </div>
            ),
        },
        { header: t("category"), accessorFn: (row) => categoryNames.get(String(row.category)) ?? "Uncategorized" },
        { header: t("name"), accessorKey: "name", filterFn: filterFn_includesString },
        { header: t("quantity"), accessorKey: "quantity" },
        { header: t("retail_price"), accessorKey: "retail_price" },
        { header: t("whole_price"), accessorKey: "whole_price" },
        { header: t("expiry_date"), accessorFn: (row) => row.expiry_dates.join(", ") || "-" },
    ]

    return (
        <div>
            <Model title={editingId ? t("InventoryItems.edit") : t("InventoryItems.new")} isOpen={isOpenAddModel} onClick={() => setIsOpenAddModel(false)} ref={addModelRef}>
                <Form ServerError={errors.root?.server} onSubmit={handleSubmit(onSubmit)} Buttons={<Button type="submit">{t("save")}</Button>}>
                    <div className="grid grid-cols-2 gap-4">
                        <ControlledSearchSelectInput<InventoryItemForm> control={control} name="category" label={t("category")} options={categoryOptions} rules={{ required: t("InventoryBillLinesMessages.categoryRequired") }} />
                        <ControlledInput<InventoryItemForm> control={control} name="name" rules={{ required: t("products.productNameRequired") }} />
                        <ControlledInput<InventoryItemForm> control={control} name="sku" />
                        <ControlledInput<InventoryItemForm> control={control} name="whole_price" type="number" />
                        <ControlledInput<InventoryItemForm> control={control} name="retail_price" type="number" />
                        <ControlledInput<InventoryItemForm> control={control} name="image_url" />
                    </div>
                </Form>
            </Model>
            <Model title={t("Suppliers.deleteTitle")} isOpen={isOpenDeleteModel} onClick={() => setIsOpenDeleteModel(false)} ref={deleteModelRef}>
                <div className="p-4">
                    <Text>{t("Suppliers.deleteConfirm")}</Text>
                    <div className="flex justify-end gap-2 mt-4">
                        <Button variants="ghost" onClick={() => setIsOpenDeleteModel(false)}>{t("Suppliers.cancel")}</Button>
                        <Button onClick={() => { if (!deleteTarget) return; deleteItem.mutate(deleteTarget.id, { onSuccess: () => { setDeleteTarget(null); setIsOpenDeleteModel(false); setSuccessMessage(t("InventoryItems.deleteSuccess")); setIsOpenToast(true); queryClient.invalidateQueries({ queryKey: ["inventoryItems"] }) } }) }}>{t("Suppliers.confirm")}</Button>
                    </div>
                </div>
            </Model>
            <Toast isOpen={isOpenToast} ref={toastRef} onClick={() => { setIsOpenToast(false); setSuccessMessage(null) }}>
                {successMessage && <div className="flex items-center gap-2"><HugeiconsIcon size={24} icon={CheckmarkCircle01Icon} /><Text>{successMessage}</Text></div>}
            </Toast>
            <div className="flex gap-3 mb-8">
                {hasPermission(user, "inventory", "create") && <Button onClick={() => setIsOpenAddModel(true)} variants="border" size="sm" iconOnly leftIcon={<HugeiconsIcon size={16} icon={Plus} />} />}
            </div>
            <Table<InventoryItems> columns={columns} data={items} tableKey="inventoryItems" />
        </div>
    )
}

export default InventoryItemsDetails
