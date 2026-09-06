import { useEffect, useMemo, useState } from "react"
import { Controller, type Control, type FieldValues, type Path, type RegisterOptions } from "react-hook-form"
import useDebounce from "../hooks/useDebounce"
import Button from "./Button"
import ControlledInput from "./ControlledInput"
import Dropdown from "./Dropdown"

export type SearchSelectOption = {
    value: string
    label: string
}

type SearchSelectInputProps = {
    legend?: string
    value?: string
    onChange?: (value: string) => void
    options: SearchSelectOption[]
    placeholder?: string
    className?: string
    state?: "normal" | "error" | "ok"
    onBlur?: () => void
}

const SearchSelectInput = ({
    legend,
    value = "",
    onChange,
    options,
    placeholder = "Search...",
    className = "",
    state = "normal",
    onBlur,
}: SearchSelectInputProps) => {
    const [isOpen, setIsOpen] = useState(false)
    const [search, setSearch] = useState(() => {
        const selected = options.find((option) => option.value === value)
        return selected ? selected.label : ""
    })
    const debouncedSearch = useDebounce(search, 300)

    // Callers build `options` inline, so the array is a new reference on every
    // parent render. Keying this effect on the array identity re-ran it - and
    // wiped whatever the user had typed - each time the parent re-rendered.
    // The signature only changes when the option *contents* change.
    const optionsSignature = options.map((option) => `${option.value}:${option.label}`).join("|")
    useEffect(() => {
        const selected = options.find((option) => option.value === value)
        setSearch(selected ? selected.label : "")
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [optionsSignature, value])

    const filteredOptions = useMemo(() => {
        const term = debouncedSearch.trim().toLowerCase()
        if (!term) return options

        return options.filter((option) => {
            return option.label.toLowerCase().includes(term) || option.value.toLowerCase().includes(term)
        })
    }, [debouncedSearch, options])

    const handleSelect = (option: SearchSelectOption) => {
        setSearch(option.label)
        onChange?.(option.value)
        setIsOpen(false)
    }

    return (
        <div className={`relative w-full h-fit ${className}`}>
            <ControlledInput
                name={"search" as any}
                control={undefined as any}
                value={search}
                onChange={(e) => {
                    setSearch(e.target.value)
                    setIsOpen(true)
                    onChange?.("")
                }}
                onBlur={() => {
                    onBlur?.()
                    window.setTimeout(() => setIsOpen(false), 120)
                }}
                onFocus={() => setIsOpen(true)}
                placeholder={placeholder}
                type="text"
                state={state}
                legend={legend}
            />

            {isOpen && filteredOptions.length > 0 && (
                <Dropdown isOpen={isOpen} absolute={true}>
                    {filteredOptions.map((option) => (
                        <Button
                            key={option.value}
                            type="button"
                            variants="ghost"
                            onMouseDown={(event) => {
                                event.preventDefault()
                                handleSelect(option)
                            }}
                        >
                            {option.label}
                        </Button>
                    ))}
                </Dropdown>
            )}
        </div>
    )
}

type ControlledSearchSelectInputProps<TFieldValues extends FieldValues> = {
    control: Control<TFieldValues>
    name: Path<TFieldValues>
    options: SearchSelectOption[]
    label?: string
    rules?: RegisterOptions<TFieldValues, Path<TFieldValues>>
    placeholder?: string
    className?: string
}

export const ControlledSearchSelectInput = <TFieldValues extends FieldValues>({
    control,
    name,
    options,
    label,
    rules,
    placeholder,
    className,
}: ControlledSearchSelectInputProps<TFieldValues>) => (
    <Controller
        name={name}
        control={control}
        rules={rules}
        render={({ field, fieldState }) => (
            <SearchSelectInput
                legend={label}
                value={String(field.value ?? "")}
                options={options}
                placeholder={placeholder}
                state={fieldState.invalid ? "error" : "normal"}
                className={className}
                onBlur={field.onBlur}
                onChange={(value) => field.onChange(value)}
            />
        )}
    />
)

export default SearchSelectInput
