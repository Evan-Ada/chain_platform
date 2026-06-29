import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { Plus } from "lucide-react"
import * as React from "react"

import { DataTable } from "@/components/Common/DataTable"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import AddDataSource from "@/components/DataSources/AddDataSource"
import { columns as dsColumns } from "@/components/DataSources/columns"
import {
  dataSourceConfigListDataSourceConfigs,
  dataSourceConfigToggleDataSourceConfig,
} from "@chain/api-client"
import { unwrapApiData } from "@/lib/unwrap"
import type { DataSourceConfigItem, ListEnvelope } from "@/types/domain"

export const Route = createFileRoute("/_layout/data-sources")({
  component: DataSourcesPage,
})

function DataSourcesPage() {
  const queryClient = useQueryClient()
  const [addOpen, setAddOpen] = React.useState(false)

  const { data, isLoading } = useQuery<ListEnvelope<DataSourceConfigItem>>({
    queryKey: ["data-sources"],
    queryFn: () =>
      unwrapApiData<ListEnvelope<DataSourceConfigItem>>(
        dataSourceConfigListDataSourceConfigs({}),
      ),
  })

  const refresh = () =>
    queryClient.invalidateQueries({ queryKey: ["data-sources"] })

  const toggle = useMutation({
    mutationFn: ({ id, enabled }: { id: number; enabled: boolean }) =>
      unwrapApiData(
        dataSourceConfigToggleDataSourceConfig({ body: { id, enabled } }),
      ),
    onSuccess: refresh,
  })

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">数据源</h1>
        <Button onClick={() => setAddOpen(true)}>
          <Plus className="size-4" />
          新增数据源
        </Button>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>数据源列表</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="py-8 text-center text-muted-foreground">
              加载中...
            </div>
          ) : (
            <DataTable
              columns={dsColumns({
                onToggle: (id, enabled) => toggle.mutate({ id, enabled }),
              })}
              data={data?.res ?? []}
              emptyMessage="暂无数据源"
            />
          )}
        </CardContent>
      </Card>
      <AddDataSource
        open={addOpen}
        onOpenChange={setAddOpen}
        onSuccess={refresh}
      />
    </div>
  )
}

export default DataSourcesPage