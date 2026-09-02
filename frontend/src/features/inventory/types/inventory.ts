export interface InventoryItems {
    productId:string
    categoryId:string
    name:string
    sku:string
    whole_price:number
    retail_price:number
    image_url:string
}

export interface InventoryCategories {
    id: string
    name:string
    description:string
}


export interface SupplierBillls {
    id: string
    supplierId:string
    managerId:string
    date:string | number
    notes:string
}



export interface SupplierBilllLines {
    id: string
    billId:string
    itemId:string
    categoryId:string
    quantity:number
    expiry_date:string | number
    unit_price:number
    discount:number
}


export interface InventoryStockEntry {
    itemId:string
    categoryId:string
    billLineId:string
    quantity:number
    expiry_date:string | number
    created_at:string | number
    movement_type:string
}