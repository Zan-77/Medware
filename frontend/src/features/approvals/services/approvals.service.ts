import ax from "../../../services/api"
import type { Account } from "../types/approvals"

const accountsUrl = "/users/manage/"

export const getAccounts = async (): Promise<Account[]> => {
	const res = await ax.get<Account[]>(accountsUrl)
	return res.data
}

// The server refuses a manager changing their own account or a superuser's,
// and ignores every field but these two.
export const patchAccount = async (
	id: string,
	data: { role?: string; is_verified?: boolean },
): Promise<Account> => {
	const res = await ax.patch<Account>(`${accountsUrl}${id}/`, data)
	return res.data
}
