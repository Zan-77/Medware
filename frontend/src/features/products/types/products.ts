
export type Products = {
    id:string
    whole_price:number | null
    retail_price:number | null
    name:string
    image_url:string
}


export type Suppliers ={
    id:string
    name:string
    phone:string
}


// Mirrors ProductSupplierSerializer: the API names the foreign keys `product`
// and `supplier` and adds read-only `*_name` labels.
export type ProductSuppliers ={
    id:string
    product:string | number
    product_name?:string | null
    supplier:string | number | null
    supplier_name?:string | null
    discount:number | null
}