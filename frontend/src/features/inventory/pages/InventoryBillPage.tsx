import { type ColumnDef, type TableFeatures } from "@tanstack/react-table"
import { Table } from "../../../components/Table"
import type { InventoryData } from "../types/inventory"
import CheckBox from "../../../components/CheckBox"




export const InventoryBillPage = () => {
  const columns: Array<ColumnDef<TableFeatures, InventoryData>> = [
    {
      header: "Name",
      accessorKey: "name",
    },
    {
      header: "SKU",
      accessorKey: "sku",
    },
    { 
      header: "Retail Price",
      accessorKey: "retail_price",
      cell: ({ getValue }) => `$${Number(getValue() ?? 0).toFixed(2)}`,
    },
    {
      header: "Whole Price",
      accessorKey: "whole_price",
      cell: ({ getValue }) => `$${Number(getValue() ?? 0).toFixed(2)}`,
    },
    {
      id: 'select-col',
      enableColumnFilter:false, 
      enableCellSelection:false,
      header: ({ table }) => (
        <CheckBox
          checked={table.getIsAllRowsSelected()}
          indeterminate={table.getIsSomeRowsSelected()}
          onClick={(e) => {table.getToggleAllRowsSelectedHandler()(e)}}
        />
      ),
      cell: ({ row }) => (
        <CheckBox
          checked={
            row.getIsSelected() ||
            (row.getCanSelectSubRows() && row.getIsAllSubRowsSelected())
          }
          //disabled={!row.getCanSelect()}
          indeterminate={row.getIsSomeSelected()}
          onClick={(e) => {row.getToggleSelectedHandler()(e)}}
        />
      ),
      
    }
  ]

  const data: InventoryData[] = [
    {
      name: "item1",
      sku: "1",
      retail_price: 12.15,
      whole_price: 10,
      image_url: ""
    },
    {
      name: "item2",
      sku: "2",
      retail_price: 14.10,
      whole_price: 11,
      image_url: ""
    },
    {
      name: "item3",
      sku: "3",
      retail_price: 8.50,
      whole_price: 6,
      image_url: ""
    },
    {
      name: "item4",
      sku: "4",
      retail_price: 20.25,
      whole_price: 16,
      image_url: ""
    }
  ]



  return (
    <div>
      <Table<InventoryData> tableKey="inventory" columns={columns} data={data} />
    </div>
  )
}
