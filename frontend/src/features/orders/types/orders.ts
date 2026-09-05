// These mirror the DRF serializers in backend/Medware_Backend/orders. The API
// names foreign keys after the model field (`customer`, `product`), never with
// an `Id` suffix, and read-only labels arrive as `*_name`.

import type { Customer } from "../../customers/types/customers"

export type OrderStatus = "PENDING" | "APPROVED" | "REJECTED" | "FINALIZED"

export interface OrderItem {
    id: string
    order_request?: string | number
    product: string | number
    product_name?: string | null
    quantity: number
    sell_price: number
    note: string
    return_quantity: number
}

export interface OrderRequest {
    id: string
    origin: string
    customer: string | number
    customer_name?: string | null
    salesman: string | number | null
    salesman_name?: string | null
    created_at: string
    status: OrderStatus
    notes: string
    previous_balance: number | null
    new_balance: number | null
    total: number
    items: OrderItem[]
}

export interface OrderInboxItem {
    kind: string
    // Exactly one of these is populated: order rows carry `order`, customer
    // approval rows carry `customer`. The backend sends both keys with the
    // unused one null.
    order: OrderRequest | null
    customer: Customer | null
    message: string
    notification_id: number | null
}

export interface OrderInbox {
    role: string
    count: number
    items: OrderInboxItem[]
}

export interface AppNotification {
    id: number
    kind: string
    target_type: string
    target_id: string
    message: string
    created_at: string
    read_at: string | null
}
