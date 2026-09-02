import { useQuery } from '@tanstack/react-query'
import { Table } from '../../../components/Table'
import type { ProductSuppliers } from '../types/products'
import { useTranslation } from 'react-i18next'
import type { ColumnDef, SortingState, TableFeatures } from '@tanstack/react-table'
import { getProductSuppliersById } from '../services/products.service'
import Text from '../../../components/Text'
import { useState } from 'react'
import { useParams } from 'react-router'

export const SupplierDetails = () => {
  const [sorting, setSorting] = useState<SortingState>([])
  const { t } = useTranslation()
  const params = useParams()
  const { data } = useQuery(
    {
      queryKey: ["ProductSuppliers"],
      queryFn: () => { params.supplierId && getProductSuppliersById(params.supplierId) }
    }
  )
  const columns: Array<ColumnDef<TableFeatures, ProductSuppliers>> = [
    {
      meta: {
        filterVariants: "value"
      },
      id: "id",
      enableSorting: true,
      header: t("id"),
      accessorKey: "id",
    },
    {
      meta: {
        filterVariants: "value"
      },
      id: "sid",
      enableSorting: true,
      header: t("id"),
      accessorKey: "id",
    },
    {
      meta: {
        filterVariants: "range"
      },
      id: "pid",
      enableSorting: true,
      header: t("id"),
      accessorKey: "id",

    },
  ]
  return (
    <div>
   <Table<ProductSuppliers> tableKey='Productsupplier' sorting={sorting}
        setSorting={setSorting} columns={columns} data={data ?? []} />

   <Table<ProductSuppliers> tableKey='Productsupplier' sorting={sorting}
        setSorting={setSorting} columns={columns} data={data ?? []} />
    </div>
  )
}
