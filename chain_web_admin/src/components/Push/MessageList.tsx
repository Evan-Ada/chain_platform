import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Bell, Eye } from "lucide-react"
import { useState } from "react"

import { pushListMessages, pushMarkAsRead } from "@chain/api-client"
import { unwrapApiData } from "@/lib/unwrap"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

interface MessageItem {
  id: number
  title: string
  summary?: string
  importance?: string
  channel?: string
  status?: string
  push_date?: string
  tags?: string[]
}

interface MessageListProps {
  pageSize?: number
  showViewAll?: boolean
}

const importanceLabel: Record<string, string> = {
  high: "高",
  medium: "中",
  low: "低",
}

export function MessageList({
  pageSize = 5,
  showViewAll = false,
}: MessageListProps) {
  const [detailOpen, setDetailOpen] = useState(false)
  const [selectedMessage, setSelectedMessage] = useState<MessageItem | null>(
    null,
  )
  const queryClient = useQueryClient()
  const { showErrorToast } = useCustomToast()

  const { data, isLoading, error } = useQuery({
    queryKey: ["push-messages", pageSize],
    queryFn: () =>
      unwrapApiData<{ total: number; res: MessageItem[] }>(
        pushListMessages({
          body: { page_num: 1, page_size: pageSize },
        }),
      ),
    throwOnError: false,
    retry: false,
  })

  const messages = data?.res ?? []

  const markReadMutation = useMutation({
    mutationFn: (id: number) =>
      unwrapApiData<unknown>(
        pushMarkAsRead({ body: { id_list: [id] } }),
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["push-messages"] })
      queryClient.invalidateQueries({ queryKey: ["push-unread-count"] })
    },
    onError: handleError.bind(showErrorToast),
  })

  const handleViewDetail = (msg: MessageItem) => {
    setSelectedMessage(msg)
    setDetailOpen(true)
    if (msg.status !== "read") {
      markReadMutation.mutate(msg.id)
    }
  }

  if (isLoading) {
    return <div className="text-sm text-muted-foreground">加载中...</div>
  }

  if (error || messages.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center">
        <Bell className="mb-2 size-8 text-muted-foreground" />
        <p className="text-sm text-muted-foreground">
          {error ? "加载消息失败，请稍后重试" : "暂无推送消息"}
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {messages.map((msg) => (
        <div
          key={msg.id}
          className="flex items-start gap-3 rounded-lg border p-3 transition-colors hover:bg-muted/50"
        >
          <div className="min-w-0 flex-1">
            <div className="mb-1 flex items-center gap-2">
              <span className="truncate text-sm font-medium">{msg.title}</span>
              {msg.importance && (
                <Badge
                  variant={
                    msg.importance === "high"
                      ? "destructive"
                      : msg.importance === "medium"
                        ? "default"
                        : "secondary"
                  }
                  className="text-xs"
                >
                  {importanceLabel[msg.importance] ?? msg.importance}
                </Badge>
              )}
            </div>
            {msg.summary && (
              <p className="truncate text-xs text-muted-foreground">
                {msg.summary}
              </p>
            )}
            <div className="mt-1 flex items-center gap-2">
              {msg.channel && (
                <Badge variant="outline" className="text-xs">
                  {msg.channel}
                </Badge>
              )}
              {msg.push_date && (
                <span className="text-xs text-muted-foreground">
                  {new Date(msg.push_date).toLocaleDateString("zh-CN")}
                </span>
              )}
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="shrink-0"
            onClick={() => handleViewDetail(msg)}
          >
            <Eye className="size-4" />
          </Button>
        </div>
      ))}

      {showViewAll && (
        <Button variant="outline" className="mt-2 w-full" disabled>
          查看全部消息
        </Button>
      )}

      <Dialog open={detailOpen} onOpenChange={setDetailOpen}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>{selectedMessage?.title}</DialogTitle>
          </DialogHeader>
          {selectedMessage && (
            <div className="space-y-4">
              {selectedMessage.summary && (
                <p className="text-sm text-muted-foreground">
                  {selectedMessage.summary}
                </p>
              )}
              {selectedMessage.tags && selectedMessage.tags.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {selectedMessage.tags.map((tag) => (
                    <Badge key={tag} variant="secondary">
                      {tag}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
