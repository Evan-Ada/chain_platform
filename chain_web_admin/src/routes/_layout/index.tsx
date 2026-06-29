import { useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { Bell } from "lucide-react"

import { pushUnreadCount } from "@chain/api-client"
import { unwrapApiData } from "@/lib/unwrap"
import { MessageList } from "@/components/Push/MessageList"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import useAuth from "@/hooks/useAuth"

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
})

function Dashboard() {
  const { user: currentUser } = useAuth()

  const { data: unreadData } = useQuery({
    queryKey: ["push-unread-count"],
    queryFn: () =>
      unwrapApiData<{ unread_count: number }>(pushUnreadCount({})),
    throwOnError: false,
    retry: false,
  })

  const unreadCount = unreadData?.unread_count ?? 0

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="max-w-sm truncate text-2xl">
          你好，{currentUser?.full_name || currentUser?.username}
        </h1>
        <p className="text-muted-foreground">欢迎回来，祝你今天工作顺利。</p>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-lg">
              <Bell className="size-5" />
              推送消息
            </CardTitle>
            {unreadCount > 0 && (
              <Badge variant="destructive" className="ml-auto">
                {unreadCount} 条未读
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <MessageList pageSize={5} showViewAll />
        </CardContent>
      </Card>
    </div>
  )
}
