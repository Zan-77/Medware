import ax from "../../../services/api"

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