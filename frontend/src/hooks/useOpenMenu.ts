import { useEffect, useRef, useState } from "react";

const useOpenMenu = () => {
    const [isOpen, setIsOpen] = useState(false);
    const ref = useRef<HTMLDivElement | null>(null);

    useEffect(() => {
        const handleClickOutside = (event: PointerEvent) => {
            const target = event.target;
            if (isOpen && ref.current && target instanceof Node && !ref.current.contains(target)) {
                setIsOpen(false);
            }
        };

        document.addEventListener('pointerdown', handleClickOutside);

        return () => {
            document.removeEventListener('pointerdown', handleClickOutside);
        };
    }, [isOpen]);

    return { isOpen, ref, setIsOpen };
}

export default useOpenMenu