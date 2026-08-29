import { tv, type VariantProps } from "tailwind-variants"
import Input, { baseInputStyle } from "./Input"
import { useController, type FieldValues, type UseControllerProps } from "react-hook-form"
import { useTranslation } from "react-i18next"
import Text from "./Text"
import type { HTMLInputTypeAttribute } from "react"



const baseControlledInputStyle = tv({
    extend: baseInputStyle,
    base: "border-0",
    variants: {
        state: {
            ok: "dark:*:border-dark-border-ok dark:*:hover:border-dark-border-ok-hover *:border-dark-border-ok *:hover:border-dark-border-ok text-ok",
            error: "dark:*:border-dark-border-error dark:*:hover:border-dark-border-error-hover *:border-light-border-error *:hover:border-light-border-error hover:text-light-text-error-hover text-error dark:hover:text-dark-text-error-hover",
        }
    },
    defaultVariants: {
        state: "normal"
    }
})

type ControlledInputStyleVariants = VariantProps<typeof baseControlledInputStyle>

type ControlledInputProps<TFieldValues extends FieldValues> = UseControllerProps<TFieldValues> &
    ControlledInputStyleVariants & {
        className?: string
        name: UseControllerProps<TFieldValues>["name"]
        control: NonNullable<UseControllerProps<TFieldValues>["control"]>
        type?: HTMLInputTypeAttribute
        buttonIcon?: React.ReactNode
        autoComplete?: React.InputHTMLAttributes<HTMLInputElement>["autoComplete"]

        onClick?: () => void
    }

const ControlledInput = <TFieldValues extends FieldValues>({ className,autoComplete, type, buttonIcon, onClick, ...props }: ControlledInputProps<TFieldValues>) => {
    const { t } = useTranslation()
    const { field, fieldState, formState } = useController({ ...props })
    const state = fieldState.error || formState.errors.root?.server ? "error" : "normal"

    const errorMessage = fieldState.error?.message
    let renderedError = ""
    if (errorMessage) {
        const translated = t(String(errorMessage))
        renderedError = translated === String(errorMessage) ? String(errorMessage) : translated
    }

    return (
        <div className={baseControlledInputStyle({ state, className })}>
            <Input autoComplete={autoComplete} onClick={onClick} {...field} state={state} type={type} buttonIcon={buttonIcon} legend={t(String(props.name))} />
            <Text color={state} className="ml-4.5 rtl:mr-4.5 select-none">{renderedError}</Text>
        </div>
    )
}


export default ControlledInput