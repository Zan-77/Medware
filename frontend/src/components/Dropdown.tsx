import { useEffect, useRef, useState } from "react";

interface DropdownProps {
  children: React.ReactNode
  isOpen: boolean
  absolute?: boolean
  className?:string
}

const Dropdown = ({ className,children, absolute = false, isOpen }: DropdownProps) => {
  const contentRef = useRef<HTMLDivElement | null>(null);
  const [contentHeight, setContentHeight] = useState(0);

  useEffect(() => {
    const updateHeight = () => {
      if (contentRef.current) setContentHeight(contentRef.current.scrollHeight);
    };

    updateHeight();

    // keep height in sync if content changes
    let ro: ResizeObserver | undefined;
    if (typeof ResizeObserver !== "undefined" && contentRef.current) {
      ro = new ResizeObserver(updateHeight);
      ro.observe(contentRef.current);
    }

    return () => {
      if (ro && contentRef.current) ro.disconnect();
    };
  }, [children]);

  useEffect(() => {
    // ensure we capture final height when opening
    if (isOpen && contentRef.current) setContentHeight(contentRef.current.scrollHeight);
  }, [isOpen]);

  const wrapperClass = ` ${absolute ? "border-1 dark:border-dark-border-primary border-light-border-primary  drop-shadow-2xl absolute top-full translate-y-2 right-0 z-20 min-w-fit w-full" : "py-1 pr-1"} transform transition-all duration-200 ease-out overflow-hidden rounded-lg`
  const visibleState = isOpen ? "opacity-100 translate-y-0 pointer-events-auto" : "opacity-0 -translate-y-1 pointer-events-none";

  const innerClass = `${absolute ? " p-2 dark:bg-dark-background-tertiary bg-light-background-tertiary drop-shadow-2xl" : ""} space-y-1 *:w-full ${className}`;

  return (
    <div 
      className={`${wrapperClass}  ${visibleState}`}
      style={{ maxHeight: isOpen ? `${contentHeight}px` : "0px" }}
      aria-hidden={!isOpen}
    >
      <div ref={contentRef} className={innerClass}>
        {children}
      </div>
    </div>
  )
}

export default Dropdown