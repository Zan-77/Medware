// Mirrors users.serializers.UserAdminSerializer. Only `role` and
// `is_verified` are writable server-side; everything else is read-only.
export interface Account {
    id: string
    username: string
    email: string
    first_name: string
    last_name: string
    role: string
    role_display: string
    is_verified: boolean
    is_staff: boolean
    is_superuser: boolean
    date_joined: string
}
