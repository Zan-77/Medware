import type { StateCreator } from "zustand";

export interface AppSliceState {
    appSlice: {
        location: string
        actions: {
            setLocation: (location: string) => void
        }
    }
}

export const createAppSlice: StateCreator<AppSliceState, [["zustand/immer", never]], [["zustand/devtools", never]]> = set => (
    {
        appSlice: {
            location: "orders",
            actions: {
                setLocation(location) {
                    set(state => {state.appSlice.location = location})
                },
            }
        }
    }
)