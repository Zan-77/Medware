// Mirrors finance.serializers. Every figure on a customer account is derived
// server-side from approved orders minus vouchers, so nothing here is writable
// - money moves by raising a voucher or approving an order.

export interface CustomerAccount {
    customer: number
    customer_name: string
    phone: string
    status: string
    /** The salesman who raised this customer's most recent order. Null until
     *  they have one - there is no salesman on a customer with no orders. */
    salesman_name: string | null
    total_ordered: number
    total_paid: number
    outstanding: number
}

/** An order on a statement: what pushed the balance up. */
export interface StatementOrder {
    id: number
    date: string
    status: string
    total: number
    salesman_name: string | null
}

/** A voucher on a statement: what brought the balance down. */
export interface StatementVoucher {
    id: number
    number: string
    date: string
    amount: number
    reference: string
    order: number | null
}

export interface CustomerStatement extends CustomerAccount {
    orders: StatementOrder[]
    vouchers: StatementVoucher[]
}

// `salesman` is filled by the server from the customer's own order and must
// never be submitted - see finance.serializers.VoucherSerializer.
export interface Voucher {
    id: number
    number: string
    date: string
    customer: number
    customer_name: string | null
    order: number | null
    salesman: number | null
    salesman_name: string | null
    amount: number
    reference: string
}

export interface NewVoucher {
    number: string
    date: string
    customer: string | number
    amount: number
    reference: string
}
