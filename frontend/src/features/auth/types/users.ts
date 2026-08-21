import type { Roles } from "./roles"

export interface User  {
    id:string,
    username:string,
    password:string,
    email:string,
    role:Roles,
    //is_staff:boolean,
    //is_superuser:boolean
}

export type UserWithoutPassword= Omit<User, "password">


