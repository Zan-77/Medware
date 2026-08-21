import type { Roles } from "./roles"
import type { SupplierData } from "../../../types/suppliers"
import type { User } from "./users"

export type Actions = "create" | "read" | "update" | "delete"


export type PermissionsCheck<key extends keyof Permissions> = boolean | ((user: Omit<User , "password">, data: Permissions[key]["dataType"]) => boolean)

export type RoleWithPermissions = {
    [R in Roles]: Partial<{ [key in keyof Permissions]: Partial<{ [Action in Permissions[key]["actions"]]: PermissionsCheck<key> }> }>
}


export type Permissions = {
    sppliers: {
        dataType: SupplierData
        actions: Actions
    }
    inventory: {
        dataType: SupplierData
        actions: Actions
    }
    products: {
        dataType: SupplierData
        actions: Actions
    }
    orders: {
        dataType: SupplierData
        actions: Actions
    }
}