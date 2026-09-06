import { CheckmarkCircle01Icon, Plus, ViewIcon } from "@hugeicons/core-free-icons"
import { HugeiconsIcon } from "@hugeicons/react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { filterFn_includesString, filterFn_inNumberRange, type ColumnDef, type ColumnFiltersState, type ColumnVisibilityState, type GroupingState, type SortingState, type TableFeatures } from "@tanstack/react-table"
import { useEffect, useMemo, useState } from "react"
import { useForm } from "react-hook-form"
import { useTranslation } from "react-i18next"
import { useNavigate } from "react-router"
import Button from "../../../components/Button"
import ControlledInput from "../../../components/ControlledInput"
import ControlledTextArea from "../../../components/ControlledTextArea"
import { ControlledDateInput } from "../../../components/DateInput"
import DebouncedInput from "../../../components/DebouncedInput"
import Form from "../../../components/Form"
import Model from "../../../components/Model"
import { ControlledSearchSelectInput } from "../../../components/SearchSelectInput"
import { Table } from "../../../components/Table"
import TableFilter from "../../../components/TableFilter"
import TableSettings from "../../../components/TableSettings"
import Text from "../../../components/Text"
import Toast from "../../../components/Toast"
import useOpenMenu from "../../../hooks/useOpenMenu"
import { useBoundStore } from "../../../store/useBoundStore"
import { hasPermission } from "../../auth"
import { getCustomerAccounts, postVoucher } from "../services/finance.service"
import type { CustomerAccount } from "../types/finance"

type VoucherFields = {
    number: string
    date: string
    customer: string
    amount: string
    reference: string
}

const today = () => {
    const now = new Date()
    const month = `${now.getMonth() + 1}`.padStart(2, "0")
    const day = `${now.getDate()}`.padStart(2, "0")
    return `${now.getFullYear()}-${month}-${day}`
}

const emptyVoucher = (): VoucherFields => ({
    number: "", date: today(), customer: "", amount: "", reference: "",
})

export const FinancePage = () => {
    const user = useBoundStore(state => state.authSlice.user)
    const navigate = useNavigate()
    const { t } = useTranslation()
    const queryClient = useQueryClient()

    const { isOpen: isOpenVoucher, setIsOpen: setIsOpenVoucher, ref: voucherRef } = useOpenMenu()
    const { isOpen: isOpenToast, setIsOpen: setIsOpenToast, ref: toastRef } = useOpenMenu()

    const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([])
    const [sorting, setSorting] = useState<SortingState>([])
    const [grouping, setGrouping] = useState<GroupingState>([])
    const [globalFilter, setGlobalFilter] = useState("")
    const [columnVisibility, setColumnVisibility] = useState<ColumnVisibilityState>({
        customer: true, customer_name: true, outstanding: true,
    })
    const [successMessage, setSuccessMessage] = useState<string | null>(null)

    const { data = [] } = useQuery({ queryKey: ["customerAccounts"], queryFn: getCustomerAccounts })

    const { control, handleSubmit, reset, watch, setError, clearErrors, formState: { errors } } =
        useForm<VoucherFields>({ defaultValues: emptyVoucher(), mode: "all" })

    // The salesman is shown, never typed: the server takes it from the
    // customer's own order, so an input here could only ever disagree with it.
    const selectedCustomer = watch("customer")
    const selectedAccount = useMemo(
        () => data.find((account) => String(account.customer) === String(selectedCustomer)),
        [data, selectedCustomer])

    const customerOptions = useMemo(
        () => data.map((account) => ({
            value: String(account.customer), label: account.customer_name,
        })),
        [data])

    const create = useMutation({
        mutationFn: postVoucher,
        onSuccess() {
            setIsOpenVoucher(false)
            setSuccessMessage(t("Finance.voucherCreated"))
            setIsOpenToast(true)
            // Balances are derived from vouchers, so every row's figures moved.
            queryClient.invalidateQueries({ queryKey: ["customerAccounts"] })
            queryClient.invalidateQueries({ queryKey: ["customerStatement"] })
        },
        onError() {
            setError("root.server", { type: "server", message: t("Finance.serverError") })
        },
    })

    useEffect(() => {
        if (!isOpenVoucher) { reset(emptyVoucher()); clearErrors() }
    }, [isOpenVoucher, clearErrors, reset])

    useEffect(() => {
        if (!isOpenToast) return
        const id = window.setTimeout(() => { setIsOpenToast(false); setSuccessMessage(null) }, 3000)
        return () => window.clearTimeout(id)
    }, [isOpenToast, setIsOpenToast])

    const onSubmit = (values: VoucherFields) => {
        clearErrors("root.server")
        create.mutate({
            number: values.number,
            date: values.date,
            customer: values.customer,
            amount: Number(values.amount),
            reference: values.reference,
        })
    }

    const columns: Array<ColumnDef<TableFeatures, CustomerAccount>> = [
        {
            id: "actions",
            enableColumnFilter: false, enableSorting: false, enableGrouping: false,
            header: t("actions"),
            cell: ({ row }) => (
                <div className="flex justify-center">
                    <Button
                        size="xs" variants="ghost"
                        onClick={() => navigate(`/app/finance/${row.original.customer}/`, {
                            state: { location: "customerStatement", details: row.original.customer_name },
                        })}
                        leftIcon={<HugeiconsIcon size={18} icon={ViewIcon} />}>
                        {t("details")}
                    </Button>
                </div>
            ),
        },
        {
            meta: { filterVariants: "value" }, id: "customer_name", enableSorting: true,
            header: t("customer"), accessorKey: "customer_name", filterFn: filterFn_includesString,
        },
        {
            meta: { filterVariants: "value" }, id: "salesman", enableSorting: true,
            header: t("salesman"),
            accessorFn: (row) => row.salesman_name ?? "",
            cell: ({ row }) => row.original.salesman_name ?? t("none"),
            filterFn: filterFn_includesString,
        },
        {
            meta: { filterVariants: "value" }, id: "phone", enableSorting: true,
            header: t("phone_"), accessorKey: "phone", filterFn: filterFn_includesString,
        },
        {
            meta: { filterVariants: "range" }, id: "total_ordered", enableSorting: true,
            header: t("Finance.totalOrdered"), accessorKey: "total_ordered",
            filterFn: filterFn_inNumberRange,
        },
        {
            meta: { filterVariants: "range" }, id: "total_paid", enableSorting: true,
            header: t("Finance.totalPaid"), accessorKey: "total_paid",
            filterFn: filterFn_inNumberRange,
        },
        {
            meta: { filterVariants: "range" }, id: "outstanding", enableSorting: true,
            header: t("Finance.outstanding"), accessorKey: "outstanding",
            filterFn: filterFn_inNumberRange,
        },
        {
            meta: { filterVariants: "range" }, id: "customer", enableGrouping: false,
            enableSorting: true, header: t("id"), accessorKey: "customer",
            filterFn: filterFn_inNumberRange,
        },
    ]

    return (
        <div>
            <Model title={t("Finance.newVoucher")} isOpen={isOpenVoucher}
                onClick={() => setIsOpenVoucher(false)} ref={voucherRef}>
                <Form ServerError={errors.root?.server} onSubmit={handleSubmit(onSubmit)}
                    Buttons={<Button type="submit">{t("Finance.addVoucher")}</Button>}>
                    <div className="grid grid-cols-2 gap-x-6">
                        <ControlledInput<VoucherFields>
                            name="number" control={control} legend={t("Finance.voucherNumber")}
                            rules={{ shouldUnregister: true, required: { message: t("Finance.numberRequired"), value: true } }} />
                        <ControlledDateInput<VoucherFields>
                            name="date" control={control}
                            rules={{ shouldUnregister: true, required: { message: t("Finance.dateRequired"), value: true } }} />
                    </div>
                    <ControlledSearchSelectInput<VoucherFields>
                        control={control} name="customer" label={t("customer")}
                        options={customerOptions} placeholder={t("search") + "..."}
                        rules={{ required: { message: t("Finance.customerRequired"), value: true } }} />

                    {/* Read-only on purpose: derived from the customer, not entered. */}
                    <div className="mt-2 mb-1">
                        <Text muted>{t("salesman")}</Text>
                        <Text>
                            {selectedCustomer
                                ? selectedAccount?.salesman_name ?? t("Finance.noSalesmanYet")
                                : t("Finance.pickCustomerFirst")}
                        </Text>
                    </div>

                    <ControlledInput<VoucherFields>
                        name="amount" control={control} type="number" legend={t("Finance.amount")}
                        rules={{
                            shouldUnregister: true,
                            required: { message: t("Finance.amountRequired"), value: true },
                            min: { message: t("Finance.amountMin"), value: 0.01 },
                        }} />
                    <ControlledTextArea<VoucherFields> name="reference" control={control}
                        placeholder={t("Finance.reference")} rules={{ shouldUnregister: true }} />
                </Form>
            </Model>

            <Toast onClick={() => { setIsOpenToast(false); setSuccessMessage(null) }}
                isOpen={isOpenToast} ref={toastRef}>
                {successMessage && <div className="flex items-center gap-x-2">
                    <HugeiconsIcon className="*:fill-ok *:stroke-white" size={24} icon={CheckmarkCircle01Icon} />
                    <Text>{successMessage}</Text>
                </div>}
            </Toast>

            <div className="flex items-center gap-x-3 mb-8">
                {hasPermission(user, "finance", "create") &&
                    <Button onClick={() => setIsOpenVoucher(true)} variants="border" size="sm" iconOnly
                        leftIcon={<HugeiconsIcon size={16} icon={Plus} />} />}
                <TableSettings<CustomerAccount> columns={columns}
                    columnVisibility={columnVisibility} setColumnVisibility={setColumnVisibility}
                    grouping={grouping} setGrouping={setGrouping} />
                <TableFilter<CustomerAccount> columns={columns}
                    columnFilters={columnFilters} setColumnFilters={setColumnFilters} />
                <DebouncedInput fieldset={false} rounded="full" className="w-44"
                    placeholder={t("search") + "..."} value={globalFilter} onChange={setGlobalFilter} />
            </div>

            {data.length > 0 ? <Table<CustomerAccount>
                columns={columns} data={data} tableKey="customerAccounts"
                columnFilters={columnFilters} setColumnFilters={setColumnFilters}
                columnVisibility={columnVisibility} setColumnVisibility={setColumnVisibility}
                sorting={sorting} setSorting={setSorting}
                grouping={grouping} setGrouping={setGrouping}
                globalFilter={globalFilter} setGlobalFilter={setGlobalFilter}
            /> : <Text>{t("Finance.noCustomers")}</Text>}
        </div>
    )
}
