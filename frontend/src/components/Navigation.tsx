
import { forwardRef, useEffect, useState } from 'react'
import Button from './Button'
import Text from './Text'
import { HugeiconsIcon } from '@hugeicons/react'
import { ArrowDown01Icon, BoxIcon, Coupon01Icon, DashboardSquare01Icon, Invoice03Icon, Logout05Icon, Money01Icon, Moon02Icon, RightToLeftListDashIcon, Sun03Icon, Trolley02Icon } from '@hugeicons/core-free-icons'
import { useTranslation } from 'react-i18next'
import { useLocation, useNavigate } from 'react-router'
import Dropdown from './Dropdown'
import useOpenMenu from '../hooks/useOpenMenu'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { logout } from '../features/auth'
import { getUnreadNotifications } from '../features/orders/services/orders.service'
import { setAuthHeader } from '../services/api'
import { useBoundStore } from '../store/useBoundStore'
import { hasPermission } from '../features/auth'

interface NavigationProps {
  className?: string
}

const SectionLabel = ({ children }: { children: React.ReactNode }) => (
  <Text className='px-2 pt-3 pb-1 text-xs opacity-60 select-none'>{children}</Text>
)

// Home, Employees and Settings have no backend yet. They are rendered so the
// shape of the app is visible, but they navigate nowhere - a nav entry that
// leads to a dead route is the bug this codebase keeps having to fix.
const ComingSoonEntry = ({ icon, label, hint }: { icon: React.ComponentProps<typeof HugeiconsIcon>["icon"]; label: string; hint: string }) => (
  <div className='w-full flex items-center gap-x-2 px-2 py-1.5 rounded-lg opacity-40 cursor-not-allowed select-none'
    aria-disabled='true' title={hint}>
    <HugeiconsIcon size={22} icon={icon} />
    <Text>{label}</Text>
  </div>
)

const Navigation = forwardRef<HTMLDivElement, NavigationProps>(({ className }, ref) => {
  const location = useLocation()
  const navigate = useNavigate()
  const user = useBoundStore(state => state.authSlice.user)
  const setIsAuthenticated = useBoundStore(state => state.authSlice.actions.setIsAuthenticated)
  const setIsGuest = useBoundStore(state => state.authSlice.actions.setIsGuest)
  const setUser = useBoundStore(state => state.authSlice.actions.setUser)
  const queryClient = useQueryClient()
  const mutation = useMutation({
    mutationKey: ["auth", "relogin"],
    mutationFn: logout,
    onError: () => {
      if (location.pathname.includes("/store/"))
        navigate("/store/")
      else
        navigate("/app/auth/login", { relative: "path" })
    },
    onSuccess: () => {
      // Nothing cached belongs to whoever signs in next - and a stale ["me"]
      // would let an unverified account past the approval screen.
      queryClient.clear()
      setAuthHeader('')
      setIsGuest(true)
      setIsAuthenticated(false)
      setUser({ id: "", role: "GUEST", email: "", username: "" ,first_name:"" ,last_name:""})
      if (location.pathname.includes("/store/"))
        navigate("/store/")
      else
        navigate("/app/auth/login", { relative: "path" })

    }
  })
  const { data: unreadNotifications } = useQuery({
    queryKey: ["unreadNotifications"],
    queryFn: getUnreadNotifications,
    refetchInterval: 30000,
  })
  const unreadCount = unreadNotifications?.length ?? 0
  const { isOpen: isOpenUserButton, setIsOpen: setIsOpenUserButton, ref: userButtonRef } = useOpenMenu()
  const { t } = useTranslation()
  const navigarte = useNavigate()
  const [isDarkMode, setIsDarkMode] = useState(() => document.documentElement.classList.contains('dark'))

  useEffect(() => {
    const syncTheme = () => setIsDarkMode(document.documentElement.classList.contains('dark'))
    const observer = new MutationObserver(syncTheme)
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })
    return () => observer.disconnect()
  }, [])

  const toggleTheme = () => {
    const html = document.documentElement
    const nextIsDarkMode = !html.classList.contains('dark')
    html.classList.toggle('dark', nextIsDarkMode)
    html.classList.toggle('light', !nextIsDarkMode)
    setIsDarkMode(nextIsDarkMode)
  }
  
  return (
    <div ref={ref} className={className}>
      <div className='*:mb-2'>
        <div className='flex items-center justify-between space-x-2'>
          <div className='relative w-full' ref={userButtonRef}>
            <Button size='sm' onClick={() => { setIsOpenUserButton(!isOpenUserButton) }} variants='ghost'
            className='w-full justify-start'
              leftIcon={<div className='h-full aspect-square rounded-sm flex justify-center items-center text-dark-text-primary bg-amber-700'>{user.first_name[0]}</div>}
              rightIcon={<HugeiconsIcon className={` transition-all ease-in-out ${isOpenUserButton ? "rotate-0" : "rotate-180"}`} size={22} icon={ArrowDown01Icon} />}>
             <span className='flex flex-col items-start leading-tight'>
               <Text>{user.first_name}</Text>
               <Text className='text-xs opacity-60'>{t(user.role)}</Text>
             </span>
            </Button>
            <Dropdown absolute isOpen={isOpenUserButton}>
              <Button onClick={() => { mutation.mutate() }} className='w-full text-light-text-error-hover hover:text-light-text-error-hover dark:text-dark-text-error-hover dark:hover:text-dark-text-error-hover' size='sm' rightIcon={<HugeiconsIcon size={22} icon={Logout05Icon} />} variants='ghost'>{t('logout')}</Button>
            </Dropdown>
          </div>
          <Button
            type='button'
            size='sm'
            variants='ghost'
            iconOnly
            aria-label={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
            onClick={toggleTheme}
            leftIcon={<HugeiconsIcon size={20} icon={isDarkMode ? Sun03Icon : Moon02Icon} />}
          />
        </div>
        <ComingSoonEntry icon={DashboardSquare01Icon} label={t('home')} hint={t('comingSoon')} />

        <Button
          size='sm'
          className={`w-full justify-start`}
          variants='ghost'
          active={location.pathname.includes("/app/requests")}
          leftIcon={<HugeiconsIcon size={22} icon={RightToLeftListDashIcon} />}
          rightIcon={unreadCount > 0
            ? <span className="min-w-5 px-1.5 rounded-full text-xs bg-error text-dark-text-primary">{unreadCount}</span>
            : undefined}
          onClick={() => { navigarte("/app/requests", { state: { location: "requests" } }); }}
        >
          {t('requests')}
        </Button>

        {user.role === 'MANAGER' && (
          <Button
            size='sm'
            className={`w-full justify-start`}
            variants='ghost'
            active={location.pathname.includes("/app/approvals")}
            leftIcon={<HugeiconsIcon size={22} icon={DashboardSquare01Icon} />}
            onClick={() => { navigarte("/app/approvals", { state: { location: "approvals" } }); }}
          >
            {t('approvals')}
          </Button>
        )}

        <SectionLabel>{t('inventory')}</SectionLabel>
        <Button size='sm' className={`w-full justify-start`} variants='ghost'
          active={location.pathname.includes("inventory/categories")}
          leftIcon={<HugeiconsIcon size={22} icon={DashboardSquare01Icon} />}
          onClick={() => { navigarte("/app/inventory/categories/", { state: { location: "inventory" } }); }}>
          {t('categories')}
        </Button>
        <Button size='sm' className={`w-full justify-start`} variants='ghost'
          active={location.pathname.includes("inventory/items")}
          leftIcon={<HugeiconsIcon size={22} icon={BoxIcon} />}
          onClick={() => { navigarte("/app/inventory/items", { state: { location: "inventory" } }); }}>
          {t('items')}
        </Button>
        <Button size='sm' className={`w-full justify-start`} variants='ghost'
          active={location.pathname === "/app/products"}
          leftIcon={<HugeiconsIcon size={22} icon={BoxIcon} />}
          onClick={() => { navigarte("/app/products", { state: { location: "Products" } }); }}>
          {t('Products')}
        </Button>

        <SectionLabel>{t('inbound')}</SectionLabel>
        <Button size='sm' className={`w-full justify-start`} variants='ghost'
          active={location.pathname === "/app/orders"}
          leftIcon={<HugeiconsIcon size={22} icon={Invoice03Icon} />}
          onClick={() => { navigarte("/app/orders", { state: { location: "orders" } }); }}>
          {t('orders')}
        </Button>
        <Button size='sm' className={`w-full justify-start`} variants='ghost'
          active={location.pathname.includes("/app/customers")}
          leftIcon={<HugeiconsIcon size={22} icon={Trolley02Icon} />}
          onClick={() => { navigarte("/app/customers", { state: { location: "customers" } }); }}>
          {t('customers')}
        </Button>

        <SectionLabel>{t('outbound')}</SectionLabel>
        <Button size='sm' className={`w-full justify-start`} variants='ghost'
          active={location.pathname === "/app/supplier"}
          leftIcon={<HugeiconsIcon size={22} icon={Trolley02Icon} />}
          onClick={() => { navigarte("/app/supplier", { state: { location: "Supplier" } }); }}>
          {t('suppliersList')}
        </Button>
        <Button size='sm' className={`w-full justify-start`} variants='ghost'
          active={location.pathname.includes("supplier/bills")}
          leftIcon={<HugeiconsIcon size={22} icon={Invoice03Icon} />}
          onClick={() => { navigarte("/app/supplier/bills", { state: { location: "supplierBills" } }); }}>
          {t('supplierBills')}
        </Button>

        {hasPermission(user, 'finance', 'read') && <>
          <SectionLabel>{t('finance')}</SectionLabel>
          <Button size='sm' className={`w-full justify-start`} variants='ghost'
            active={location.pathname.includes("/app/finance")}
            leftIcon={<HugeiconsIcon size={22} icon={Money01Icon} />}
            onClick={() => { navigarte("/app/finance", { state: { location: "finance" } }); }}>
            {t('customerAccounts')}
          </Button>
        </>}

        <ComingSoonEntry icon={Trolley02Icon} label={t('employees')} hint={t('comingSoon')} />

        <SectionLabel>{t('preferences')}</SectionLabel>
        <ComingSoonEntry icon={Coupon01Icon} label={t('settings')} hint={t('comingSoon')} />
      </div>
    </div>
  )
})


export default Navigation