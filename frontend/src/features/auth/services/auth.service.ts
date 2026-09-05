import ax, { setAuthHeader } from "../../../services/api"

import type { LoginFieldsValues, RegisterFieldsValues } from "../types/authForms"

interface AuthReturn {
    access: string
    refresh: string
}


export async function login(data: LoginFieldsValues): Promise<AuthReturn> {
    const res = await ax.post("/auth/token/", data)

    return res.data
}


export async function register(data: RegisterFieldsValues): Promise<AuthReturn> {
    const res = await ax.post("/auth/register/", data)
    return res.data
}

export async function relogin(): Promise<AuthReturn> {
    const res = await ax.post("/auth/token/refresh/")
    return res.data
}

export interface CurrentUser {
    id: string
    username: string
    email: string
    role: string
    role_display: string
    is_verified: boolean
    is_staff: boolean
    is_superuser: boolean
}

// The token claim is a 15-minute-old snapshot, so after a manager approves an
// account it lags. This endpoint answers from the row and is authoritative -
// the backend authorises off the same value.
export async function getCurrentUser(): Promise<CurrentUser> {
    const res = await ax.get<CurrentUser>("/users/me/")
    return res.data
}

export async function logout(): Promise<AuthReturn> {
    const res = await ax.post("/auth/logout/")
    return res.data
}


// Response interceptor to handle 401 (unauthorized) responses.
// It attempts a token refresh via `relogin()`, retries the original request
// with the new access token, and on failure triggers `logout()` and redirects
// to the login page.
let isRefreshing = false
let failedQueue: Array<{ resolve: (value?: any) => void; reject: (err?: any) => void }> = []

const processQueue = (error: any, token: string | null = null) => {
    failedQueue.forEach((p) => {
        if (error) p.reject(error)
        else p.resolve(token)
    })
    failedQueue = []
}

// The endpoints that mint tokens must never be retried through this path: a
// 401 from them means the credentials/refresh cookie are genuinely invalid,
// and refreshing in response would recurse.
const isAuthEndpoint = (url: string) =>
    url.includes("/auth/token/") || url.includes("/auth/logout/")

ax.interceptors.response.use(
    (response) => response,
    async (error) => {
        const original = error?.config as (typeof error.config & { _retry?: boolean }) | undefined

        if (error?.response?.status !== 401 || !original || original._retry || isAuthEndpoint(original.url ?? "")) {
            return Promise.reject(error)
        }

        original._retry = true

        // A refresh is already in flight: queue this request and replay it
        // with whatever token that refresh produces, so a page that fired ten
        // queries at once does not fire ten refreshes.
        if (isRefreshing) {
            return new Promise<string | null>((resolve, reject) => {
                failedQueue.push({ resolve, reject })
            }).then((token) => {
                original.headers = { ...original.headers, Authorization: `Bearer ${token}` }
                return ax(original)
            })
        }

        isRefreshing = true

        try {
            const data = await relogin()
            setAuthHeader(data.access)
            processQueue(null, data.access)
            original.headers = { ...original.headers, Authorization: `Bearer ${data.access}` }
            return await ax(original)
        } catch (refreshError) {
            processQueue(refreshError)
            setAuthHeader(null)
            try {
                await logout()
            } catch {
                // The session is gone either way - never let a failing logout
                // swallow the redirect below.
            }
            if (typeof window !== "undefined" && !window.location.pathname.includes("/store")) {
                window.location.assign("/app/auth/login")
            }
            return Promise.reject(refreshError)
        } finally {
            isRefreshing = false
        }
    },
)