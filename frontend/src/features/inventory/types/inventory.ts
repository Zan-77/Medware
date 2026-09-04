// These types mirror the DRF serializers in backend/Medware_Backend/inventory.
// The API names foreign keys after the model field (`bill`, `item`, `category`),
// not with an `Id` suffix - the previous `billId`/`itemId`/`categoryId` names
// matched nothing in the payload, so those table columns rendered blank.
// `*_name` fields are read-only labels the serializers add so a table does not
// have to resolve one id per row.

export interface InventoryItems {
    id: string
    product: string | number | null
    category: string | number
    name: string
    sku: string | null
    whole_price: number | null
    retail_price: number | null
    image_url: string
    quantity: number
}

export interface InventoryCategories {
    id: string
    name: string
    description: string
}


export interface SupplierBillls {
    id: string
    supplier: string | number | null
    supplier_name?: string | null
    manager: string | number | null
    date: string
    notes: string
}



export interface SupplierBilllLines {
    id: string
    bill: string | number
    item: string | number | null
    item_name?: string | null
    category: string | number | null
    category_name?: string | null
    quantity: number
    expiry_date: string | null
    unit_price: number | null
    discount: number | null
}


export interface InventoryStockEntry {
    id: string
    item: string | number
    quantity: number
    expiry_date: string | null
    source_bill_line: string | number | null
    created_at: string
    movement_type: string
}
