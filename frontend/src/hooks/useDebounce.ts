import { useEffect, useState } from 'react';

/**
 * Debounces a value by the specified delay.
 * Returns the debounced value which updates only after the delay has passed
 * since the last change to `value`.
 */
export default function useDebounce<T>(value: T, delay = 300): T {
	const [debouncedValue, setDebouncedValue] = useState<T>(value);

	useEffect(() => {
		const id = setTimeout(() => setDebouncedValue(value), delay);
		return () => {
			clearTimeout(id);
		};
	}, [value, delay]);

	return debouncedValue;
}

