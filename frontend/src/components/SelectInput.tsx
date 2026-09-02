import { useState, type SelectHTMLAttributes } from 'react'
import { tv, type VariantProps } from 'tailwind-variants'
import { HugeiconsIcon } from '@hugeicons/react'
import { ArrowDown01Icon } from '@hugeicons/core-free-icons'
import Text from './Text'

export const baseSelectStyle = tv({
  base: 'border-2 rounded-lg transition-colors min-w-40',
  variants: {
    state: {
      error: '',
      ok: '',
      normal: 'dark:border-dark-border-primary dark:hover:border-dark-border-primary-hover border-light-border-primary hover:border-light-border-primary-hover',
    },
  },
  defaultVariants: {
    state: 'normal',
  },
})

type SelectVariants = VariantProps<typeof baseSelectStyle>

interface SelectInputProps extends SelectVariants, Omit<SelectHTMLAttributes<HTMLSelectElement>, 'className'> {
  legend?: string
  className?: string
}

const SelectInput = ({ legend, className, ...rest }: SelectInputProps) => {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <fieldset className={baseSelectStyle({ ...rest, className })}>
      {legend && <legend className='px-2 ml-2 rtl:mr-2 select-none'>
        <Text color={rest.state}>{legend}</Text>
      </legend>
      }
      <div className='relative'>
        <select
          {...rest}
          onFocus={() => setIsOpen(true)}
          onBlur={() => setIsOpen(false)}
          onClick={() => setIsOpen(prev => !prev)}
          className='w-full rtl:pl-6 ltr:pr-6 h-8  outline-none bg-transparent appearance-none cursor-pointer py-1 px-4'
        >
          {rest.children}
        </select>

        <span
          aria-hidden='true'
          className='pointer-events-none absolute left-5 top-1/2 -translate-y-1/2 transition-transform duration-200 '
        >
          <HugeiconsIcon
            size={22}
            className={`transition-all ease-in ${isOpen ? 'rotate-180' : 'rotate-0'}`}
            icon={ArrowDown01Icon}
          />
        </span>
      </div>
    </fieldset>
  )
}

export default SelectInput