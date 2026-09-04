import { useEffect, useState } from "react"
import DatePicker from "react-datepicker"
import "react-datepicker/dist/react-datepicker.css"
import { useController, type FieldValues, type UseControllerProps } from "react-hook-form"
import { useTranslation } from "react-i18next"
import Text from "./Text"

type DateInputProps = Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type' | 'value' | 'onChange'> & {
    value?: string
    onChange?: (value: string) => void
    legend?: string
    className?: string
}

const getThemeMode = () => (document.documentElement.classList.contains("dark") ? "dark" : "light")

// `yyyy-MM-dd` in the user's own timezone - the format every DateField in the
// API expects.
const toLocalDateString = (date: Date) => {
    const month = `${date.getMonth() + 1}`.padStart(2, "0")
    const day = `${date.getDate()}`.padStart(2, "0")
    return `${date.getFullYear()}-${month}-${day}`
}

const DateInput = ({ value, onChange, legend, className, ...rest }: DateInputProps) => {
    const [theme, setTheme] = useState<"light" | "dark">(getThemeMode)

    useEffect(() => {
        const syncTheme = () => setTheme(getThemeMode())
        syncTheme()

        const observer = new MutationObserver(syncTheme)
        observer.observe(document.documentElement, {
            attributes: true,
            attributeFilter: ["class"],
        })

        return () => observer.disconnect()
    }, [])

    const selectedDate = value && value.length >= 10 ? new Date(`${value}T00:00:00`) : null

    return (
        <fieldset className={`w-full rounded-xl border-2 border-light-border-primary hover:border-light-border-primary-hover dark:border-dark-border-primary dark:hover:border-dark-border-primary-hover transition-colors ${className ?? ""}`}>
            {legend && (
                <legend className="px-2 ml-2 rtl:mr-2 select-none">
                    <Text>{legend}</Text>
                </legend>
            )}
            <div className="relative">
                <DatePicker
                    id={rest.id}
                    name={rest.name}
                    selected={selectedDate}
                    onChange={(date: Date | null | Date[]) => {
                        const selected = Array.isArray(date) ? date[0] ?? null : date
                        // The picker hands back local midnight. `toISOString()`
                        // converts to UTC first, so east of Greenwich the saved
                        // date was the day before the one that was clicked.
                        onChange?.(selected ? toLocalDateString(selected) : "")
                    }}
                    onBlur={rest.onBlur}
                    onFocus={rest.onFocus}
                    dateFormat="yyyy-MM-dd"
                    wrapperClassName="w-full"
                    calendarClassName={theme === "dark" ? "dark-theme-datepicker" : "light-theme-datepicker"}
                    popperClassName={theme === "dark" ? "dark-theme-datepicker-popper" : "light-theme-datepicker-popper"}
                    className="w-full h-8 outline-none pb-2 px-4 bg-transparent text-light-text-primary dark:text-dark-text-primary placeholder:text-light-text-muted dark:placeholder:text-dark-text-muted"
                    placeholderText={"yyyy-dd-mm"}
                    autoComplete={rest.autoComplete}
                    disabled={rest.disabled}
                    required={rest.required}
                    readOnly={rest.readOnly}
                    aria-invalid={rest["aria-invalid"] ? "true" : "false"}
                />
            </div>
        </fieldset>
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
            <DateInput
                {...props}
                {...field}
                value={field.value ?? ""}
                onChange={(value) => field.onChange(value)}
                legend={t(String(name))}
                className={state === "error" ? "border-light-border-error dark:border-dark-border-error" : ""}
            />
            <Text color={state} className="ml-4.5 rtl:mr-4.5 select-none">{renderedError}</Text>
        </div>
    )
}

export default DateInput
