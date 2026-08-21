import axios from "redaxios"


const ax = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL,
    withCredentials: true,
})

export const setAuthHeader = (token: string | null) => {
    const headers = (ax.defaults.headers ?? {}) as Record<string, string>

    if (token) {
        headers.Authorization = `Token ${token}`
        ax.defaults.headers = headers
        
    } else {
        delete headers.Authorization
        ax.defaults.headers = headers
    }
}

export default ax