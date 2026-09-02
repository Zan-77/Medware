import { tv, type VariantProps } from "tailwind-variants";



const baseButtonStyle = tv({
    base: "flex justify-center items-center select-none transition-colors  font-medium align-ba text-light-text-muted hover:text-light-text-primary dark:text-dark-text-muted dark:hover:text-dark-text-primary",

    variants: {
        variants: {
            primary: "dark:bg-dark-button-background-primary dark:hover:bg-dark-button-background-primary-hover bg-light-button-background-primary hover:bg-light-button-background-primary-hover dark:text-dark-text-primary dark:hover:text-dark-text-primary text-dark-text-primary hover:text-dark-text-primary",
            secondary: "dark:bg-dark-button-background-secondary dark:hover:bg-dark-button-background-secondary-hover/50 bg-light-button-background-secondary hover:bg-light-button-background-secondary-hover border-2 border-light-border-secondary dark:border-dark-border-primary dark:hover:border-dark-border-primary-hover",
            border: "border-2 dark:border-dark-border-primary dark:hover:border-dark-border-primary-hover dark:hover:bg-dark-button-background-secondary-hover/20  border-light-border-primary hover:border-light-border-primary-hover",
            ghost: "dark:hover:bg-dark-button-background-secondary-hover hover:dark:bg-dark-button-background-secondary-hover/50 hover:bg-dark-button-background-secondary-hover/10"
        },
        active: {
            true: "",
            false: ""
        },
        size: {
            xs: "py-1.5 px-2.5 h-6 gap-x-2.5",
            sm: "py-1.5 px-2.5 h-8 gap-x-2.5",
            md: "py-1.5 px-2.5 h-10 gap-x-2.5",
            lg: "py-2 px-4 h-12 gap-x-4",

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
        iconOnly: {
            true: "px-0 aspect-square rounded-full",
            false: ""
        },
        disabled: {
            true: "hover:cursor-progress opacity-70",
            false: "hover:cursor-pointer"
        }
    },
    compoundVariants: [
        {
            variants: "ghost",
            active: true,
            className: "dark:text-dark-text-primary text-light-text-primary dark:bg-dark-button-background-secondary-hover/50 bg-dark-button-background-secondary-hover/10"
        },
        {
            variants: "border",
            active: true,
            className: "dark:bg-dark-button-background-secondary-hover bg-light-button-background-secondary-hover"
        }
    ],
    defaultVariants: {
        variants: "primary",
        size: "md",
        active: false,
        disabled: false,
        rounded: "lg",
        iconOnly: false
    }
})



type ButtonVariants = VariantProps<typeof baseButtonStyle>

interface ButtonProps extends ButtonVariants {
    children?: React.ReactNode
    leftIcon?: React.ReactNode
    rightIcon?: React.ReactNode
    className?: string
    type?: React.ButtonHTMLAttributes<HTMLButtonElement>["type"]
    onClick?: React.MouseEventHandler<HTMLButtonElement>
    ref?: any
}

/**
 * Reusable button component with theme-aware styles and size presets.
 *
 * Supports three visual variants (`primary`, `secondary`, `tertiary`),
 * `md` and `lg` sizing, optional left/right icons, and an `iconOnly`
 * mode for square icon buttons.
 */
const Button = ({ children, type, className, leftIcon, rightIcon, ref, onClick, ...variants }: ButtonProps) => {

    return (
        <button ref={ref} type={type} className={baseButtonStyle({ ...variants, className })} onClick={onClick}>
            {leftIcon}
            {children}
            {rightIcon}
        </button>
    )
}

export default Button