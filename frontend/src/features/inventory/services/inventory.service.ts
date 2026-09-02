
import ax from "../../../services/api"
import type { InventoryCategories } from "../types/inventory"
import type { SupplierBillls } from "../types/inventory"

const inventoryCategoriesUrl = "/inventory/categories/"

export const getInventoryCategories = async (): Promise<InventoryCategories[]> => {
	const res = await ax.get<InventoryCategories[]>(inventoryCategoriesUrl)
	return res.data
}

export const postInventoryCategory = async (data: Omit<InventoryCategories, "id">) => {
	const res = await ax.post(inventoryCategoriesUrl, data)
	return res
}

export const putInventoryCategory = async (id: string, data: Omit<InventoryCategories, "id">) => {
	const res = await ax.put(`${inventoryCategoriesUrl}${id}/`, data)
	return res
}

export const deleteInventoryCategory = async (id: string) => {
	const res = await ax.delete(`${inventoryCategoriesUrl}${id}/`)
	return res
}

const inventoryBillsUrl = "/inventory/bills/"

export const getInventoryBills = async (): Promise<SupplierBillls[]> => {
	const res = await ax.get<SupplierBillls[]>(inventoryBillsUrl)
	return res.data
}

export const postInventoryBill = async (data: Omit<SupplierBillls, "id">) => {
	const res = await ax.post(inventoryBillsUrl, data)
	return res
}

export const putInventoryBill = async (id: string, data: Omit<SupplierBillls, "id">) => {
	const res = await ax.put(`${inventoryBillsUrl}${id}/`, data)
	return res
}

export const deleteInventoryBill = async (id: string) => {
	const res = await ax.delete(`${inventoryBillsUrl}${id}/`)
	return res
}



