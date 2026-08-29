import Button from './Button'
import { HugeiconsIcon } from '@hugeicons/react'
import { CheckIcon, MinusSignIcon } from '@hugeicons/core-free-icons'

interface CheckBoxProps {
    checked: boolean
    indeterminate: boolean
    onClick: React.MouseEventHandler<HTMLButtonElement>
}

const CheckBox = ({ checked, indeterminate, onClick }: CheckBoxProps) => {

    return (
        <Button onClick={(e: React.MouseEvent<HTMLButtonElement>) => onClick(e)} size='xs' variants='border' className='border-2 rounded-lg' iconOnly={true}>
            {indeterminate && !checked ? (
                <HugeiconsIcon size={20} icon={MinusSignIcon} />
            ) : checked ? (
                <HugeiconsIcon size={20} icon={CheckIcon} />
            ) : null}
        </Button>
    )
}

export default CheckBox