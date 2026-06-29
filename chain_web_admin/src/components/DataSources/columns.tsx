import type { ColumnDef } from "@tanstack/react-table"
import { Power } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import DataSourceActions from "@/components/DataSources/DataSourceActions"
import type { DataSourceConfigItem } from "@/types/domain"

interface Options {
  onToggle: (id: number, enabled: boolean) => void
}

export const columns = (opts: Options): ColumnDef<DataSourceConfigItem>[] => [
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
    cell: ({ row }) => <Badge variant="outline">{row.original.source_type}</Badge>,
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
      const c = row.original
      return (
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="size-8"
            onClick={() => opts.onToggle(c.id, !c.enabled)}
            title={c.enabled ? "禁用" : "启用"}
          >
            <Power className="size-4" />
          </Button>
          <DataSourceActions config={c} />
        </div>
      )
    },
  },
]

export default columns