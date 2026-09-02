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
ax.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest: any = error?.config

        if (!originalRequest) return Promise.reject(error)

        if (originalRequest._retry) return Promise.reject(error)

        const status = error?.response?.status
        if (status === 401) {
            // Don't try to refresh if the refresh endpoint itself returned 401
            if (originalRequest.url && originalRequest.url.includes("/auth/token/refresh/")) {
                try {
                    await logout()
                } catch (e) {
                    // ignore
                }
                window.location.href = "/login"
                return Promise.reject(error)
            }

            if (isRefreshing) {
                return new Promise((resolve, reject) => {
                    failedQueue.push({ resolve, reject })
                }).then((token) => {
                    if (token) originalRequest.headers = { ...originalRequest.headers, Authorization: `Bearer ${token}` }
                    return ax(originalRequest)
                })
            }

            originalRequest._retry = true
            isRefreshing = true

            try {
                const data = await relogin()
                const access = data?.access ?? null
                if (access) setAuthHeader(access)
                processQueue(null, access)
                return ax(originalRequest)
            } catch (err) {
                processQueue(err, null)
                try {
                    await logout()
                } catch (e) {
                    // ignore
                }
                window.location.href = "/login"
                return Promise.reject(err)
            } finally {
                isRefreshing = false
            }
        }

        return Promise.reject(error)
    }
)