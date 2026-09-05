import { useEffect, useRef } from "react"
import { HugeiconsIcon } from "@hugeicons/react"
import { Plus, Trash } from "@hugeicons/core-free-icons"
import { useMutation, useQuery } from "@tanstack/react-query"
import { useFieldArray, useForm } from "react-hook-form"
import { useTranslation } from "react-i18next"
import { useNavigate } from "react-router"
import Button from "../../../components/Button"
import ControlledInput from "../../../components/ControlledInput"
import ControlledTextArea from "../../../components/ControlledTextArea"
import Form from "../../../components/Form"
import { ControlledSearchSelectInput } from "../../../components/SearchSelectInput"
import Text from "../../../components/Text"
import { getProducts } from "../../products/services/products.service"
import { getCustomers } from "../../customers/services/customers.service"
import { postOrder } from "../services/orders.service"

type OrderFormFields = {
    customer: string
    notes: string
    items: Array<{ product: string; quantity: string; sell_price: string; note: string }>
}

const emptyItem = { product: "", quantity: "1", sell_price: "0", note: "" }

export const OrderCreatePage = () => {
    const { t } = useTranslation()
    const navigate = useNavigate()

    const { data: customers = [] } = useQuery({
        queryKey: ["customers", "APPROVED"],
        // Only approved customers can have orders raised for them - the
        // backend refuses the rest with a 400, so offering them in the picker
        // would just be a trap.
        queryFn: () => getCustomers("APPROVED"),
    })
    // getProducts is typed as returning a single Products by mistake in the
    // products service; the endpoint returns a list, so normalise here.
    const { data: products } = useQuery({ queryKey: ["productsList"], queryFn: getProducts })
    const productList = Array.isArray(products) ? products : []

    const customerOptions = customers.map((c) => ({ value: String(c.id), label: c.name }))
    const productOptions = productList.map((p) => ({ value: String(p.id), label: p.name }))

    const { control, handleSubmit, watch, setValue, setError, formState: { errors } } =
        useForm<OrderFormFields>({
            defaultValues: { customer: "", notes: "", items: [emptyItem] },
            mode: "all",
        })

    const { fields, append, remove } = useFieldArray({ control, name: "items" })
    const watchedItems = watch("items")

    // Tracks which product each row was last prefilled for, keyed by the
    // useFieldArray field id (stable across reordering, unlike the index).
    const prefilledProductByRow = useRef<Record<string, string>>({})

    // Choosing a product fills that row's price from the catalogue once. It
    // deliberately does NOT re-derive from the current price text: "0" and ""
    // are values a user can legitimately type, and re-writing on every render
    // both clobbered mid-edit input and span forever for a product priced 0.
    useEffect(() => {
        fields.forEach((field, index) => {
            const chosen = watchedItems[index]?.product
            if (!chosen) return
            if (prefilledProductByRow.current[field.id] === chosen) return

            const product = productList.find((p) => String(p.id) === String(chosen))
            // Products may still be loading - do not record the row as done.
            if (!product) return

            prefilledProductByRow.current[field.id] = chosen
            setValue(`items.${index}.sell_price`, String(product.retail_price ?? 0))
        })
    }, [fields, watchedItems, productList, setValue])

    // Live feedback only. The server recomputes and its response is the truth.
    const previewTotal = watchedItems.reduce(
        (sum, item) => sum + (Number(item.quantity) || 0) * (Number(item.sell_price) || 0), 0)

    const create = useMutation({
        mutationFn: postOrder,
        onSuccess(order) {
            navigate(`/app/orders/${order.id}/`, { state: { location: "orders" } })
        },
        onError() {
            setError("root.server", { type: "server", message: t("Orders_.serverError") })
        },
    })

    const onSubmit = (values: OrderFormFields) => {
        const items = values.items.filter((item) => item.product)
        if (items.length === 0) {
            setError("root.server", { type: "server", message: t("Orders_.itemsRequired") })
            return
        }
        create.mutate({
            customer: Number(values.customer),
            notes: values.notes,
            items: items.map((item) => ({
                product: Number(item.product),
                quantity: Number(item.quantity),
                sell_price: Number(item.sell_price),
                note: item.note,
            })),
        })
    }

    return (
        <Form
            ServerError={errors.root?.server}
            onSubmit={handleSubmit(onSubmit)}
            Buttons={<Button type="submit">{t("newOrder")}</Button>}>

            <div className="grid grid-cols-2 gap-x-6">
                <ControlledSearchSelectInput<OrderFormFields>
                    control={control}
                    name="customer"
                    label={t("customer")}
                    rules={{ required: { message: t("Orders_.customerRequired"), value: true } }}
                    options={customerOptions}
                    placeholder={t("search") + "..."}
                />
            </div>

            <div className="mt-6 space-y-3">
                {fields.map((field, index) => (
                    <div key={field.id} className="grid grid-cols-5 gap-x-3 items-start">
                        <ControlledSearchSelectInput<OrderFormFields>
                            control={control}
                            name={`items.${index}.product`}
                            label={t("item")}
                            options={productOptions}
                            placeholder={t("search") + "..."}
                        />
                        <ControlledInput<OrderFormFields>
                            name={`items.${index}.quantity`}
                            type="number"
                            control={control}
                            rules={{ min: { message: t("Orders_.quantityMin"), value: 1 } }}
                        />
                        <ControlledInput<OrderFormFields>
                            name={`items.${index}.sell_price`}
                            type="number"
                            control={control}
                            rules={{ min: { message: t("Orders_.priceMin"), value: 0 } }}
                        />
                        <ControlledInput<OrderFormFields>
                            name={`items.${index}.note`}
                            control={control}
                        />
                        <Button
                            type="button"
                            className="dark:text-error text-error"
                            size="xs" variants="ghost" iconOnly
                            onClick={() => remove(index)}
                            leftIcon={<HugeiconsIcon size={18} icon={Trash} />} />
                    </div>
                ))}
            </div>

            <div className="mt-3">
                <Button type="button" variants="border" size="sm"
                    onClick={() => append({ ...emptyItem })}
                    leftIcon={<HugeiconsIcon size={16} icon={Plus} />}>{t("addItem")}</Button>
            </div>

            <ControlledTextArea<OrderFormFields>
                placeholder={t("notes")}
                name="notes"
                control={control}
            />

            <Text className="mt-4">{t("orderTotal")}: {previewTotal}</Text>
        </Form>
    )
}
