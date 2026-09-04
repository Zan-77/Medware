import { HugeiconsIcon } from '@hugeicons/react'
import Button from './Button'
import { Cancel01Icon, FilterMailIcon, Plus, Trash } from '@hugeicons/core-free-icons'
import Dropdown from './Dropdown'
import useOpenMenu from '../hooks/useOpenMenu'
import DebouncedInput from './DebouncedInput'
import SelectInput from './SelectInput'
import type { ColumnDef, ColumnFiltersState, RowData, TableFeatures } from '@tanstack/react-table'
import { useEffect } from 'react'
import { useTranslation } from 'react-i18next'

interface TableFilterProps<D extends RowData> {
    columnFilters: ColumnFiltersState
    setColumnFilters: React.Dispatch<React.SetStateAction<ColumnFiltersState>>
    columns: ColumnDef<TableFeatures, D>[]
}
//@ts-ignore
const getColumnId = <TData extends TableFeatures, TValue>(column: ColumnDef<TData, TValue>, index: number) => {
    return (column.id ?? (column as any).accessorKey ?? `col-${index}`) as string
}
//@ts-ignore
const getColumnLabel = <TData extends TableFeatures, TValue>(column: ColumnDef<TData, TValue>, index: number) => {
    const header = column.header ?? (column as any).accessorKey ?? column.id ?? `Column ${index + 1}`
    return typeof header === 'string' ? header : String(header) || `Column ${index + 1}`
}

const isRangeFilterColumn = <D extends RowData>(column: ColumnDef<TableFeatures, D> | undefined) => {
    return (column as any)?.meta?.filterVariants === 'range'
}

const getDefaultFilterValue = <D extends RowData>(column: ColumnDef<TableFeatures, D> | undefined) => {
    return isRangeFilterColumn(column) ? ['', ''] : ''
}

const TableFilter = <D extends RowData>({ columns, columnFilters, setColumnFilters }: TableFilterProps<D>) => {
    const { t } = useTranslation()
    const { isOpen, ref, setIsOpen } = useOpenMenu()
    const filterableColumns = columns.filter((column) => (column as any).enableColumnFilter !== false)

    useEffect(() => {
        if (!isOpen || columnFilters.length > 0 || filterableColumns.length === 0) return

        const firstColumnId = getColumnId(filterableColumns[0], 0)
        setColumnFilters([{ id: firstColumnId, value: getDefaultFilterValue(filterableColumns[0]) }])
    }, [isOpen, columnFilters.length, filterableColumns, setColumnFilters])

    const getAvailableColumns = (currentId: string, currentIndex: number) => {
        const usedIds = new Set(
            columnFilters
                .map((filter, index) => (index === currentIndex ? null : filter.id))
                .filter((id): id is string => typeof id === 'string'),
        )

        return filterableColumns.filter((column, index) => {
            const columnId = getColumnId(column, index)
            return columnId === currentId || !usedIds.has(columnId)
        })
    }

    const addFilterRow = () => {
        if (columnFilters.length >= filterableColumns.length) return

        const usedIds = new Set(columnFilters.map((filter) => filter.id))
        const nextColumn = filterableColumns.find((column, index) => !usedIds.has(getColumnId(column, index)))

        if (!nextColumn) return

        const nextColumnId = getColumnId(nextColumn, filterableColumns.indexOf(nextColumn))
        // A range column needs its `{ min, max }` shape here; an empty string
        // matched nothing and blanked the whole table on "add filter".
        setColumnFilters((prev) => [...prev, { id: nextColumnId, value: getDefaultFilterValue(nextColumn) }])
    }

    const updateFilterColumn = (index: number, nextColumnId: string) => {
        setColumnFilters((prev) =>
            prev.map((filter, filterIndex) => {
                if (filterIndex !== index) return filter

                const nextColumn = filterableColumns.find((column, columnIndex) => getColumnId(column, columnIndex) === nextColumnId)
                return { ...filter, id: nextColumnId, value: getDefaultFilterValue(nextColumn) }
            }),
        )
    }

    const updateFilterValue = (index: number, value: string) => {
        setColumnFilters((prev) =>
            prev.map((filter, filterIndex) =>
                filterIndex === index ? { ...filter, value } : filter,
            ),
        )
    }

    const updateRangeFilterValue = (index: number, bound: 'min' | 'max', value: string) => {
        setColumnFilters((prev) =>
            prev.map((filter, filterIndex) => {
                if (filterIndex !== index) return filter

                const currentRange = Array.isArray(filter.value) ? filter.value : ['', '']
                const nextRange = [...currentRange]
                nextRange[bound === 'min' ? 0 : 1] = value
                return { ...filter, value: nextRange }
            }),
        )
    }

    const removeFilterRow = (index: number) => {
        setColumnFilters((prev) => prev.filter((_, filterIndex) => filterIndex !== index))
    }

    const removeAllFilters = () => {
        setColumnFilters([])
    }

    return (
        <div className='relative' ref={ref}>
            <Button onClick={() => { setIsOpen(!isOpen) }} size='sm' variants='border' iconOnly leftIcon={<HugeiconsIcon size={20} icon={FilterMailIcon} />} />
            <Dropdown absolute={true} isOpen={isOpen}>
                <div className='flex flex-col gap-2 p-3'>
                    {columnFilters.map((filter, index) => {
                        const availableColumns = getAvailableColumns(String(filter.id), index)
                        const currentColumn = filterableColumns.find((column, columnIndex) => getColumnId(column, columnIndex) === filter.id)
                        const isRangeFilter = isRangeFilterColumn(currentColumn)
                        const rangeValue = Array.isArray(filter.value) ? filter.value : ['', '']

                        return (
                            <div key={`${filter.id}-${index}`} className='flex items-center space-x-10'>

                                <SelectInput
                                    legend={t('tableFilter.column')}
                                    value={String(filter.id)}
                                    onChange={(event) => updateFilterColumn(index, event.target.value)}
                                >
                                    {availableColumns.length > 0 ? (
                                        availableColumns.map((column, columnIndex) => (
                                            <option key={getColumnId(column, columnIndex)} value={getColumnId(column, columnIndex)}>
                                                {getColumnLabel(column, columnIndex)}
                                            </option>
                                        ))
                                    ) : currentColumn ? (
                                        <option value={String(filter.id)}>
                                            {getColumnLabel(currentColumn, filterableColumns.indexOf(currentColumn))}
                                        </option>
                                    ) : null}
                                </SelectInput>

                                {isRangeFilter ? (
                                    <>
                                        <DebouncedInput
                                            legend={t('tableFilter.min')}
                                            value={typeof rangeValue[0] === 'string' ? rangeValue[0] : String(rangeValue[0] ?? '')}
                                            onChange={(nextValue) => updateRangeFilterValue(index, 'min', nextValue)}
                                        />
                                        <DebouncedInput
                                            legend={t('tableFilter.max')}
                                            value={typeof rangeValue[1] === 'string' ? rangeValue[1] : String(rangeValue[1] ?? '')}
                                            onChange={(nextValue) => updateRangeFilterValue(index, 'max', nextValue)}
                                        />
                                    </>
                                ) : (
                                    <DebouncedInput
                                        legend={t('tableFilter.value')}
                                        type='text'
                                        value={typeof filter.value === 'string' ? filter.value : ''}
                                        onChange={(nextValue) => updateFilterValue(index, nextValue)}
                                    />
                                )}
                                
                                    <Button className={index > 0 ?"visible":"invisible"} type='button' iconOnly={true} variants='ghost' size='sm' onClick={() => removeFilterRow(index)}>
                                        <HugeiconsIcon icon={Cancel01Icon} />
                                    </Button>
                            </div>
                        )
                    })}

                    <div className='mt-2 flex items-center justify-between gap-2'>
                        {
                            columnFilters.length < filterableColumns.length &&
                            <Button
                                type='button'
                                variants='ghost'
                                size='sm'
                                onClick={addFilterRow}
                                rightIcon={<HugeiconsIcon size={22} icon={Plus} />}
                            >
                                {t('tableFilter.addFilter')}
                            </Button>
                        }

                        <Button type='button' variants='ghost' size='sm' onClick={removeAllFilters} rightIcon={<HugeiconsIcon size={20} icon={Trash} />}>
                            {t('tableFilter.removeAll')}
                        </Button>
                    </div>
                </div>
            </Dropdown>
        </div>
    )
}

export default TableFilter
