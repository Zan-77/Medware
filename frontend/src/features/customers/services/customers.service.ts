import ax from "../../../services/api"
import type { Customer } from "../types/customers"

const customersUrl = "/customers/"

export const getCustomers = async (status?: string): Promise<Customer[]> => {
	const res = await ax.get<Customer[]>(customersUrl, {
		params: status ? { status } : undefined,
	})
	return res.data
}

// `status`, `created_by` and `rejection_notes` are set by the server.
export const postCustomer = async (data: Pick<Customer, "name" | "phone" | "address" | "notes">) => {
	const res = await ax.post<Customer>(customersUrl, data)
	return res.data
}

export const putCustomer = async (id: string, data: Pick<Customer, "name" | "phone" | "address" | "notes">) => {
	const res = await ax.put<Customer>(`${customersUrl}${id}/`, data)
	return res.data
}

export const deleteCustomer = async (id: string) => {
	const res = await ax.delete(`${customersUrl}${id}/`)
	return res
}

export const approveCustomer = async (id: string): Promise<Customer> => {
	const res = await ax.post<Customer>(`${customersUrl}${id}/approve/`)
	return res.data
}

// The backend returns 400 when `notes` is blank - a rejection never reaches
// the salesman without a reason.
export const rejectCustomer = async (id: string, notes: string): Promise<Customer> => {
	const res = await ax.post<Customer>(`${customersUrl}${id}/reject/`, { notes })
	return res.data
}
