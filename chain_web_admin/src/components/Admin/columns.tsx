import type { ColumnDef } from "@tanstack/react-table"

import type { UserPublic } from "@chain/api-client"
import { Badge } from "@/components/ui/badge"
import UserActionsMenu from "@/components/Admin/UserActionsMenu"

export const columns = (currentUserId: number): ColumnDef<UserPublic>[] => [
  {
    header: "ID",
    accessorKey: "id",
    cell: ({ row }) => (
      <span className="font-mono text-xs text-muted-foreground">
        {row.original.id}
      </span>
    ),
  },
  {
    header: "用户名",
    cell: ({ row }) => (
      <span className="font-medium">{row.original.username}</span>
    ),
  },
  {
    header: "姓名",
    accessorKey: "full_name",
  },
  {
    header: "邮箱",
    cell: ({ row }) => row.original.email || "—",
  },
  {
    header: "角色",
    cell: ({ row }) => (
      <Badge variant={row.original.is_superuser ? "default" : "secondary"}>
        {row.original.is_superuser ? "管理员" : "用户"}
      </Badge>
    ),
  },
  {
    header: "状态",
    cell: ({ row }) => (
      <Badge variant={row.original.is_active ? "outline" : "destructive"}>
        {row.original.is_active ? "正常" : "禁用"}
      </Badge>
    ),
  },
  {
    header: "操作",
    id: "actions",
    cell: ({ row }) => (
      <UserActionsMenu user={row.original} currentUserId={currentUserId} />
    ),
  },
]

// 提供一种"无 currentUserId"占位列(默认管理员看到自己的 id=1,实际由路由传)
export const defaultColumns: ColumnDef<UserPublic>[] = columns(1)