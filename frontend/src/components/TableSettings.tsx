import Button from './Button'
import { HugeiconsIcon } from '@hugeicons/react'
import { FilterHorizontalIcon } from '@hugeicons/core-free-icons'
import type { ColumnDef, ColumnVisibilityState, GroupingState, OnChangeFn, RowData, TableFeatures } from '@tanstack/react-table'
import Dropdown from './Dropdown'
import useOpenMenu from '../hooks/useOpenMenu'
import Text from './Text'
import SelectInput from './SelectInput'
import { useTranslation } from 'react-i18next'

interface TableSettingsProps<D extends RowData> {
    columnVisibility: ColumnVisibilityState
    setColumnVisibility: OnChangeFn<ColumnVisibilityState>
    setGrouping: OnChangeFn<GroupingState>
    columns: ColumnDef<TableFeatures, D>[]
    grouping: GroupingState

}

const TableSettings = <D extends RowData>({ columns, columnVisibility, grouping, setColumnVisibility, setGrouping }: TableSettingsProps<D>) => {
    const { isOpen, setIsOpen, ref } = useOpenMenu()
    const {t} = useTranslation()
    const toggleColumnVisibility = (columnId: string) => {
        setColumnVisibility((prev) => ({
            ...prev,
            [columnId]: !prev[columnId],
        }))
    }

    const toggleGrouping = (columnId: string) => {
        setGrouping((prev) => {
            if (!columnId) return []
            if (prev[0] === columnId) return []
            return [columnId]
        })
    }

    const toggleableColumns = columns.filter((column) => {
        if (!column.id) return false
        return column.id !== 'actions'
    })

    const groupableColumns = toggleableColumns.filter((column) => {
        // ColumnDef has optional `enableGrouping`. If it's explicitly false, column is not groupable.
        // Otherwise consider it groupable.
        // @ts-ignore - some ColumnDef variants may not include enableGrouping in typings
        return column.enableGrouping !== false
    })

    return (
        <div className='relative' ref={ref}>
            <Button onClick={() => { setIsOpen(!isOpen) }} variants="border" size="sm" iconOnly leftIcon={<HugeiconsIcon size={16} icon={FilterHorizontalIcon} />} />
            <Dropdown absolute={true} isOpen={isOpen} className="w-2xs *:first:mb-8 p-4">
                <div className='flex items-center gap-x-8 w-full'>
                    <Text>{t("tableSettings.groupBy")}</Text>
                        <SelectInput
                            value={grouping[0] ?? ''}
                            onChange={(event) => toggleGrouping(event.target.value)}
                        >
                            <option value="">{t("none")}</option>
                            {groupableColumns.map((column) => {
                                const columnId = column.id as string
                                const columnLabel = typeof column.header === 'string' ? column.header : columnId
                                return (
                                    <option key={columnId} value={columnId}>{columnLabel}</option>
                                )
                            })}
                        </SelectInput>
                </div>
                <div className='flex flex-col gap-y-4'>
                    <Text muted={true}>{t("tableSettings.displayColumns")}</Text>
                    <div className='flex flex-wrap gap-2'>
                        {toggleableColumns.map((column) => {
                            const columnId = column.id as string
                            const isVisible = columnVisibility[columnId] ?? true
                            const columnLabel = typeof column.header === 'string' ? column.header : columnId

                            return (
                                <Button
                                className='text-sm'
                                    key={columnId}
                                    type='button'
                                    rounded='full'
                                    size='md'
                                    variants='border'
                                    active={isVisible}
                                    onClick={() => toggleColumnVisibility(columnId)}
                                >
                                    {columnLabel}
                                </Button>
                            )
                        })}
                    </div>
                </div>
            </Dropdown>
        </div>
    )
}

export default TableSettings