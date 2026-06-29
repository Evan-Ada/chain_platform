import type { ColumnDef } from "@tanstack/react-table"

import type { ItemPublic } from "@chain/api-client"
import ItemActionsMenu from "@/components/Items/ItemActionsMenu"
import { useCopyToClipboard } from "@/hooks/useCopyToClipboard"
import { Check, Copy } from "lucide-react"

function IdCell({ id }: { id: number }) {
  const [copiedText, copy] = useCopyToClipboard()
  const isCopied = copiedText === String(id)
  return (
    <button
      className="inline-flex items-center gap-1 font-mono text-xs text-muted-foreground hover:text-foreground"
      onClick={() => copy(String(id))}
    >
      {id}
      {isCopied ? (
        <Check className="size-3" />
      ) : (
        <Copy className="size-3 opacity-50" />
      )}
    </button>
  )
}

export const columns: ColumnDef<ItemPublic>[] = [
  {
    header: "ID",
    cell: ({ row }) => <IdCell id={row.original.id} />,
  },
  {
    header: "标题",
    cell: ({ row }) => (
      <span className="font-medium">{row.original.title}</span>
    ),
  },
  {
    header: "描述",
    cell: ({ row }) => row.original.description || "—",
  },
  {
    header: "Owner",
    cell: ({ row }) => (
      <span className="font-mono text-xs">{row.original.owner_id}</span>
    ),
  },
  {
    header: "创建时间",
    cell: ({ row }) => (
      <span className="text-xs text-muted-foreground">
        {row.original.created_at
          ? new Date(row.original.created_at).toLocaleString("zh-CN")
          : "—"}
      </span>
    ),
  },
  {
    id: "actions",
    header: "操作",
    cell: ({ row }) => <ItemActionsMenu item={row.original} />,
  },
]

export default columns