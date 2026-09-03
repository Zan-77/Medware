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
            control?: NonNullable<UseControllerProps<TFieldValues>["control"]>
        type?: HTMLInputTypeAttribute
        buttonIcon?: React.ReactNode
        autoComplete?: React.InputHTMLAttributes<HTMLInputElement>["autoComplete"]
        placeholder?: string
        value?: string
        onChange?: React.ChangeEventHandler<HTMLInputElement>
        onBlur?: React.FocusEventHandler<HTMLInputElement>
        onFocus?: React.FocusEventHandler<HTMLInputElement>
        onClick?: () => void
        state?: "normal" | "error" | "ok"
        legend?: string
    }

const ControlledInput = <TFieldValues extends FieldValues>({ className, autoComplete, type, buttonIcon, onClick, placeholder, value, onChange, onBlur, onFocus, state, legend, ...props }: ControlledInputProps<TFieldValues>) => {
    const { t } = useTranslation()
    const hasExternalState = value !== undefined || onChange !== undefined || onBlur !== undefined || onFocus !== undefined

    if (hasExternalState) {
        const resolvedState = state ?? "normal"
        return (
            <div className={baseControlledInputStyle({ state: resolvedState, className })}>
                <Input
                    autoComplete={autoComplete}
                    onClick={onClick}
                    onFocus={onFocus}
                    onBlur={onBlur}
                    onChange={onChange}
                    value={value}
                    placeholder={placeholder}
                    state={resolvedState}
                    type={type}
                    buttonIcon={buttonIcon}
                    legend={legend ?? t(String(props.name))}
                />
            </div>
        )
    }

    const { field, fieldState, formState } = useController({ ...props })
    const resolvedState = fieldState.error || formState.errors.root?.server ? "error" : "normal"

    const errorMessage = fieldState.error?.message
    let renderedError = ""
    if (errorMessage) {
        const translated = t(String(errorMessage))
        renderedError = translated === String(errorMessage) ? String(errorMessage) : translated
    }

    return (
        <div className={baseControlledInputStyle({ state: resolvedState, className })}>
            <Input autoComplete={autoComplete} onClick={onClick} {...field} state={resolvedState} type={type} buttonIcon={buttonIcon} legend={t(String(props.name))} />
            <Text color={resolvedState} className="ml-4.5 rtl:mr-4.5 select-none">{renderedError}</Text>
        </div>
    )
}


export default ControlledInput