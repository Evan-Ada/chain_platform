import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { Plus } from "lucide-react"
import * as React from "react"

import { DataTable } from "@/components/Common/DataTable"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import AddTask from "@/components/ScheduledTasks/AddTask"
import { columns as taskColumns } from "@/components/ScheduledTasks/columns"
import {
  scheduledTaskListScheduledTasks,
  scheduledTaskRunNow,
  scheduledTaskToggleScheduledTask,
} from "@chain/api-client"
import { unwrapApiData } from "@/lib/unwrap"
import type { ListEnvelope, ScheduledTaskItem } from "@/types/domain"

export const Route = createFileRoute("/_layout/scheduled-tasks")({
  component: ScheduledTasksPage,
})

function ScheduledTasksPage() {
  const queryClient = useQueryClient()
  const [addOpen, setAddOpen] = React.useState(false)
  const [pageNum] = React.useState(1)
  const pageSize = 20

  const { data, isLoading } = useQuery<ListEnvelope<ScheduledTaskItem>>({
    queryKey: ["scheduled-tasks", pageNum],
    queryFn: () =>
      unwrapApiData<ListEnvelope<ScheduledTaskItem>>(
        scheduledTaskListScheduledTasks({
          body: {
            page_num: pageNum,
            page_size: pageSize,
          },
        }),
      ),
  })

  const refresh = () =>
    queryClient.invalidateQueries({ queryKey: ["scheduled-tasks"] })

  const toggle = useMutation({
    mutationFn: ({ id, enabled }: { id: number; enabled: boolean }) =>
      unwrapApiData(
        scheduledTaskToggleScheduledTask({ body: { id, enabled } }),
      ),
    onSuccess: refresh,
  })

  const runNow = useMutation({
    mutationFn: (id: number) =>
      unwrapApiData<{ new_count: number }>(
        scheduledTaskRunNow({ body: { id } }),
      ),
  })

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">定时任务</h1>
        <Button onClick={() => setAddOpen(true)}>
          <Plus className="size-4" />
          新增任务
        </Button>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>任务列表</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="py-8 text-center text-muted-foreground">
              加载中...
            </div>
          ) : (
            <DataTable
              columns={taskColumns({
                onToggle: (id, enabled) => toggle.mutate({ id, enabled }),
                onRunNow: (id) => runNow.mutate(id),
              })}
              data={data?.res ?? []}
              emptyMessage="暂无定时任务"
            />
          )}
        </CardContent>
      </Card>
      <AddTask
        open={addOpen}
        onOpenChange={setAddOpen}
        onSuccess={refresh}
      />
    </div>
  )
}

export default ScheduledTasksPage