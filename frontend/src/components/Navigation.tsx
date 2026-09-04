
import { forwardRef } from 'react'
import Button from './Button'
import { HugeiconsIcon } from '@hugeicons/react'
import { ArrowDown01Icon,  BoxIcon, Coupon01Icon, DashboardSquare01Icon, Invoice03Icon, Logout05Icon, RightToLeftListDashIcon, Trolley02Icon } from '@hugeicons/core-free-icons'
import { useTranslation } from 'react-i18next'
import { useLocation, useNavigate } from 'react-router'
import Dropdown from './Dropdown'
import useOpenMenu from '../hooks/useOpenMenu'
import { useMutation, useQuery } from '@tanstack/react-query'
import { logout } from '../features/auth'
import { getUnreadNotifications } from '../features/orders/services/orders.service'
import { setAuthHeader } from '../services/api'
import { useBoundStore } from '../store/useBoundStore'

interface NavigationProps {
  className?: string
}

const Navigation = forwardRef<HTMLDivElement, NavigationProps>(({ className }, ref) => {
  const location = useLocation()
  const navigate = useNavigate()
  const user = useBoundStore(state => state.authSlice.user)
  const setIsAuthenticated = useBoundStore(state => state.authSlice.actions.setIsAuthenticated)
  const setIsGuest = useBoundStore(state => state.authSlice.actions.setIsGuest)
  const setUser = useBoundStore(state => state.authSlice.actions.setUser)
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
  const { isOpen: isOpenWareHouse, setIsOpen: setIsOpenWareHouse } = useOpenMenu()
  const { isOpen: isOpenOrders, setIsOpen: setIsOpenOrders } = useOpenMenu()
  const { isOpen: isOpenSuppliers, setIsOpen: setIsOpenSuppliers } = useOpenMenu()
  const { t } = useTranslation()
  const navigarte = useNavigate()
  
  return (
    <div ref={ref} className={className}>
      <div className='*:mb-2'>
        <div className='flex items-center justify-between space-x-2'>
          <div className='relative w-full' ref={userButtonRef}>
            <Button size='sm' onClick={() => { setIsOpenUserButton(!isOpenUserButton) }} variants='ghost'
            className='w-full justify-start'
              leftIcon={<div className='h-full aspect-square rounded-sm flex justify-center items-center text-dark-text-primary bg-amber-700'>{user.first_name[0]}</div>}
              rightIcon={<HugeiconsIcon className={` transition-all ease-in-out ${isOpenUserButton ? "rotate-0" : "rotate-180"}`} size={22} icon={ArrowDown01Icon} />}>
             {user.first_name}
            </Button>
            <Dropdown absolute isOpen={isOpenUserButton}>
              <Button onClick={() => { mutation.mutate() }} className='w-full text-light-text-error-hover hover:text-light-text-error-hover dark:text-dark-text-error-hover dark:hover:text-dark-text-error-hover' size='sm' rightIcon={<HugeiconsIcon size={22} icon={Logout05Icon} />} variants='ghost'>{t('logout')}</Button>
            </Dropdown>
          </div>
        </div>
        <Button active={location.pathname.includes("products")} size='sm' onClick={() => { navigarte("/app/products", { state: { location: "Products" } }); }} className={`w-full justify-start`} leftIcon={<HugeiconsIcon size={22} icon={BoxIcon} />} variants='ghost'>{t('Products')}</Button>
        <div>
          <Button size='sm'
            onClick={() => { setIsOpenSuppliers(!isOpenSuppliers) }}
            className={`w-full justify-start`}
            leftIcon={<HugeiconsIcon size={22} icon={Trolley02Icon} />}
            rightIcon={<HugeiconsIcon className={` transition-all ease-in-out ${isOpenSuppliers ? "rotate-0" : "rotate-180"}`} size={22} icon={ArrowDown01Icon} />}
            variants='ghost'>{t('Supplier')}</Button>
          <Dropdown isOpen={isOpenSuppliers}>
            <Button
              size='sm'
              className={`w-full justify-start`}
              variants='ghost'
              active={location.pathname === "/app/supplier"}
              leftIcon={<HugeiconsIcon size={22} icon={Trolley02Icon} />}
              onClick={() => { navigarte("/app/supplier", { state: { location: "Supplier" } }); }}
            >
              {t('suppliersList')}
            </Button>
            <Button
              size='sm'
              className={`w-full justify-start`}
              variants='ghost'
              active={location.pathname.includes("supplier/bills")}
              leftIcon={<HugeiconsIcon size={22} icon={Invoice03Icon} />}
              onClick={() => { navigarte("/app/supplier/bills", { state: { location: "supplierBills" } }); }}
            >
              {t('supplierBills')}
            </Button>
          </Dropdown>
        </div>
        <div>
          <Button size='sm'
            onClick={() => { setIsOpenWareHouse(!isOpenWareHouse) }}
            className={`w-full justify-start`}
            rightIcon={<HugeiconsIcon className={` transition-all ease-in-out ${isOpenWareHouse ? "rotate-0" : "rotate-180"}`} size={22} icon={ArrowDown01Icon} />}
            variants='ghost'>{t('inventory')}</Button>
          <Dropdown isOpen={isOpenWareHouse}>
            <Button
              size='sm'
              className={`w-full justify-start`}
              variants='ghost'
              active={location.pathname.includes("inventory/categories")}
              leftIcon={<HugeiconsIcon size={22} icon={DashboardSquare01Icon} />}
              onClick={() => { navigarte("/app/inventory/categories/", { state: { location: "inventory" } }); }}
            >
              {t('categories')}
            </Button>
            <Button
              size='sm'
              className={`w-full justify-start`}
              variants='ghost'
              active={location.pathname.includes("inventory/items")}
              leftIcon={<HugeiconsIcon size={22} icon={RightToLeftListDashIcon} />}
              onClick={() => { navigarte("/app/inventory/items", { state: { location: "inventory" } }); }}
            >
              {t('items')}
            </Button>
          </Dropdown>
        </div>
        <div>
          <Button size='sm'
            onClick={() => { setIsOpenOrders(!isOpenOrders) }}
            className={`w-full justify-start`}
            rightIcon={<HugeiconsIcon className={` transition-all ease-in-out ${isOpenOrders ? "rotate-0" : "rotate-180"}`} size={22} icon={ArrowDown01Icon} />}
            variants='ghost'>{t('Orders')}</Button>
          <Dropdown isOpen={isOpenOrders}>
            <Button
              size='sm'
              className={`w-full justify-start`}
              variants='ghost'
              active={location.pathname === "/app/orders"}
              leftIcon={<HugeiconsIcon size={22} icon={Invoice03Icon} />}
              onClick={() => { navigarte("/app/orders", { state: { location: "orders" } }); }}
            >
              {t('orders')}
            </Button>
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
          </Dropdown>
        </div>
        <Button active={location.pathname.includes("finance")} size='sm' onClick={() => { navigarte("/app/finance", { state: { location: "finance" } }); }} className={`w-full justify-start`} leftIcon={<HugeiconsIcon size={22} icon={Coupon01Icon} />} variants='ghost'>{t('finance')}</Button>
      </div>
    </div>
  )
})


export default Navigation