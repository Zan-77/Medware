import { aggregationFn_count, aggregationFn_extent, aggregationFn_mean, aggregationFn_sum, createExpandedRowModel, createFilteredRowModel, createGroupedRowModel, createSortedRowModel, stockFeatures, tableFeatures, useTable, type ColumnDef, type ColumnFiltersState, type ColumnVisibilityState, type FilterFn, type GroupingState, type OnChangeFn, type RowData, type RowSelectionState, type SortingState, type TableFeatures } from "@tanstack/react-table"
import { useTanStackTableDevtools } from "@tanstack/react-table-devtools"
import { useVirtualizer } from "@tanstack/react-virtual"
import { useRef, type Dispatch, type SetStateAction } from "react"
import Button from "./Button"
import { HugeiconsIcon } from "@hugeicons/react"
import { ArrowDown01Icon, Sorting01Icon, Sorting02Icon, Sorting05Icon } from "@hugeicons/core-free-icons"
import Text from "./Text"
import { rankItem } from '@tanstack/match-sorter-utils'

const fuzzyFilter: FilterFn<TableFeatures, RowData> = (
    row: any,
    _columnId: string,
    value: unknown,
    addMeta: ((meta: Record<string, unknown>) => void) | undefined,
) => {
    const searchValue = String(value ?? '').trim()
    if (!searchValue) return true

    let bestRank: ReturnType<typeof rankItem> | undefined

    row.getVisibleCells().forEach((cell: any) => {
        const candidateText = String(cell.getValue() ?? '')
        const itemRank = rankItem(candidateText, searchValue)

        if (!bestRank || itemRank.rank > bestRank.rank) {
            bestRank = itemRank
        }
    })

    if (!bestRank) return false

    addMeta?.({ itemRank: bestRank })
    return bestRank.passed
}
interface TableProps<D extends RowData> {
    // We type-cast the features slot as TableFeatures directly to satisfy the validator
    columns: ColumnDef<TableFeatures, D>[]
    data: D[]
    tableKey: string
    setRowSelection?: (updater: RowSelectionState | ((old: RowSelectionState) => RowSelectionState)) => void
    setColumnFilters?: Dispatch<SetStateAction<ColumnFiltersState>>
    setColumnVisibility?: OnChangeFn<ColumnVisibilityState>
    setSorting?: OnChangeFn<SortingState>
    setGrouping?: OnChangeFn<GroupingState>
    setGlobalFilter?: OnChangeFn<string>
    rowSelection?: RowSelectionState
    columnFilters?: ColumnFiltersState
    columnVisibility?: ColumnVisibilityState
    sorting?: SortingState
    grouping?: GroupingState
    globalFilter?: string
}

const features = tableFeatures({
    filteredRowModel: createFilteredRowModel(),
    sortedRowModel: createSortedRowModel(),
    groupedRowModel: createGroupedRowModel(),
    expandedRowModel: createExpandedRowModel(),
    aggregationFns: {
        count: aggregationFn_count,
        extent: aggregationFn_extent,
        mean: aggregationFn_mean,
        sum: aggregationFn_sum,
    },
    filterFns: {
        fuzzy: fuzzyFilter,
    },
    ...stockFeatures,
})

export const Table = <D extends RowData>(
    {
        tableKey,
        columns,
        data,
        rowSelection,
        columnFilters,
        columnVisibility,
        sorting,
        grouping,
        setSorting,
        setGrouping,
        setGlobalFilter,
        setRowSelection,
        setColumnFilters,
        setColumnVisibility,
        globalFilter }: TableProps<D>
) => {
    const tableContainerRef = useRef<HTMLDivElement>(null)
    const rowGap = 10

    const table = useTable<typeof features ,D>({
        key: tableKey,
        features,
        //@ts-ignore
        columns,
        data,
        onRowSelectionChange: setRowSelection,
        onColumnFiltersChange: setColumnFilters,
        onColumnVisibilityChange: setColumnVisibility,
        onGroupingChange: setGrouping,
        onSortingChange: setSorting,
        onGlobalFilterChange: setGlobalFilter,
        //@ts-ignore    
        globalFilterFn: fuzzyFilter,
        state: {
            rowSelection,
            columnFilters,
            columnVisibility,
            sorting,
            grouping,
            globalFilter,
        },
    })
    const rows = table.getRowModel().rows
    const rowVirtualizer = useVirtualizer({
        count: rows.length,
        getScrollElement: () => tableContainerRef.current,
        estimateSize: () => 34 + rowGap,
        overscan: 5,
    })
    useTanStackTableDevtools(table)



    return (
        <div className="relative xl:h-[72vh] 2xl:h-[80vh] max-md:max-h-[72vh] overflow-auto w-full" ref={tableContainerRef}>
            <table className="w-full table-fixed border-separate border-spacing-0">
                <thead className="sticky top-0 z-10 *:border-t *:border-l *:border-r *:dark:border-dark-border-primary-hover *:border-light-background-primary *:rounded-t-2xl">
                    {table.getHeaderGroups().map((headerGroup) => (
                        <tr className="flex dark:drop-shadow-lg drop-shadow-lg *:py-4 dark:bg-dark-background-tertiary bg-light-background-tertiary *:last:rounded-tl-2xl *:first:rounded-tr-2xl" key={headerGroup.id}>
                            {headerGroup.headers.map((header) => {
                                const canSort = header.column.getCanSort()
                                const sortDirection = header.column.getIsSorted()
                                const toggleSorting = header.column.getToggleSortingHandler()
                                const isSorted = Boolean(sortDirection)

                                return (
                                    <th key={header.id}
                                        className="group flex-1 hover:cursor-pointer dark:hover:bg-dark-button-background-secondary hover:bg-light-button-background-secondary-hover"
                                    >
                                        <div className="flex justify-center items-center">
                                            {header.isPlaceholder ? null : (
                                                <table.FlexRender header={header} />
                                            )}
                                            <div className="relative w-px h-1">
                                                {canSort && (
                                                    <Button
                                                        className={`absolute top-1/2 -translate-y-1/2 right-full -translate-x-1/4 transition-opacity duration-150 ${isSorted ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none group-hover:opacity-100 group-hover:pointer-events-auto'}`}
                                                        type="button"
                                                        onClick={toggleSorting}
                                                        size="sm"
                                                        iconOnly={true}
                                                        variants='ghost'
                                                        leftIcon={<HugeiconsIcon size={22} icon={
                                                            sortDirection === 'asc'
                                                                ? Sorting02Icon
                                                                : sortDirection === 'desc'
                                                                    ? Sorting01Icon
                                                                    : Sorting05Icon
                                                        } />}
                                                    />
                                                )}
                                            </div>
                                        </div>
                                    </th>
                                )
                            })}
                        </tr>
                    ))}
                </thead>
                <tbody style={{
                    height: `${rowVirtualizer.getTotalSize()}px`,
                    position: 'relative',
                    width: "100%"
                }} >
                    {rowVirtualizer.getVirtualItems().map(virtualRow => {
                        const row = rows[virtualRow.index]

                        return (
                            <tr className={`flex transition-colors duration-200 ${row.getIsGrouped() ? "dark:bg-dark-background-tertiary/60 bg-light-background-secondary/70" : "hover:dark:bg-dark-button-background-secondary-hover/20 hover:bg-dark-button-background-secondary-hover/5"}`}
                                key={row.id}
                                style={{
                                    position: 'absolute',
                                    transform: `translateY(${virtualRow.start * rowGap / 8}px)`,
                                    width: '100%',
                                }}
                            >
                                {row.getVisibleCells().map(cell => (
                                    <td onClick={() => { cell.getIsGrouped() && row.getToggleExpandedHandler()() }} key={cell.id} className={`${cell.getIsGrouped() ? "hover:cursor-pointer dark:bg-dark-background-tertiary bg-light-background-secondary/80 w-full rounded-lg" : "flex-1"} py-1.5 text-center transition-colors duration-200`}>
                                        {cell.getIsGrouped() ? (
                                            // If it's a grouped cell, add an expander and row count
                                            <div className="px-8">
                                                <Button
                                                    variants="ghost"
                                                    rightIcon={<HugeiconsIcon className={`transition-transform duration-200 ease-out ${row.getIsExpanded() ? "rotate-0" : "rotate-180"}`} icon={ArrowDown01Icon} />}
                                                >
                                                    <div className="flex items-center gap-x-2">
                                                        <table.FlexRender cell={cell} />
                                                        <Text weight="medium">({row.subRows.length.toLocaleString()})</Text>
                                                    </div>
                                                </Button>
                                            </div>
                                        ) : cell.getIsPlaceholder() ? null : row.getIsGrouped() ? null : (
                                            <table.FlexRender cell={cell} />
                                        )}
                                    </td>
                                ))}
                            </tr>
                        )
                    })}
                </tbody>
                <tfoot className="sticky bottom-0 z-10 *:border-b *:border-l *:border-r *:dark:border-dark-border-primary-hover *:drop-shadow-2xl *:border-light-background-primary *:rounded-b-2xl">
                    {table.getFooterGroups().map((footerGroup) => (
                        <tr className="flex w-full" key={footerGroup.id}>
                            {footerGroup.headers.map((header) => (
                                <th className="flex-1" key={header.id} colSpan={header.colSpan}>
                                    {header.isPlaceholder ? null : (
                                        <table.FlexRender footer={header} />
                                    )}
                                </th>
                            ))}
                        </tr>
                    ))}
                </tfoot>
            </table>
        </div>
    )
}


//