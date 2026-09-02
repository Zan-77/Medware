import { Outlet, useLocation } from 'react-router'
import Navigation from '../components/Navigation'
import Text from '../components/Text'
import { LayoutAlignRightIcon } from '@hugeicons/core-free-icons'
import { HugeiconsIcon } from '@hugeicons/react'
import Button from '../components/Button'
import useOpenMenu from '../hooks/useOpenMenu'
import { useTranslation } from 'react-i18next'
import { useLayoutEffect } from 'react'

export const appLayout = () => {
    const { isOpen, setIsOpen, ref:navRef } = useOpenMenu()
    const location =useLocation()
    const { t } = useTranslation()
    useLayoutEffect(() => {
        if (window.innerWidth < 768)
            setIsOpen(false)
        else
            setIsOpen(true)
    },[])
    
    return (
        <div className='flex h-dvh box-border md:p-4'>

            <Navigation 
                ref={navRef}
                className={`px-4 max-md:fixed max-md:inset-y-0 max-md:right-0 z-30 w-3xs max-md:h-full max-md:overflow-hidden max-md:transition-all max-md:duration-250 max-md:dark:shadow-lg max-md:border-r max-md:border-light-border-secondary max-md:dark:border-dark-border-tertiary max-md:dark:bg-dark-background-secondary max-md:bg-light-background-secondary ${isOpen ? 'max-md:w-3xs max-md:visible max-md:opacity-100' : 'max-md:w-0 max-md:invisible max-md:opacity-0'}`}
            />
            <div
                aria-hidden={!isOpen}
                className={`fixed inset-0 z-20 bg-black/30 transition-opacity duration-250 md:hidden ${isOpen ? 'visible opacity-100' : 'pointer-events-none invisible opacity-0'}`}
                onClick={() => setIsOpen(false)}
            />

            <div
                className={`w-full *:p-4 md:border md:rounded-xl
                md:dark:border-dark-border-tertiary
                dark:bg-dark-background-secondary bg-light-background-secondary 
                md:border-light-border-secondary shadow-sm`}>
                <div className='flex gap-x-2 items-center border-b dark:border-dark-border-tertiary border-light-border-secondary'>
                    <Button className='md:hidden' onClick={() => setIsOpen(!isOpen)} size='xs' variants='ghost' iconOnly leftIcon={<HugeiconsIcon size={20} icon={LayoutAlignRightIcon} />} />
                    <Text  weight='medium' className='select-none'>{t(location.state?.location)}</Text>
                    <Text  weight='medium' className='select-none'>{location.state?.details}</Text>
                </div>
                <div>
                    <Outlet />
                </div>
            </div>
        </div>
    )
}
