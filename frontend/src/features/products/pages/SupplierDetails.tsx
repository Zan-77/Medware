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
  const { supplierId } = useParams<{ supplierId: string }>()
  const { data } = useQuery(
    {
      // The supplier id belongs in the key: without it every supplier shared
      // one cache entry. The queryFn also had a braced body with no `return`,
      // so it resolved `undefined` and the table was always empty.
      queryKey: ["ProductSuppliers", supplierId],
      queryFn: () => getProductSuppliersById(String(supplierId)),
      enabled: Boolean(supplierId),
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
      id: "product",
      enableSorting: true,
      header: t("Products"),
      // All three columns used to read `accessorKey: "id"` under the headers
      // id/id/id, so the table showed the same value three times.
      accessorFn: (row) => row.product_name ?? String(row.product ?? ""),
      cell: ({ row }) => row.original.product_name ?? String(row.original.product ?? ""),
    },
    {
      meta: {
        filterVariants: "range"
      },
      id: "discount",
      enableSorting: true,
      header: t("discount"),
      accessorKey: "discount",
    },
  ]
  return (
    <div>
      {data && data.length > 0
        ? <Table<ProductSuppliers> tableKey='Productsupplier' sorting={sorting}
          setSorting={setSorting} columns={columns} data={data} />
        : <Text>no items</Text>}
    </div>
  )
}
