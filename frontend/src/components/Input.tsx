import { type HTMLInputTypeAttribute } from "react"
import { tv, type VariantProps } from "tailwind-variants"
import Text from "./Text"
import Button from "./Button"


export const baseInputStyle = tv({
    base: "border-2 rounded-lg transition-colors",
    variants: {
        state: {
            error: "",
            ok: "",
            normal: "dark:border-dark-border-primary dark:hover:border-dark-border-primary-hover border-light-border-primary hover:border-light-border-primary-hover",
        }
    },
    defaultVariants: {
        state: "normal"
    }
})

type InputVariants = VariantProps<typeof baseInputStyle>

interface InputProps extends InputVariants {
    legend?: string
    type?: HTMLInputTypeAttribute
    className?: string
    buttonIcon?: React.ReactNode
    autoComplete?:React.InputHTMLAttributes<HTMLInputElement>["autoComplete"]
    onClick?: () => void
}

const Input = ({ legend, type, buttonIcon,autoComplete, className,onClick, ...variants }: InputProps) => {
    return (
        <fieldset className={baseInputStyle({ ...variants, className })}>
            <legend className="px-2 ml-2 rtl:mr-2 select-none"><Text color={variants.state}>{legend}</Text></legend>
            <div className="relative mb-2 px-4">
                <input autoComplete={autoComplete} {...variants} type={type} className="w-full rtl:pl-6 ltr:pr-6 h-8 text-sm outline-none" />
                {buttonIcon && <Button type="button" onClick={onClick} variants="ghost" size="sm" className="absolute top-1/2 -translate-y-1/2 left-2" iconOnly>{buttonIcon}</Button>}
            </div>
        </fieldset>
    )
}

export default Input