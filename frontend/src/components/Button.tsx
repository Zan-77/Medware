import { tv, type VariantProps } from "tailwind-variants";



const baseButtonStyle = tv({
    base: "flex justify-center items-center border select-none border-transparent transition-colors rounded-xl font-medium align-ba dark:text-dark-text-secondary dark:hover:text-dark-text-primary text-light-text-secondary hover:text-light-text-primary",

    variants: {
        variants: {
            primary: "dark:bg-dark-button-background-primary dark:hover:bg-dark-button-background-primary-hover bg-light-button-background-primary hover:bg-light-button-background-primary-hover dark:text-dark-text-primary dark:hover:text-dark-text-primary text-dark-text-primary hover:text-dark-text-primary",
            secondary: "dark:bg-dark-button-background-secondary dark:hover:bg-dark-button-background-secondary-hover bg-light-button-background-secondary hover:bg-light-button-background-secondary-hover",
            border: "dark:border-dark-border-primary dark:hover:border-dark-border-primary-hover dark:hover:bg-dark-button-background-secondary-hover/20 hover:bg-light-button-background-secondary/50 border-light-border-primary hover:border-light-border-primary-hover",
            ghost: "dark:hover:bg-dark-button-background-secondary-hover hover:bg-light-button-background-secondary-hover"
        },
        size: {
            sm: "py-0.5 px-1 h-8 gap-x-1",
            md: "py-1.5 px-2.5 h-10 gap-x-2.5",
            lg: "py-2 px-4 h-12 gap-x-4",

        },
        iconOnly: {
            true: "px-0 aspect-square",
            false: ""
        },
        disabled: {
            true: "hover:cursor-progress opacity-70",
            false: "hover:cursor-pointer"
        }
    },
    defaultVariants: {
        variants: "primary",
        size: "md",
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
    onClick?: () => void
}

/**
 * Reusable button component with theme-aware styles and size presets.
 *
 * Supports three visual variants (`primary`, `secondary`, `tertiary`),
 * `md` and `lg` sizing, optional left/right icons, and an `iconOnly`
 * mode for square icon buttons.
 */
const Button = ({ children,type, className, leftIcon, rightIcon, onClick, ...variants }: ButtonProps) => {

    return (
        <button type={type} className={baseButtonStyle({ ...variants, className })} onClick={onClick}>
            {leftIcon}
            {children}
            {rightIcon}
        </button>
    )
}

export default Button