import type { User } from "./users"

export type LoginFieldsValues = Pick<User, "email" | "password">

export type RegisterFieldsValues = Omit<User, "id"> & { confirmPassword: String } 