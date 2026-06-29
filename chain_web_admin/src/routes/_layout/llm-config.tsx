import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { Plus } from "lucide-react"
import * as React from "react"

import { DataTable } from "@/components/Common/DataTable"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import AddLLMConfig from "@/components/LLMConfig/AddLLMConfig"
import { columns as llmColumns } from "@/components/LLMConfig/columns"
import {
  llmConfigDeleteLlmConfig,
  llmConfigListLlmConfigs,
  llmConfigSetDefaultLlmConfig,
  llmConfigTestLlmConfig,
} from "@chain/api-client"
import { unwrapApiData } from "@/lib/unwrap"
import type { ListEnvelope, LlmConfigItem } from "@/types/domain"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

export const Route = createFileRoute("/_layout/llm-config")({
  component: LlmConfigPage,
})

function LlmConfigPage() {
  const queryClient = useQueryClient()
  const [addOpen, setAddOpen] = React.useState(false)
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const { data, isLoading } = useQuery<ListEnvelope<LlmConfigItem>>({
    queryKey: ["llm-configs"],
    queryFn: () =>
      unwrapApiData<ListEnvelope<LlmConfigItem>>(
        llmConfigListLlmConfigs({}),
      ),
  })

  const refresh = () =>
    queryClient.invalidateQueries({ queryKey: ["llm-configs"] })

  const setDefault = useMutation({
    mutationFn: (id: number) =>
      unwrapApiData(llmConfigSetDefaultLlmConfig({ body: { id } })),
    onSuccess: () => {
      showSuccessToast("已设为默认")
      refresh()
    },
    onError: handleError.bind(showErrorToast),
  })

  const remove = useMutation({
    mutationFn: (id: number) =>
      unwrapApiData(llmConfigDeleteLlmConfig({ body: { id } })),
    onSuccess: () => {
      showSuccessToast("已删除")
      refresh()
    },
    onError: handleError.bind(showErrorToast),
  })

  const test = useMutation({
    mutationFn: (id: number) =>
      unwrapApiData<{ reply: string; latency_ms: number }>(
        llmConfigTestLlmConfig({ body: { id } }),
      ),
    onSuccess: (res) =>
      showSuccessToast(`测试成功: ${res.reply} (${res.latency_ms}ms)`),
    onError: handleError.bind(showErrorToast),
  })

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">LLM 配置</h1>
        <Button onClick={() => setAddOpen(true)}>
          <Plus className="size-4" />
          新增配置
        </Button>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>LLM 配置列表</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="py-8 text-center text-muted-foreground">
              加载中...
            </div>
          ) : (
            <DataTable
              columns={llmColumns({
                onSetDefault: (id) => setDefault.mutate(id),
                onDelete: (id) => remove.mutate(id),
                onTest: (id) => test.mutate(id),
                testingId: test.isPending ? test.variables : undefined,
              })}
              data={data?.res ?? []}
              emptyMessage="暂无 LLM 配置"
            />
          )}
        </CardContent>
      </Card>
      <AddLLMConfig
        open={addOpen}
        onOpenChange={setAddOpen}
        onSuccess={refresh}
      />
    </div>
  )
}

export default LlmConfigPage