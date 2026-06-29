import { useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { Plus } from "lucide-react"
import * as React from "react"

import { DataTable } from "@/components/Common/DataTable"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Pagination } from "@/components/ui/pagination"
import AddUser from "@/components/Admin/AddUser"
import { columns } from "@/components/Admin/columns"
import type { UsersPublic } from "@chain/api-client"
import { usersReadUsers } from "@chain/api-client"
import { unwrapResult } from "@/lib/unwrap"
import useAuth from "@/hooks/useAuth"

export const Route = createFileRoute("/_layout/admin")({
  component: AdminPage,
})

function AdminPage() {
  const { user: currentUser } = useAuth()
  const [pageNum, setPageNum] = React.useState(1)
  const [addOpen, setAddOpen] = React.useState(false)
  const pageSize = 20

  const { data, isLoading } = useQuery<UsersPublic>({
    queryKey: ["users", pageNum],
    queryFn: () =>
      unwrapResult(
        usersReadUsers({
          query: { skip: (pageNum - 1) * pageSize, limit: pageSize },
        }),
      ),
  })

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">用户管理</h1>
        <Button onClick={() => setAddOpen(true)}>
          <Plus className="size-4" />
          新增用户
        </Button>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>用户列表</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="py-8 text-center text-muted-foreground">
              加载中...
            </div>
          ) : (
            <DataTable
              columns={columns(currentUser?.id ?? 0)}
              data={data?.data ?? []}
              emptyMessage="暂无用户"
            />
          )}
          <Pagination
            pageNum={pageNum}
            pageSize={pageSize}
            total={data?.count ?? 0}
            onPageChange={setPageNum}
          />
        </CardContent>
      </Card>
      <AddUser
        open={addOpen}
        onOpenChange={setAddOpen}
        currentUserId={currentUser?.id ?? 0}
      />
    </div>
  )
}

export default AdminPage