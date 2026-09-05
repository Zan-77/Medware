import type { Roles } from "./roles"

export interface User  {
    id:string
    username:string
    password:string
    email:string
    first_name:string
    last_name:string
    role:Roles
    // Set from /api/users/me/, which is authoritative. The JWT carries the
    // same flag but it is a 15-minute-old snapshot, so it lags approval.
    is_verified?:boolean
    //is_staff:boolean
    //is_superuser:boolean
}

export type UserWithoutPassword= Omit<User, "password">


