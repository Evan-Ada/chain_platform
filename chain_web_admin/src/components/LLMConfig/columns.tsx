import type { ColumnDef } from "@tanstack/react-table"
import { Check, Star, Trash2, Zap } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import type { LlmConfigItem } from "@/types/domain"

interface Options {
  onSetDefault: (id: number) => void
  onDelete: (id: number) => void
  onTest: (id: number) => void
  testingId?: number
}

export const columns = (opts: Options): ColumnDef<LlmConfigItem>[] => [
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
    header: "Provider",
    cell: ({ row }) => (
      <Badge variant="outline">{row.original.provider}</Badge>
    ),
  },
  {
    header: "Model",
    cell: ({ row }) => <code className="text-xs">{row.original.model}</code>,
  },
  {
    header: "API Key",
    cell: ({ row }) => (
      <code className="text-xs">{row.original.masked_api_key}</code>
    ),
  },
  {
    header: "默认",
    cell: ({ row }) =>
      row.original.is_default ? (
        <Badge>
          <Star className="size-3" />
          默认
        </Badge>
      ) : null,
  },
  {
    header: "状态",
    cell: ({ row }) => (
      <div className="flex items-center gap-2">
        <Badge variant={row.original.enabled ? "default" : "secondary"}>
          {row.original.enabled ? "启用" : "禁用"}
        </Badge>
        {row.original.last_test_status && (
          <Badge
            variant={
              row.original.last_test_status === "success"
                ? "outline"
                : "destructive"
            }
          >
            {row.original.last_test_status === "success" ? "✓" : "✗"}{" "}
            {row.original.last_test_status}
          </Badge>
        )}
      </div>
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
            disabled={opts.testingId === c.id}
            onClick={() => opts.onTest(c.id)}
            title="连通性测试"
          >
            <Zap className="size-4" />
          </Button>
          {!c.is_default && (
            <Button
              variant="ghost"
              size="icon"
              className="size-8"
              onClick={() => opts.onSetDefault(c.id)}
              title="设为默认"
            >
              <Check className="size-4" />
            </Button>
          )}
          <Button
            variant="ghost"
            size="icon"
            className="size-8 text-destructive"
            onClick={() => opts.onDelete(c.id)}
            title="删除"
          >
            <Trash2 className="size-4" />
          </Button>
        </div>
      )
    },
  },
]

export default columns