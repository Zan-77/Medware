import { tv ,type VariantProps} from "tailwind-variants/lite";


const baseTextStyle= tv({
    base:"mx-px",
    variants:{
        color:{
            error:"hover:text-light-text-error-hover text-error dark:hover:text-dark-text-error-hover",
            ok:"text-ok",
            alert:"text-alert",
            normal:"dark:text-dark-text text-light-text"
        },
        size:{
            "12":"text-xs h-4",
            "14":"text-sm h-4.5",
            "16":"text-base h-5",
            "18":"text-lg h-5.5",
            "20":"text-xl h-6",
            "24":"text-2xl h-6.5",
        },
        weight:{
            black:"font-black",
            extrabold:"font-extrabold",
            bold:"font-bold",
            semibold:"font-semibold",
            medium:"font-medium",
            normal:"font-normal",
            light:"font-light",
            extralight:"font-extralight",
        },
        muted:{
            true:"dark:text-dark-text-muted text-light-text-muted",
            false:""
        }
    },
    defaultVariants:{
        color:"normal",
        size:"16",
        weight:"normal",
        muted:false,
    }
})      

type TextVariants = VariantProps<typeof baseTextStyle>;

interface TextProps extends TextVariants {
    children:React.ReactNode
    className?:string
} 

const Text = ({children,className, ...variants}:TextProps) => {
  return (
    <span className={baseTextStyle({ ...variants, className })}>{children}</span>
  )
}

export default Text