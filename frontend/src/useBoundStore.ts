import { create } from "zustand"
import { immer } from 'zustand/middleware/immer';
import { devtools } from 'zustand/middleware';
import { createAuthSlice, type AuthSliceSate } from "./features/auth/AuthSlice";

type StoreState = AuthSliceSate

export const useBoundStore = create<StoreState>()(
    devtools(
        immer((...a) => (
            {
               ...createAuthSlice(...a)
            }
        ))
    )
)