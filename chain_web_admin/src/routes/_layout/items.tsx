import { useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { Plus } from "lucide-react"
import * as React from "react"

import { DataTable } from "@/components/Common/DataTable"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Pagination } from "@/components/ui/pagination"
import AddItem from "@/components/Items/AddItem"
import { columns as itemColumns } from "@/components/Items/columns"
import type { ItemsPublic } from "@chain/api-client"
import { itemsReadItems } from "@chain/api-client"
import { unwrapResult } from "@/lib/unwrap"

export const Route = createFileRoute("/_layout/items")({
  component: ItemsPage,
})

function ItemsPage() {
  const queryClient = useQueryClient()
  const [pageNum, setPageNum] = React.useState(1)
  const [addOpen, setAddOpen] = React.useState(false)
  const pageSize = 20

  const { data, isLoading } = useQuery<ItemsPublic>({
    queryKey: ["items", pageNum],
    queryFn: () =>
      unwrapResult(
        itemsReadItems({
          query: { skip: (pageNum - 1) * pageSize, limit: pageSize },
        }),
      ),
  })

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Items</h1>
        <Button onClick={() => setAddOpen(true)}>
          <Plus className="size-4" />
          新增
        </Button>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Items 列表</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="py-8 text-center text-muted-foreground">
              加载中...
            </div>
          ) : (
            <DataTable
              columns={itemColumns}
              data={data?.data ?? []}
              emptyMessage="暂无 Item"
            />
          )}
          <Pagination
            pageNum={pageNum}
            pageSize={pageSize}
            total={data?.count ?? 0}
            onPageChange={setPageNum}
          />
        </CardContent>
      </Card>
      <AddItem
        open={addOpen}
        onOpenChange={setAddOpen}
        onSuccess={() =>
          queryClient.invalidateQueries({ queryKey: ["items"] })
        }
      />
    </div>
  )
}

export default ItemsPage