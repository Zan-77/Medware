import Text from "./Text"

type FormProps = {
    onSubmit?: () => void
    children: React.ReactNode
    className?: string
    ServerError?: Partial<{ message: String, type: string | number } | undefined>
    Buttons?: React.ReactNode
}
const Form = ({
    children,
    className,
    ServerError,
    Buttons,
    onSubmit,
}: FormProps) => {
    return (
        <form className={className} onSubmit={onSubmit}>
            {children}
            {ServerError && <Text color={ServerError ? "error" : "normal"}>{ServerError?.message}</Text>}
            {Buttons}
        </form>
    )
}

export default Form