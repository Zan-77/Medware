import ax from "../../../services/api"
import type { Products, Suppliers } from "../../products/types/products"

const productsUrl = "/products/products/"

export const getProducts = async ():Promise<Products>=> {
    const res = await ax.get<Products>(productsUrl)
    return res.data
}

export const postProducts = async (data: Omit<Products, "id">) => {
    const res = await ax.post(productsUrl, data)
    return res
}

export const putProduct = async (id: string, data: Omit<Products, "id">) => {
    const res = await ax.put(`${productsUrl}${id}/`, data)
    return res
}

export const deleteProduct = async (id: string) => {
    const res = await ax.delete(`${productsUrl}${id}/`)
    return res
}


const suppliersUrl = "/products/suppliers/"


export const getSuppliers = async ():Promise<Products>=> {
    const res = await ax.get<Products>(suppliersUrl)
    return res.data
}

export const postSuppliers = async (data: Omit<Suppliers, "id">) => {
    const res = await ax.post(suppliersUrl, data)
    return res
}

export const putSupplier = async (id: string, data: Omit<Suppliers, "id">) => {
    const res = await ax.put(`${suppliersUrl}${id}/`, data)
    return res
}

export const deleteSupplier = async (id: string) => {
    const res = await ax.delete(`${suppliersUrl}${id}/`)
    return res
}
