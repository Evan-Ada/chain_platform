import type { ColumnDef } from "@tanstack/react-table"
import { Play, Power } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import CronPreview from "@/components/Common/CronPreview"
import TaskActions from "@/components/ScheduledTasks/TaskActions"
import type { ScheduledTaskItem } from "@/types/domain"

interface Options {
  onToggle: (id: number, enabled: boolean) => void
  onRunNow: (id: number) => void
}

export const columns = (opts: Options): ColumnDef<ScheduledTaskItem>[] => [
  {
    header: "ID",
    cell: ({ row }) => (
      <span className="font-mono text-xs">{row.original.id}</span>
    ),
  },
  {
    header: "名称",
    cell: ({ row }) => (
      <span className="font-medium">{row.original.name}</span>
    ),
  },
  {
    header: "类型",
    cell: ({ row }) => <Badge variant="outline">{row.original.biz_type}</Badge>,
  },
  {
    header: "Cron",
    cell: ({ row }) => (
      <code className="text-xs">{row.original.cron_expr}</code>
    ),
  },
  {
    header: "下次执行",
    cell: ({ row }) => <CronPreview cronExpr={row.original.cron_expr} />,
  },
  {
    header: "状态",
    cell: ({ row }) => (
      <Badge variant={row.original.enabled ? "default" : "secondary"}>
        {row.original.enabled ? "启用" : "禁用"}
      </Badge>
    ),
  },
  {
    id: "actions",
    header: "操作",
    cell: ({ row }) => {
      const t = row.original
      return (
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="size-8"
            onClick={() => opts.onToggle(t.id, !t.enabled)}
            title={t.enabled ? "禁用" : "启用"}
          >
            <Power className="size-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="size-8"
            onClick={() => opts.onRunNow(t.id)}
            title="立即执行"
          >
            <Play className="size-4" />
          </Button>
          <TaskActions task={t} />
        </div>
      )
    },
  },
]

export default columns