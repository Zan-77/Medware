import type { InventoryData } from "../inventory/types/inventory"
import type { Products, Suppliers } from "../products/types/products"
import type { Roles } from "./types/roles"
import type { User } from "./types/users"

export type Actions = "create" | "read" | "update" | "delete"


export type PermissionsCheck<key extends keyof Permissions> = boolean | ((user: Omit<User, "password">, data: Permissions[key]["dataType"]) => boolean)

export type RoleWithPermissions = {
    [R in Roles]: Partial<{ [key in keyof Permissions]: Partial<{ [Action in Permissions[key]["actions"]]: PermissionsCheck<key> }> }>
}


export type Permissions = {
    suppliers: {
        dataType: Suppliers
        actions: Actions
    }
    inventory: {
        dataType: InventoryData
        actions: Actions
    }
    products: {
        dataType: Products
        actions: Actions
    }
    orders: {
        dataType: Suppliers
        actions: Actions
    }
}

const ROLES = {
    GUEST: {
        orders: {
            create: false,
            read: false,
            update: false,
            delete: false
        },
        products: {
            create: false,
            read: false,
            update: false,
            delete: false
        },
        suppliers: {
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
    },
    ACCOUNTANT: {
        orders:{
            
        },
        suppliers: {
            read: true,
            create:false,
            delete:false,
            update:false
        },
        products: {
            read: true,
            create: false,
            delete: false,
            update: false
        },
        inventory: {
            read: true
        }
    },
    CUSTOMER: {
        orders:{
            
        },
        suppliers: {
            read: false,
            create:false,
            delete:false,
            update:false
        },
        products: {
            read: true,
            create: false,
            delete: false,
            update: false
        },
        inventory: {
            read: true
        }
    },
    MANAGER: {
        orders:{
            
        },
        suppliers: {
            read: true,
            create:true,
            delete:true,
            update:true
        },
        products: {
            read: true,
            create: true,
            delete: true,
            update: true
        },
        inventory: {
            read: true
        }
    },
    SALESMAN: {
        orders:{
            
        },
        suppliers: {
            read: true,
            create:false,
            delete:false,
            update:false
        },
        products: {
            read: true,
            create: false,
            delete: false,
            update: false
        },
        inventory: {
            read: true
        }
    },
    WAREHOUSE_WORKER: {
        orders:{
            
        },
        suppliers: {
            read: true,
            create:false,
            delete:false,
            update:false
        },
        products: {
            read: true,
            create: false,
            delete: false,
            update: false
        },
    }
} as const satisfies Partial<RoleWithPermissions>



export function hasPermission<Resource extends keyof Permissions>(
    user: Omit<User, "password">,
    resource: Resource,
    action: Permissions[Resource]["actions"],
    data?: Permissions[Resource]["dataType"]
) {
    const permission = (ROLES as RoleWithPermissions)[user.role][resource]?.[action]
    if (permission == null) return false
    if (typeof permission === "boolean") return permission
    return data != null && permission(user, data)
}