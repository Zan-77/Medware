import Input from "./Input"
import { useController, type FieldValues, type UseControllerProps } from "react-hook-form"
import { useTranslation } from "react-i18next"
import Text from "./Text"

type DateInputProps = Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type'> & {
    value?: string
    onChange?: (value: string) => void
    legend?: string
}

const DateInput = ({ value, onChange, legend, ...rest }: DateInputProps) => {
    return (
        <Input
            {...rest}
            type="date"
            value={value}
            onChange={(e) => onChange && onChange(e.target.value)}
            legend={legend}
        />
    )
}

type ControlledDateInputProps<TFieldValues extends FieldValues> = UseControllerProps<TFieldValues> & {
    className?: string
}

export const ControlledDateInput = <TFieldValues extends FieldValues>({ name, control, ...props }: ControlledDateInputProps<TFieldValues>) => {
    const { t } = useTranslation()
    const { field, fieldState, formState } = useController({ name, control })
    const state = fieldState.error || formState.errors.root?.server ? "error" : "normal"
    const errorMessage = fieldState.error?.message
    let renderedError = ""
    if (errorMessage) {
        const translated = t(String(errorMessage))
        renderedError = translated === String(errorMessage) ? String(errorMessage) : translated
    }

    return (
        <div>
            <Input {...props} {...field} type="date" legend={t(String(name))} state={state} />
            <Text color={state} className="ml-4.5 rtl:mr-4.5 select-none">{renderedError}</Text>
        </div>
    )
}

export default DateInput
