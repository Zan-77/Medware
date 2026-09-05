// Mirrors customers.serializers.CustomerSerializer. `status`, `created_by` and
// `rejection_notes` are read-only server-side and must never be submitted.

export type CustomerStatus = "PENDING" | "APPROVED" | "REJECTED"

export interface Customer {
    id: string
    name: string
    phone: string
    address: string
    notes: string
    user: string | number | null
    created_at: string
    status: CustomerStatus
    created_by: string | number | null
    created_by_name?: string | null
    rejection_notes: string
}
