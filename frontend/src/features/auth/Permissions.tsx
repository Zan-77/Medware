import type { InventoryCategories, InventoryItems, InventoryStockEntry, SupplierBilllLines, SupplierBillls } from "../inventory/types/inventory"
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
    supplierBills: {
        dataType: SupplierBillls
        actions: Actions
    }
    supplierBillLines: {
        dataType: SupplierBilllLines
        actions: Actions
    }
    inventory: {
        dataType: InventoryItems
        actions: Actions
    }
    inventoryCategories: {
        dataType: InventoryCategories
        actions: Actions
    }
    inventoryStockEntry: {
        dataType: InventoryStockEntry
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
        inventoryStockEntry: {
            read: true,
            create: false,
            delete: false,
            update: false
        },
        supplierBillLines: {
            read: true,
            create: false,
            delete: false,
            update: false
        },
        supplierBills: {
            read: true,
            create: false,
            delete: false,
            update: false
        },
        inventoryCategories: {
            read: true,
            create: false,
            delete: false,
            update: false
        },
        orders: {

        },
        suppliers: {
            read: true,
            create: false,
            delete: false,
            update: false
        },
        products: {
            read: true,
            create: false,
            delete: false,
            update: false
        },
        inventory: {
            read: true,
            create: false,
            delete: false,
            update: false
        }
    },
    CUSTOMER: {
        inventoryStockEntry: {
            read: false,
            create: false,
            delete: false,
            update: false
        },
        supplierBillLines: {
            read: false,
            create: false,
            delete: false,
            update: false
        },
        supplierBills: {
            read: false,
            create: false,
            delete: false,
            update: false
        },
        inventoryCategories: {
            read: true,
            create: false,
            delete: false,
            update: false
        },
        orders: {

        },
        suppliers: {
            read: false,
            create: false,
            delete: false,
            update: false
        },
        products: {
            read: true,
            create: false,
            delete: false,
            update: false
        },
        inventory: {
            read: false,
            create: false,
            delete: false,
            update: false
        }
    },
    MANAGER: {
        inventoryStockEntry: {
            read: true,
            create: true,
            delete: true,
            update: true
        },
        supplierBillLines: {
            read: true,
            create: true,
            delete: true,
            update: true
        },
        supplierBills: {
            read: true,
            create: true,
            delete: true,
            update: true
        },
        inventoryCategories: {
            read: true,
            create: true,
            delete: true,
            update: true
        },
        orders: {

        },
        suppliers: {
            read: true,
            create: true,
            delete: true,
            update: true
        },
        products: {
            read: true,
            create: true,
            delete: true,
            update: true
        },
        inventory: {
            read: true,
            create: true,
            delete: true,
            update: true
        }
    },
    SALESMAN: {
        inventoryStockEntry: {
            read: false,
            create: false,
            delete: false,
            update: false
        },
        supplierBillLines: {
            read: false,
            create: false,
            delete: false,
            update: false
        },
        supplierBills: {
            read: false,
            create: false,
            delete: false,
            update: false
        },
        inventoryCategories: {
            read: true,
            create: false,
            delete: false,
            update: false
        },
        orders: {

        },
        suppliers: {
            read: true,
            create: false,
            delete: false,
            update: false
        },
        products: {
            read: true,
            create: false,
            delete: false,
            update: false
        },
        inventory: {
            read: true,
            create: false,
            delete: false,
            update: false
        }
    },
    WAREHOUSE_WORKER: {
        inventoryStockEntry: {
            read: true,
            create: false,
            delete: false,
            update: false
        },
        supplierBillLines: {
            read: false,
            create: false,
            delete: false,
            update: false
        },
        supplierBills: {
            read: false,
            create: false,
            delete: false,
            update: false
        },
        inventoryCategories: {
            read: true,
            create: false,
            delete: false,
            update: false
        },
        orders: {

        },
        suppliers: {
            read: true,
            create: false,
            delete: false,
            update: false
        },
        products: {
            read: true,
            create: false,
            delete: false,
            update: false
        },
        inventory: {
            read: true,
            create: false,
            delete: false,
            update: false
        }
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