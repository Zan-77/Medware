// These mirror the DRF serializers in backend/Medware_Backend/orders. The API
// names foreign keys after the model field (`customer`, `product`), never with
// an `Id` suffix, and read-only labels arrive as `*_name`.

export type OrderStatus = "PENDING" | "APPROVED" | "REJECTED" | "FINALIZED"

export interface OrderItem {
    id: string
    order_request?: string | number
    product: string | number
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
    order: OrderRequest
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

export interface Customer {
    id: string
    name: string
    phone: string
    address: string
    notes: string
    user: string | number | null
    created_at: string
}
