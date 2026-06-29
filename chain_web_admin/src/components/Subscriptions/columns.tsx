import type { ColumnDef } from "@tanstack/react-table"
import { Play, Power } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import SubscriptionActions from "@/components/Subscriptions/SubscriptionActions"
import type { SubscriptionItem } from "@/types/domain"

interface Options {
  onToggle: (id: number, enabled: boolean) => void
  onRunNow: (id: number) => void
  togglingId?: number
}

export const columns = (opts: Options): ColumnDef<SubscriptionItem>[] => [
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
    header: "关键词",
    cell: ({ row }) =>
      row.original.keywords?.length ? (
        <div className="flex flex-wrap gap-1">
          {row.original.keywords.map((k: string) => (
            <Badge key={k} variant="secondary">
              {k}
            </Badge>
          ))}
        </div>
      ) : (
        <span className="text-xs text-muted-foreground">—</span>
      ),
  },
  {
    header: "调度",
    cell: ({ row }) => (
      <code className="text-xs">{row.original.schedule_cron}</code>
    ),
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
      const s = row.original
      return (
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="size-8"
            title={s.enabled ? "禁用" : "启用"}
            disabled={opts.togglingId === s.id}
            onClick={() => opts.onToggle(s.id, !s.enabled)}
          >
            <Power className="size-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="size-8"
            title="立即抓取"
            onClick={() => opts.onRunNow(s.id)}
          >
            <Play className="size-4" />
          </Button>
          <SubscriptionActions subscription={s} />
        </div>
      )
    },
  },
]

export default columns