import { forwardRef } from "react"
import Button from "./Button"
import { HugeiconsIcon } from "@hugeicons/react"
import { Close } from "@hugeicons/core-free-icons"
import Text from "./Text"

export interface ModelProps {
    className?: string
    children?: React.ReactNode
    isOpen: boolean
    title: string
    onClick: React.MouseEventHandler<HTMLButtonElement>
}

const Model = forwardRef<HTMLDivElement, ModelProps>(({ title, isOpen, className, children, onClick }, ref) => {
    return (
        <div className={`fixed inset-0 z-30 bg-black/15 transition-all duration-200 ease-in-out ${isOpen ? "opacity-100 visible" : "opacity-0 invisible"} ${className}`}>
            <div ref={ref} className={`duration-200 ease-in-out ${isOpen ? "opacity-100 visible" : "opacity-0 invisible"} absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 max-md:w-11/12 md:min-w-3xs p-4 rounded-2xl dark:bg-dark-background-tertiary bg-light-background-tertiary drop-shadow-2xl border dark:border-dark-border-tertiary border-light-border-secondary`}>
                <div className="flex items-center justify-between gap-x-2 mb-4">
                    <Text weight="semibold">{title}</Text>
                    <Button onClick={onClick} size="xs" variants="ghost" iconOnly={true} leftIcon={<HugeiconsIcon size={18} icon={Close} />} />
                </div>
                {children}
            </div>
        </div>
    )
})

export default Model