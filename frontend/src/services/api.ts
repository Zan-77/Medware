import axios from "axios"


const ax = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL,
    withCredentials: true,
})

export const setAuthHeader = (token: string | null) => {
    const headers = { ...(ax.defaults.headers ?? {}) } as typeof ax.defaults.headers & {
        Authorization?: string
    }

    if (token) {
        headers.Authorization = `Bearer ${token}`
    } else {
        delete headers.Authorization
    }

    ax.defaults.headers = headers
}


export default ax