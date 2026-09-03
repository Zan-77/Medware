import { useEffect, useRef } from "react"
import { tv, type VariantProps } from "tailwind-variants"
import Text from "./Text"

export const baseTextAreaStyle = tv({
    base: "border-2 transition-colors min-w-40 w-full",
    variants: {
        state: {
            error: "",
            ok: "",
            normal: "dark:border-dark-border-primary dark:hover:border-dark-border-primary-hover border-light-border-primary hover:border-light-border-primary-hover",
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
    },
    defaultVariants: {
        state: "normal",
        rounded: "lg",
    },
})

type TextAreaVariants = VariantProps<typeof baseTextAreaStyle>

export interface TextAreaProps extends TextAreaVariants, Omit<React.TextareaHTMLAttributes<HTMLTextAreaElement>, "className"> {
    legend?: string
    className?: string
    fieldset?: boolean
    autoResize?: boolean
}

const TextArea = ({ legend, className, fieldset = true, autoResize = true, ...rest }: TextAreaProps) => {
    const textareaRef = useRef<HTMLTextAreaElement | null>(null)

    useEffect(() => {
        if (!autoResize || !textareaRef.current) return

        textareaRef.current.style.height = "auto"
        textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
    }, [rest.value, autoResize])

    return (
        fieldset ? (
            <fieldset className={baseTextAreaStyle({ ...rest, className })}>
                <legend className="px-2 ml-2 rtl:mr-2 select-none">
                    <Text color={rest.state}>{legend}</Text>
                </legend>
                <textarea
                    autoComplete="off"
                    {...rest}
                    ref={textareaRef}
                    className="w-full rtl:pl-6 ltr:pr-6 min-h-20 outline-none pb-2 px-4 py-2 bg-transparent resize-none overflow-hidden rap-break-word whitespace-pre-wrap"
                    onInput={(event) => {
                        if (!autoResize) return
                        const target = event.currentTarget
                        target.style.height = "auto"
                        target.style.height = `${target.scrollHeight}px`
                    }}
                />
            </fieldset>
        ) : (
            <div className={baseTextAreaStyle({ ...rest, className })}>
                <textarea
                    {...rest}
                    autoComplete="off"
                    ref={textareaRef}
                    className="w-full rtl:pl-6 ltr:pr-6 min-h-20 outline-none py-2 px-4 bg-transparent resize-none overflow-hidden rap-break-word whitespace-pre-wrap"
                    onInput={(event) => {
                        if (!autoResize) return
                        const target = event.currentTarget
                        target.style.height = "auto"
                        target.style.height = `${target.scrollHeight}px`
                    }}
                />
            </div>
        )
    )
}

export default TextArea
