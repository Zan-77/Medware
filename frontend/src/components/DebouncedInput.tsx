
import { useEffect, useState } from 'react'
import useDebounce from '../hooks/useDebounce'
import Input, { type InputProps } from './Input'

type DebouncedInputProps = Omit<InputProps, 'value' | 'onChange'> & {
    value: string
    onChange: (value: string) => void
    delay?: number
}

const DebouncedInput = ({ value, onChange, delay = 300, ...props }: DebouncedInputProps) => {
    const [draftValue, setDraftValue] = useState(value)
    const debouncedValue = useDebounce(draftValue, delay)

    useEffect(() => {
        setDraftValue(value)
    }, [value])

    useEffect(() => {
        if (debouncedValue !== value) {
            onChange(debouncedValue)
        }
    }, [debouncedValue, onChange, value])

    return (
        <Input
            placeholder={props.placeholder}
            {...props}
            value={draftValue}
            onChange={(event) => setDraftValue(event.target.value)}
        />
    )
}

export default DebouncedInput