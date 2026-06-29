import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { Plus } from "lucide-react"
import * as React from "react"

import { DataTable } from "@/components/Common/DataTable"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Pagination } from "@/components/ui/pagination"
import AddSubscription from "@/components/Subscriptions/AddSubscription"
import { columns as subColumns } from "@/components/Subscriptions/columns"
import {
  subscriptionListSubscriptions,
  subscriptionRunNow,
  subscriptionToggleSubscription,
} from "@chain/api-client"
import { unwrapApiData } from "@/lib/unwrap"
import type { ListEnvelope, SubscriptionItem } from "@/types/domain"

export const Route = createFileRoute("/_layout/subscriptions")({
  component: SubscriptionsPage,
})

function SubscriptionsPage() {
  const queryClient = useQueryClient()
  const [pageNum, setPageNum] = React.useState(1)
  const [addOpen, setAddOpen] = React.useState(false)
  const pageSize = 20

  const { data, isLoading } = useQuery<ListEnvelope<SubscriptionItem>>({
    queryKey: ["subscriptions"],
    queryFn: () =>
      unwrapApiData<ListEnvelope<SubscriptionItem>>(
        subscriptionListSubscriptions({}),
      ),
  })

  const refresh = () =>
    queryClient.invalidateQueries({ queryKey: ["subscriptions"] })

  const toggle = useMutation({
    mutationFn: ({ id, enabled }: { id: number; enabled: boolean }) =>
      unwrapApiData(subscriptionToggleSubscription({ body: { id, enabled } })),
    onSuccess: refresh,
  })

  const runNow = useMutation({
    mutationFn: (id: number) =>
      unwrapApiData<{ new_count: number }>(
        subscriptionRunNow({ body: { id } }),
      ),
  })

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">订阅管理</h1>
        <Button onClick={() => setAddOpen(true)}>
          <Plus className="size-4" />
          新增订阅
        </Button>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>订阅列表</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="py-8 text-center text-muted-foreground">
              加载中...
            </div>
          ) : (
            <DataTable
              columns={subColumns({
                onToggle: (id, enabled) => toggle.mutate({ id, enabled }),
                onRunNow: (id) => runNow.mutate(id),
                togglingId: toggle.isPending ? toggle.variables?.id : undefined,
              })}
              data={data?.res ?? []}
              emptyMessage="暂无订阅"
            />
          )}
          <Pagination
            pageNum={pageNum}
            pageSize={pageSize}
            total={data?.total ?? 0}
            onPageChange={setPageNum}
          />
        </CardContent>
      </Card>
      <AddSubscription
        open={addOpen}
        onOpenChange={setAddOpen}
        onSuccess={refresh}
      />
    </div>
  )
}

export default SubscriptionsPage