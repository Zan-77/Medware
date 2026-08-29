import { forwardRef } from "react"
import Button from "./Button"
import { HugeiconsIcon } from "@hugeicons/react"
import { Close } from "@hugeicons/core-free-icons"

interface ToastProps {
  className?: string
  isOpen: boolean
  children?: React.ReactNode
  onClick: React.MouseEventHandler<HTMLButtonElement>
}

const Toast = forwardRef<HTMLDivElement, ToastProps>(({ children, isOpen, className, onClick }, ref) => {
  return (
    <div
      ref={ref}
      className={`
        absolute bottom-4 right-3 z-30 w-56 rounded-xl border
        border-light-border-secondary bg-light-background-tertiary p-2
        drop-shadow-2xl transition-all duration-300 ease-out
        dark:border-dark-border-tertiary dark:bg-dark-background-tertiary
        ${isOpen ? "visible translate-y-0 opacity-100" : "invisible translate-y-2 opacity-0"}
        ${className ?? ""}
      `}
    >
      <div className="flex items-center justify-between gap-2">
        {children}
        <Button onClick={onClick} size="xs" variants="ghost" iconOnly={true} leftIcon={<HugeiconsIcon size={18} icon={Close} />} />
      </div>
    </div>
  )
})

export default Toast