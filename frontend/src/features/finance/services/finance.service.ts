import ax from "../../../services/api"
import type { CustomerAccount, CustomerStatement, NewVoucher, Voucher } from "../types/finance"

const accountsUrl = "/finance/customer-accounts/"
const vouchersUrl = "/finance/vouchers/"

export const getCustomerAccounts = async (): Promise<CustomerAccount[]> => {
	const res = await ax.get<CustomerAccount[]>(accountsUrl)
	return res.data
}

export const getCustomerStatement = async (customerId: string): Promise<CustomerStatement> => {
	const res = await ax.get<CustomerStatement>(`${accountsUrl}${customerId}/statement/`)
	return res.data
}

// `salesman` is derived server-side from the customer's own order; sending one
// would be ignored, so it is not part of the payload.
export const postVoucher = async (data: NewVoucher): Promise<Voucher> => {
	const res = await ax.post<Voucher>(vouchersUrl, data)
	return res.data
}

export const getVouchers = async (customerId?: string | number): Promise<Voucher[]> => {
	const res = await ax.get<Voucher[]>(vouchersUrl, {
		params: customerId ? { customer: customerId } : undefined,
	})
	return res.data
}
