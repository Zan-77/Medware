
import ax from "../../../services/api"
import type { InventoryCategories, InventoryItemInput, InventoryItems, SupplierBilllLines } from "../types/inventory"
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

const inventoryItemsUrl = "/inventory/items/"

export const getInventoryItems = async (categoryId?: string): Promise<InventoryItems[]> => {
	const res = await ax.get<InventoryItems[]>(inventoryItemsUrl, {
		params: categoryId ? { category: categoryId } : undefined,
	})
	return res.data
}

export const postInventoryItem = async (data: InventoryItemInput) => {
	const res = await ax.post(inventoryItemsUrl, data)
	return res
}

export const putInventoryItem = async (id: string, data: InventoryItemInput) => {
	const res = await ax.put(`${inventoryItemsUrl}${id}/`, data)
	return res
}

export const deleteInventoryItem = async (id: string) => {
	const res = await ax.delete(`${inventoryItemsUrl}${id}/`)
	return res
}

const inventoryBillsUrl = "/inventory/bills/"

// `supplierId` maps to the `?supplier=` filter on SupplierBillViewSet, which is
// how the suppliers table opens "the bills of this supplier".
export const getInventoryBills = async (supplierId?: string): Promise<SupplierBillls[]> => {
	const res = await ax.get<SupplierBillls[]>(inventoryBillsUrl, {
		params: supplierId ? { supplier: supplierId } : undefined,
	})
	return res.data
}


export const getInventoryBillById = async (id: string): Promise<SupplierBillls> => {
	const res = await ax.get<SupplierBillls>(`${inventoryBillsUrl}${id}/`)
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

const inventoryBillLinesUrl = "/inventory/bill-lines/"

export const getSupplierBillLines = async (): Promise<SupplierBilllLines[]> => {
	const res = await ax.get<SupplierBilllLines[]>(inventoryBillLinesUrl)
	return res.data
}

// One bill's lines. The `?bill=` filter is enforced server-side by
// SupplierBillLineViewSet.get_queryset; without it this returned every line in
// the system, which is what made one bill look like it had every other bill's
// rows in it.
export const getSupplierBillLinesById = async (id: string): Promise<SupplierBilllLines[]> => {
	const res = await ax.get<SupplierBilllLines[]>(inventoryBillLinesUrl, { params: { bill: id } })
	return res.data
}

export const postSupplierBillLine = async (data: Omit<SupplierBilllLines, "id">) => {
	const res = await ax.post(inventoryBillLinesUrl, data)
	return res
}

export const putSupplierBillLine = async (id: string, data: Omit<SupplierBilllLines, "id">) => {
	const res = await ax.put(`${inventoryBillLinesUrl}${id}/`, data)
	return res
}

export const deleteSupplierBillLine = async (id: string) => {
	const res = await ax.delete(`${inventoryBillLinesUrl}${id}/`)
	return res
}
