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

// The two modes live in separate components on purpose: `useController` used
// to sit *after* an early return, so whether the hook ran depended on the
// props. Splitting them keeps the hook order fixed in each component.
const ExternallyControlledInput = <TFieldValues extends FieldValues>({ className, autoComplete, type, buttonIcon, onClick, placeholder, value, onChange, onBlur, onFocus, state, legend, ...props }: ControlledInputProps<TFieldValues>) => {
    const { t } = useTranslation()
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

const FormControlledInput = <TFieldValues extends FieldValues>({ className, autoComplete, type, buttonIcon, onClick, placeholder, legend, name, control, rules }: ControlledInputProps<TFieldValues>) => {
    const { t } = useTranslation()
    const { field, fieldState, formState } = useController({ name, control, rules })
    const resolvedState = fieldState.error || formState.errors.root?.server ? "error" : "normal"

    const errorMessage = fieldState.error?.message
    let renderedError = ""
    if (errorMessage) {
        const translated = t(String(errorMessage))
        renderedError = translated === String(errorMessage) ? String(errorMessage) : translated
    }

    return (
        <div className={baseControlledInputStyle({ state: resolvedState, className })}>
            <Input autoComplete={autoComplete} onClick={onClick} placeholder={placeholder} {...field} state={resolvedState} type={type} buttonIcon={buttonIcon} legend={legend ?? t(String(name))} />
            <Text color={resolvedState} className="ml-4.5 rtl:mr-4.5 select-none">{renderedError}</Text>
        </div>
    )
}

const ControlledInput = <TFieldValues extends FieldValues>(props: ControlledInputProps<TFieldValues>) => {
    const hasExternalState = props.value !== undefined || props.onChange !== undefined || props.onBlur !== undefined || props.onFocus !== undefined

    return hasExternalState
        ? <ExternallyControlledInput<TFieldValues> {...props} />
        : <FormControlledInput<TFieldValues> {...props} />
}


export default ControlledInput