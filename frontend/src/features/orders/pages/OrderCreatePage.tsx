import { useEffect, useRef } from "react"
import { HugeiconsIcon } from "@hugeicons/react"
import { Plus, Trash } from "@hugeicons/core-free-icons"
import { useMutation, useQuery } from "@tanstack/react-query"
import { useFieldArray, useForm, useWatch, type Control, type UseFormSetValue } from "react-hook-form"
import { useTranslation } from "react-i18next"
import { useNavigate } from "react-router"
import Button from "../../../components/Button"
import ControlledInput from "../../../components/ControlledInput"
import ControlledTextArea from "../../../components/ControlledTextArea"
import Form from "../../../components/Form"
import { ControlledSearchSelectInput } from "../../../components/SearchSelectInput"
import Text from "../../../components/Text"
import { getCustomers } from "../../customers/services/customers.service"
import { getInventoryCategories, getInventoryItems } from "../../inventory/services/inventory.service"
import type { InventoryCategories, InventoryItems } from "../../inventory/types/inventory"
import { postOrder } from "../services/orders.service"

type OrderFormFields = {
    customer: string
    notes: string
    categories: Array<{
        category: string
        items: Array<{ inventoryItem: string; quantity: string; sell_price: string; note: string }>
    }>
}

const emptyItem = { inventoryItem: "", quantity: "1", sell_price: "0", note: "" }
const emptyCategory = { category: "", items: [{ ...emptyItem }] }

type CategoryItemsProps = {
    control: Control<OrderFormFields>
    setValue: UseFormSetValue<OrderFormFields>
    categoryIndex: number
    inventoryItems: InventoryItems[]
}

const CategoryItems = ({ control, setValue, categoryIndex, inventoryItems }: CategoryItemsProps) => {
    const { t } = useTranslation()
    const itemFieldName = `categories.${categoryIndex}.items` as `categories.${number}.items`
    const { fields, append, remove } = useFieldArray<OrderFormFields, `categories.${number}.items`>({ control, name: itemFieldName })
    const category = useWatch({ control, name: `categories.${categoryIndex}.category` as const })
    const previousCategory = useRef<string | undefined>(undefined)
    const itemOptions = inventoryItems
        .filter((item) => category && String(item.category) === String(category))
        .sort((left, right) => left.name.localeCompare(right.name))
        .map((item) => ({ value: String(item.id), label: item.name }))

    useEffect(() => {
        if (previousCategory.current !== undefined && previousCategory.current !== category) {
            fields.forEach((_, itemIndex) => setValue(`categories.${categoryIndex}.items.${itemIndex}.inventoryItem`, ""))
        }
        previousCategory.current = category
    }, [category, categoryIndex, fields, setValue])

    return <div className="space-y-3">
        {fields.map((field, itemIndex) => <div key={field.id} className="grid grid-cols-4 gap-x-3 items-start">
            <ControlledSearchSelectInput<OrderFormFields>
                control={control}
                name={`categories.${categoryIndex}.items.${itemIndex}.inventoryItem`}
                label={t("item")}
                options={itemOptions}
                placeholder={t("search") + "..."}
                rules={{ required: { message: t("Orders_.itemsRequired"), value: true } }}
            />
            <ControlledInput<OrderFormFields> name={`categories.${categoryIndex}.items.${itemIndex}.quantity`} type="number" control={control} rules={{ min: { message: t("Orders_.quantityMin"), value: 1 } }} />
            <ControlledInput<OrderFormFields> name={`categories.${categoryIndex}.items.${itemIndex}.sell_price`} type="number" control={control} rules={{ min: { message: t("Orders_.priceMin"), value: 0 } }} />
            <div className="flex items-start gap-2">
                <ControlledInput<OrderFormFields> name={`categories.${categoryIndex}.items.${itemIndex}.note`} control={control} />
                {fields.length > 1 && <Button type="button" size="xs" variants="ghost" iconOnly onClick={() => remove(itemIndex)} leftIcon={<HugeiconsIcon size={18} icon={Trash} />} />}
            </div>
        </div>)}
        <Button type="button" variants="border" size="sm" onClick={() => (append as unknown as (item: typeof emptyItem) => void)({ ...emptyItem })} leftIcon={<HugeiconsIcon size={16} icon={Plus} />}>{t("addItem")}</Button>
    </div>
}

export const OrderCreatePage = () => {
    const { t } = useTranslation()
    const navigate = useNavigate()
    const { data: customers = [] } = useQuery({ queryKey: ["customers", "APPROVED"], queryFn: () => getCustomers("APPROVED") })
    const customerOptions = customers.map((customer) => ({ value: String(customer.id), label: customer.name }))
    const { data: categories = [] } = useQuery<InventoryCategories[]>({ queryKey: ["inventoryCategories"], queryFn: getInventoryCategories })
    const { data: inventoryItems = [] } = useQuery<InventoryItems[]>({ queryKey: ["inventoryItems"], queryFn: () => getInventoryItems() })
    const categoryOptions = categories.map((category) => ({ value: String(category.id), label: category.name }))
    const { control, handleSubmit, watch, setValue, setError, formState: { errors } } = useForm<OrderFormFields>({ defaultValues: { customer: "", notes: "", categories: [{ ...emptyCategory }] }, mode: "all" })
    const { fields, append, remove } = useFieldArray({ control, name: "categories" })
    const watchedCategories = watch("categories")
    const prefilledItems = useRef<Record<string, string>>({})

    useEffect(() => {
        fields.forEach((field, categoryIndex) => {
            watchedCategories[categoryIndex]?.items.forEach((item, itemIndex) => {
                if (!item.inventoryItem || prefilledItems.current[`${field.id}-${itemIndex}`] === item.inventoryItem) return
                const inventoryItem = inventoryItems.find((entry) => String(entry.id) === item.inventoryItem)
                if (!inventoryItem) return
                prefilledItems.current[`${field.id}-${itemIndex}`] = item.inventoryItem
                setValue(`categories.${categoryIndex}.items.${itemIndex}.sell_price`, String(inventoryItem.whole_price ?? 0))
            })
        })
    }, [fields, inventoryItems, setValue, watchedCategories])

    const create = useMutation({
        mutationFn: postOrder,
        onSuccess: (order) => navigate(`/app/orders/${order.id}/`, { state: { location: "orders" } }),
        onError: () => setError("root.server", { type: "server", message: t("Orders_.serverError") }),
    })

    const onSubmit = (values: OrderFormFields) => {
        const items = values.categories.flatMap((category) => category.items.filter((item) => item.inventoryItem).map((item) => ({ category, item })))
        if (items.length === 0) {
            setError("root.server", { type: "server", message: t("Orders_.itemsRequired") })
            return
        }
        create.mutate({
            customer: Number(values.customer),
            notes: values.notes,
            items: items.map(({ item }) => {
                const inventoryItem = inventoryItems.find((entry) => String(entry.id) === item.inventoryItem)
                return { product: Number(inventoryItem?.product), quantity: Number(item.quantity), sell_price: Number(item.sell_price), note: item.note }
            }),
        })
    }

    return <Form ServerError={errors.root?.server} onSubmit={handleSubmit(onSubmit)} Buttons={<Button type="submit">{t("newOrder")}</Button>}>
        <div className="grid grid-cols-2 gap-x-6">
            <ControlledSearchSelectInput<OrderFormFields> control={control} name="customer" label={t("customer")} rules={{ required: { message: t("Orders_.customerRequired"), value: true } }} options={customerOptions} placeholder={t("search") + "..."} />
        </div>
        <div className="mt-6 space-y-4">
            {fields.map((field, index) => <div key={field.id} className="space-y-3 border-b pb-4">
                <div className="flex items-start gap-2">
                    <ControlledSearchSelectInput<OrderFormFields> control={control} name={`categories.${index}.category`} label={t("category")} rules={{ required: { message: t("InventoryBillLinesMessages.categoryRequired"), value: true } }} options={categoryOptions} placeholder={t("search") + "..."} />
                    {fields.length > 1 && <Button type="button" size="xs" variants="ghost" iconOnly onClick={() => remove(index)} leftIcon={<HugeiconsIcon size={18} icon={Trash} />} />}
                </div>
                <CategoryItems control={control} setValue={setValue} categoryIndex={index} inventoryItems={inventoryItems} />
            </div>)}
            <Button type="button" variants="border" size="sm" onClick={() => append({ ...emptyCategory, items: [{ ...emptyItem }] })} leftIcon={<HugeiconsIcon size={16} icon={Plus} />}>{t("addCategory")}</Button>
        </div>
        <ControlledTextArea<OrderFormFields> placeholder={t("notes")} name="notes" control={control} />
        <Text className="mt-4">{t("orderTotal")}: {watchedCategories.reduce((sum, category) => sum + category.items.reduce((categorySum, item) => categorySum + (Number(item.quantity) || 0) * (Number(item.sell_price) || 0), 0), 0)}</Text>
    </Form>
}
