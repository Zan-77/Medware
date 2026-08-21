import { Outlet } from 'react-router'

export const AuthLayout = () => {
    return (
        <div className='flex justify-center items-center w-full h-dvh'>
            <Outlet />
        </div>
    )
}

