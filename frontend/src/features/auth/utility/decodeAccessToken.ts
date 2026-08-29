import { jwtDecode } from 'jwt-decode';
import type { Roles } from '../types/roles';

interface JwtPayload {
exp: number
iat: number
jti:string
role: Roles
token_type: string
user_id: string
first_name:string
last_name:string
email:string
}

export const decodeAccessToken = (token: string): JwtPayload | null => {
  try {
    return jwtDecode<JwtPayload>(token);
  } catch (error) {
    console.error('Invalid JWT token:', error);
    return null;
  }
};
