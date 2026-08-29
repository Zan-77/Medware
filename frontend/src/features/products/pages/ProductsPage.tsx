import { HugeiconsIcon } from "@hugeicons/react"
import { CheckmarkCircle01Icon, Edit, FilterHorizontalIcon, FilterMailIcon, Plus, Trash } from "@hugeicons/core-free-icons"
import Button from "../../../components/Button"
import useOpenMenu from "../../../hooks/useOpenMenu"
import Form from "../../../components/Form"
import ControlledInput from "../../../components/ControlledInput"
import { useForm } from "react-hook-form"
import type { Products } from "../types/products"
import { useTranslation } from "react-i18next"
import { useEffect, useState } from "react"
import Model from "../../../components/Model"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { getProducts, postProducts, putProduct, deleteProduct } from "../../inventory/services/products.service"
import { Table } from "../../../components/Table"
import type { ColumnDef, TableFeatures } from "@tanstack/react-table"
import Toast from "../../../components/Toast"
import Text from "../../../components/Text"
import { hasPermission } from "../../auth"
import { useBoundStore } from "../../../store/useBoundStore"

type NewProductFieldsValueState = Omit<Products, "id">

const defaultProductValues: NewProductFieldsValueState = {
    image_url: "",
    name: "",
    retail_price: 0,
    whole_price: 0,
}

export const ProductsPage = () => {
    const user = useBoundStore(state => state.authSlice.user)
    const { isOpen: isOpenAddModel, setIsOpen: setIsOpenAddModel, ref: AddModelRef } = useOpenMenu()
    const { isOpen: isOpenToast, setIsOpen: setIsOpenToast, ref: toastRef } = useOpenMenu()
    const { isOpen: isOpenDeleteModel, setIsOpen: setIsOpenDeleteModel, ref: DeleteModelRef } = useOpenMenu()
    const { data } = useQuery({
        queryKey: ["products"],
        queryFn: getProducts
    })
    const queryClient = useQueryClient()

    const { mutate: addProducts, isSuccess } = useMutation({
        mutationKey: ["products", "new"],
        mutationFn: postProducts
    })

    const updateProduct = useMutation({
        mutationKey: ["products", "update"],
        mutationFn: ({ id, data }: { id: number, data: Omit<NewProductFieldsValueState, "id"> }) => putProduct(id, data),
    })

    const deleteProductMutation = useMutation({
        mutationKey: ["products", "delete"],
        mutationFn: (id: number) => deleteProduct(id),
    })

    const { control, handleSubmit, reset, setError, clearErrors, formState: { errors } } = useForm<NewProductFieldsValueState>({
        defaultValues: defaultProductValues,
        mode: "all"
    })
    const [editingProductId, setEditingProductId] = useState<number | null>(null)
    const [deleteTarget, setDeleteTarget] = useState<null | Products>(null)
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
        }, 3000)

        return () => window.clearTimeout(timeoutId)
    }, [isOpenToast, setIsOpenToast])

    const onSubmit = (data: NewProductFieldsValueState) => {
        clearErrors("root.server")
        if (editingProductId) {
            updateProduct.mutate({ id: editingProductId, data }, {
                onError(error) {
                    console.log(error)
                    setError("root.server", { type: "server", message: t("products.serverError") })
                },
                onSuccess() {
                    reset(defaultProductValues)
                    clearErrors()
                    setEditingProductId(null)
                    setIsOpenAddModel(false)
                    setIsOpenToast(true)
                    //@ts-ignore
                    queryClient.invalidateQueries(["products"])
                }
            })
            return
        }

        addProducts(data, {

            onError(error) {
                console.log(error);
                setError("root.server", { type: "server", message: t("products.serverError") })
            },
            onSuccess() {
                reset(defaultProductValues)
                clearErrors()
                setIsOpenAddModel(false)
                setIsOpenToast(true)
                //@ts-ignore
                queryClient.invalidateQueries(["products"])
            },
        })
    }
    const columns: Array<ColumnDef<TableFeatures, Products>> = [
        {
            id: "actions",
            enableColumnFilter: false,
            enableCellSelection: false,
            header: t("actions"),
            cell: ({ row }) => (
                <div className="flex justify-center gap-x-2">
                    {hasPermission(user, "products", "delete") && <Button onClick={() => { setDeleteTarget(row.original); setIsOpenDeleteModel(true) }} size="xs" variants="ghost" iconOnly={true} leftIcon={<HugeiconsIcon size={18} icon={Trash} />} />}
                    {hasPermission(user, "products", "update") && <Button onClick={() => { setEditingProductId(row.original.id); reset({ name: row.original.name, retail_price: row.original.retail_price, whole_price: row.original.whole_price, image_url: row.original.image_url }); setIsOpenAddModel(true) }} size="xs" variants="ghost" iconOnly={true} leftIcon={<HugeiconsIcon size={18} icon={Edit} />} />}
                </div>
            )

        },
        {
            header: t("retail_price"),
            accessorKey: "retail_price",
            cell: ({ getValue }) => `${Number(getValue() ?? 0).toFixed(2)} ل.س`,
        },
        {
            header: t("whole_price"),
            accessorKey: "whole_price",
            cell: ({ getValue }) => `${Number(getValue() ?? 0).toFixed(2)} ل.س`,
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
            <Model title={t("products.newProduct")} isOpen={isOpenAddModel} onClick={() => setIsOpenAddModel(false)} ref={AddModelRef}>
                <Form ServerError={errors.root?.server} onSubmit={handleSubmit(onSubmit)} Buttons={<Button type="submit">{t("products.addProduct")}</Button>}>
                    <div className="grid grid-cols-2 gap-x-6">
                        <ControlledInput<NewProductFieldsValueState>
                            rules={{
                                shouldUnregister: true,
                                required: { message: t("products.productNameRequired"), value: true },
                            }}
                            name="name"
                            control={control}
                        />
                        <ControlledInput<NewProductFieldsValueState>
                            rules={{
                                shouldUnregister: true,
                                required: { message: t("products.retailPriceRequired"), value: true },
                                min: { message: t("products.retailPriceMin"), value: 0 },
                            }}
                            name="retail_price"
                            control={control}
                        />
                        <ControlledInput<NewProductFieldsValueState>
                            rules={{
                                shouldUnregister: true,
                                required: { message: t("products.wholePriceRequired"), value: true },
                                min: { message: t("products.wholePriceMin"), value: 0 },
                            }}
                            name="whole_price"
                            control={control}
                        />
                    </div>
                </Form>
            </Model>
            <Model title={t("products.deleteTitle") ?? t("Suppliers.deleteTitle")} isOpen={isOpenDeleteModel} onClick={() => setIsOpenDeleteModel(false)} ref={DeleteModelRef}>
                <div className="p-4">
                    <Text>{t("products.deleteConfirm") ?? t("Suppliers.deleteConfirm")}</Text>
                    <div className="flex justify-end gap-x-2 mt-4">
                        <Button variants="ghost" onClick={() => { setIsOpenDeleteModel(false); setDeleteTarget(null) }}>{t("Suppliers.cancel")}</Button>
                        <Button onClick={() => {
                            if (!deleteTarget) return
                            deleteProductMutation.mutate(deleteTarget.id, {
                                onError(error) {
                                    console.log(error)
                                    setIsOpenDeleteModel(false)
                                },
                                onSuccess() {
                                    setIsOpenDeleteModel(false)
                                    setDeleteTarget(null)
                                    setIsOpenToast(true)
                                    //@ts-ignore
                                    queryClient.invalidateQueries(["products"])
                                }
                            })
                        }}>{t("Suppliers.confirm")}</Button>
                    </div>
                </div>
            </Model>
            <Toast onClick={() => { setIsOpenToast(false) }} isOpen={isOpenToast} ref={toastRef}>
                {isSuccess && <div className="flex items-center gap-x-2 "><HugeiconsIcon className="*:fill-ok *:stroke-white" size={24} icon={CheckmarkCircle01Icon} /> <Text>{t("products.successMessage")}</Text></div>}
            </Toast>
            <div>
                <div className="flex gap-x-3 mb-8">
                    {hasPermission(user, "products", "create") && <Button onClick={() => { setIsOpenAddModel(true) }} variants="border" size="sm" iconOnly leftIcon={<HugeiconsIcon size={16} icon={Plus} />} />}
                    <Button variants="border" size="sm" iconOnly leftIcon={<HugeiconsIcon size={16} icon={FilterHorizontalIcon} />} />
                    <Button variants="border" size="sm" iconOnly leftIcon={<HugeiconsIcon size={16} icon={FilterMailIcon} />} />
                </div>
                <Table<Products> columns={columns} data={data as any ?? []} tableKey="products" />
            </div>
        </div>
    )
}
