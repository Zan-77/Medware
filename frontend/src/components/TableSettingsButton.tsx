import type { ColumnDef, RowData, TableFeatures } from "@tanstack/react-table"
import Button from "./Button"
import { HugeiconsIcon } from "@hugeicons/react"
import { FilterMailIcon } from "@hugeicons/core-free-icons"
import Dropdown from "./Dropdown"
import useOpenMenu from "../hooks/useOpenMenu"

interface TableSettingsButtonProps<D extends RowData> {
    columns: ColumnDef<TableFeatures, D>[]
}

const TableSettingsButton = <D extends RowData>({ columns }: TableSettingsButtonProps<D>) => {
    const { isOpen, setIsOpen, ref } = useOpenMenu()
    return (
        <div className="relative" ref={ref}>
            <Button onClick={() => { setIsOpen(!isOpen) }} variants="border" size="sm" iconOnly leftIcon={<HugeiconsIcon size={16} icon={FilterMailIcon} />} />
            <Dropdown absolute={true} isOpen={isOpen}>
                <Button>asdasda</Button>
            </Dropdown>
        </div>
    )
}

export default TableSettingsButton