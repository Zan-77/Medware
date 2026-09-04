import ax from "../../../services/api"
import type { AppNotification, Customer, OrderInbox, OrderRequest } from "../types/orders"

const ordersUrl = "/orders/order-requests/"

export const getOrders = async (status?: string): Promise<OrderRequest[]> => {
	const res = await ax.get<OrderRequest[]>(ordersUrl, {
		params: status ? { status } : undefined,
	})
	return res.data
}

export const getOrderById = async (id: string): Promise<OrderRequest> => {
	const res = await ax.get<OrderRequest>(`${ordersUrl}${id}/`)
	return res.data
}

// `status`, `origin` and `salesman` are set by the server and must not be sent.
export const postOrder = async (data: {
	customer: string | number
	notes: string
	items: Array<{ product: string | number; quantity: number; sell_price: number; note: string }>
}) => {
	const res = await ax.post<OrderRequest>(ordersUrl, data)
	return res.data
}

export const approveOrder = async (id: string): Promise<OrderRequest> => {
	const res = await ax.post<OrderRequest>(`${ordersUrl}${id}/approve/`)
	return res.data
}

// The backend returns 400 when `notes` is blank - a rejection never reaches a
// salesman without a reason.
export const rejectOrder = async (id: string, notes: string): Promise<OrderRequest> => {
	const res = await ax.post<OrderRequest>(`${ordersUrl}${id}/reject/`, { notes })
	return res.data
}

export const getInbox = async (): Promise<OrderInbox> => {
	const res = await ax.get<OrderInbox>("/orders/inbox/")
	return res.data
}

export const getUnreadNotifications = async (): Promise<AppNotification[]> => {
	const res = await ax.get<AppNotification[]>("/notifications/", { params: { unread: "true" } })
	return res.data
}

export const markNotificationRead = async (id: number) => {
	const res = await ax.post(`/notifications/${id}/read/`)
	return res.data
}

export const getCustomers = async (): Promise<Customer[]> => {
	const res = await ax.get<Customer[]>("/customers/")
	return res.data
}
