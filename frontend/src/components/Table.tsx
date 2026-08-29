import { useCreateAtom, useSelector } from "@tanstack/react-store"
import { createFilteredRowModel, stockFeatures, tableFeatures, useTable, type ColumnDef, type ColumnFiltersState, type RowData, type RowSelectionState, type TableFeatures } from "@tanstack/react-table"
import { useTanStackTableDevtools } from "@tanstack/react-table-devtools"
import { useVirtualizer } from "@tanstack/react-virtual"
import { useRef } from "react"


interface TableProps<D extends RowData> {
    // We type-cast the features slot as TableFeatures directly to satisfy the validator
    columns: ColumnDef<TableFeatures, D>[]
    data: D[]
    tableKey: string
}

const features = tableFeatures({
    filteredRowModel: createFilteredRowModel(),
    filterFns: {

    },
    ...stockFeatures,
})

export const Table = <D extends RowData>({ tableKey, columns, data }: TableProps<D>) => {
    const tableContainerRef = useRef<HTMLDivElement>(null)
    const rowGap = 10
    // rowSelection 
    const rowSelectionAtom = useCreateAtom<RowSelectionState>({})
    const rowSelection = useSelector(rowSelectionAtom)
    // colunm filtering 
    const columnFiltersAtom = useCreateAtom<ColumnFiltersState>([])
    const columnFilters = useSelector(columnFiltersAtom)

    const table = useTable({
        key: tableKey,
        features,
        columns,
        data,
        atoms: {
            rowSelection: rowSelectionAtom,
            columnFilters: columnFiltersAtom
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
                        <tr className="flex dark:drop-shadow-lg drop-shadow-lg *:py-4 dark:bg-dark-background-tertiary bg-light-background-tertiary" key={headerGroup.id}>
                            {headerGroup.headers.map((header) => (
                                <th key={header.id}
                                    className="flex-1"
                                >
                                    {header.isPlaceholder ? null : (
                                        <table.FlexRender header={header} />
                                    )}
                                </th>
                            ))}
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
                            <tr className="flex hover:dark:bg-dark-button-background-secondary-hover/20 hover:bg-dark-button-background-secondary-hover/5"
                                key={row.id}
                                style={{
                                    position: 'absolute',
                                    transform: `translateY(${virtualRow.start * rowGap / 8}px)`,
                                    width: '100%',
                                }}
                            >
                                {row.getVisibleCells().map(cell => (
                                    <td key={cell.id} className="flex-1 py-1.5 text-center"> <table.FlexRender cell={cell} /></td>
                                ))}
                            </tr>
                        )
                    })}
                </tbody>
            </table>
        </div>
    )
}


//