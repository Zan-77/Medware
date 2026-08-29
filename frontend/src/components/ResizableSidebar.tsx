const ResizableSidebar = () => {
    return (
        <div className='absolute group ltr:right-full ltr:translate-x-1 rtl:left-full rtl:-translate-x-1 top-1/2 -translate-y-1/2 w-2 h-5/6 hover:cursor-ew-resize'>
            <div className='mx-auto w-px h-full rounded-xl border-l border-r-0 border-transparent group-hover:dark:border-light-border-primary group-hover:border-dark-border-primary transition-colors' />
        </div>
    )
}

export default ResizableSidebar