import type { Permissions, RoleWithPermissions } from "./types/permissions"
import { type User } from "./types/users"

const ROLES = {
    guest: {
        orders: {
            create: false,
            read: false,
            update: false,
            delete: false
        },
        products: {
            create: false,
            read: true,
            update: false,
            delete: false
        },
        sppliers: {
            create: false,
            read: false,
            update: false,
            delete: false
        },
        inventory: {
            create: false,
            read: false,
            update: false,
            delete: false
        }
    }
} as const satisfies Partial<RoleWithPermissions>



export function hasPermission<Resource extends keyof Permissions>(
    user: Omit<User , "password">,
    resource: Resource,
    action: Permissions[Resource]["actions"],
    data?: Permissions[Resource]["dataType"]
){
    const permission = (ROLES as RoleWithPermissions)[user.role][resource]?.[action]
    if(permission ==null) return false
    if(typeof permission === "boolean") return permission
    return data !=null && permission(user , data)
}