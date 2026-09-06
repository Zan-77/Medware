import { useController, type FieldValues, type UseControllerProps } from "react-hook-form"
import { useTranslation } from "react-i18next"
import Text from "./Text"
import TextArea from "./TextArea"

type ControlledTextAreaProps<TFieldValues extends FieldValues> = UseControllerProps<TFieldValues> & {
    className?: string
    name: UseControllerProps<TFieldValues>["name"]
    control: NonNullable<UseControllerProps<TFieldValues>["control"]>
    placeholder?: string
    rows?: number
    onFocus?: React.FocusEventHandler<HTMLTextAreaElement>
    onBlur?: React.FocusEventHandler<HTMLTextAreaElement>
    onChange?: React.ChangeEventHandler<HTMLTextAreaElement>
    value?: string
    autoResize?: boolean
}

const ControlledTextArea = <TFieldValues extends FieldValues>({
    className,
    placeholder,
    rows,
    onFocus,
    onBlur,
    onChange,
    value,
    autoResize = true,
    ...props
}: ControlledTextAreaProps<TFieldValues>) => {
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
        <div className={className}>
            <TextArea
                {...field}
                fieldset={false}
                value={value ?? field.value}
                onChange={onChange ?? field.onChange}
                onBlur={onBlur ?? field.onBlur}
                onFocus={onFocus}
                placeholder={placeholder}
                rows={rows}
                legend={t(String(props.name).split(".").pop() ?? String(props.name))}
                state={state}
                autoResize={autoResize}
            />
            <Text color={state} className="ml-4.5 rtl:mr-4.5 select-none">{renderedError}</Text>
        </div>
    )
}

export default ControlledTextArea
