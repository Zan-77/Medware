import { create } from "zustand"
import { immer } from 'zustand/middleware/immer';
import { devtools } from 'zustand/middleware';
import { createAuthSlice, type AuthSliceSate } from "../features/auth/authSlice";
import { createAppSlice ,type AppSliceState } from "./appSlice";

type StoreState = AuthSliceSate & AppSliceState

export const useBoundStore = create<StoreState>()(
    devtools(
        immer((set, get, api) => ({
            ...createAuthSlice(set as never, get as never, api as never),
            ...createAppSlice(set as never, get as never, api as never),
        }))
    )
)