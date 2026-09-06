import { type HTMLInputTypeAttribute } from "react"
import { tv, type VariantProps } from "tailwind-variants"
import Text from "./Text"
import Button from "./Button"


export const baseInputStyle = tv({
    base: "border-2  transition-colors min-w-40 w-full",
    variants: {
        state: {
            error: "",
            ok: "",
            normal: "dark:border-dark-border-primary dark:hover:border-dark-border-primary-hover border-light-border-primary hover:border-light-border-primary-hover",
        },
        rounded: {
            xs: "rounded-xs",
            sm: "rounded-sm",
            md: "rounded-md",
            lg: "rounded-lg",
            xl: "rounded-xl",
            "2xl": "rounded-2xl",
            full: "rounded-full",

        },
    },
    defaultVariants: {
        state: "normal",
        rounded:"lg"
    }
})

type InputVariants = VariantProps<typeof baseInputStyle>

export interface InputProps extends InputVariants, Omit<React.InputHTMLAttributes<HTMLInputElement>, "type" | "className"> {
    legend?: string
    type?: HTMLInputTypeAttribute
    className?: string
    buttonIcon?: React.ReactNode
    autoComplete?: React.InputHTMLAttributes<HTMLInputElement>["autoComplete"]
    fieldset?: boolean
    onClick?: () => void
}

const Input = ({ legend, type, buttonIcon, autoComplete, className, fieldset = true, onClick, ...rest }: InputProps) => {
    return (
        fieldset ? <fieldset className={baseInputStyle({ ...rest, className })}>
            <legend className="px-2 ml-2 rtl:mr-2 select-none"><Text color={rest.state}>{legend}</Text></legend>
            <div className="relative">
                <input autoComplete={autoComplete} {...rest} type={type} className="w-full rtl:pl-6 ltr:pr-6 h-8 outline-none pb-2 px-4" />
                {buttonIcon && <Button type="button" onClick={onClick} variants="ghost" size="sm" className="absolute -top-1\  left-2" iconOnly>{buttonIcon}</Button>}
            </div>
        </fieldset> :
            <div className={baseInputStyle({ ...rest, className })}>
                <div className="relative">
                    <input autoComplete={autoComplete} {...rest} placeholder={rest.placeholder} type={type} className=" w-full rtl:pl-6 ltr:pr-6 outline-none py-1 px-4" />
                    {buttonIcon && <Button type="button" onClick={onClick} variants="ghost" size="sm" className="absolute top-1/2 -translate-y-1/2 left-2" iconOnly>{buttonIcon}</Button>}
                </div>
            </div>
    )
}

export default Input    