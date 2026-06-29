import { useQuery } from "@tanstack/react-query"
import { Loader2 } from "lucide-react"

import { scheduledTaskPreviewNext } from "@chain/api-client"
import { unwrapApiData } from "@/lib/unwrap"

interface CronPreviewProps {
  cronExpr: string
  enabled?: boolean
}

export function CronPreview({ cronExpr, enabled = true }: CronPreviewProps) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["cron-preview", cronExpr],
    queryFn: () =>
      unwrapApiData<{ next_runs: string[] }>(
        scheduledTaskPreviewNext({ body: { cron_expr: cronExpr } }),
      ),
    enabled: enabled && !!cronExpr,
    staleTime: 60 * 1000,
  })

  if (!enabled || !cronExpr) {
    return <span className="text-xs text-muted-foreground">—</span>
  }
  if (isLoading) {
    return <Loader2 className="size-3 animate-spin text-muted-foreground" />
  }
  if (isError || !data?.next_runs?.length) {
    return (
      <span className="text-xs text-destructive">无效 cron 表达式</span>
    )
  }
  const next = new Date(data.next_runs[0]).toLocaleString("zh-CN")
  return (
    <span className="text-xs text-muted-foreground">下次: {next}</span>
  )
}

export default CronPreview