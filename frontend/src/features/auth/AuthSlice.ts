import { type StateCreator } from "zustand"
import type { UserWithoutPassword } from "./types/users"
import type { RegisterFieldsValues } from "./types/authForms"



export interface AuthSliceSate {
    authSlice: {
        registerformData: RegisterFieldsValues
        user: UserWithoutPassword
        isGuest: boolean
        isAuthenticated: boolean
        actions: {
            resetRegisterformData: () => void
            setRegisterformData: (user: RegisterFieldsValues) => void
            setIsAuthenticated: (isAuthenticated: boolean) => void
            setUser: (user: UserWithoutPassword) => void
            setIsGuest: (isGuest: boolean) => void
        }
    }

}

export const createAuthSlice: StateCreator<AuthSliceSate, [["zustand/immer", never]], [["zustand/devtools", never]]> = (set) =>
(
    {
        authSlice: {
            registerformData: {
                email: "",
                password: "",
                confirmPassword: "",
                role: "GUEST",
                username: ""
            },
            user: {
                id: "",
                email: "",
                role: "GUEST",
                username: ""
            },
            isGuest: true,
            isAuthenticated: false,
            actions: {
                resetRegisterformData: () => {
                    set((state) => {
                        state.authSlice.registerformData = {
                            email: "",
                            password: "",
                            confirmPassword: "",
                            role: "GUEST",
                            username: ""
                        }
                    })
                },
                setRegisterformData(registerformData) {
                    set((state) => { state.authSlice.registerformData = registerformData })

                },
                setIsAuthenticated: (isAuthenticated) => {
                    set((state) => { state.authSlice.isAuthenticated = isAuthenticated })
                }, setIsGuest: (isGuest) => {
                    set((state) => { state.authSlice.isGuest = isGuest })
                },
                setUser(user) {
                    set((state) => { state.authSlice.user = user })
                },
            }
        }
    }
)