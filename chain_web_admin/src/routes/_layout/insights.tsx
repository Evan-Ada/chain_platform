import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { useState } from "react"
import { Plus } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { LoadingButton } from "@/components/ui/loading-button"
import { Textarea } from "@/components/ui/textarea"
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from "@/components/ui/dialog"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { unwrapApiData } from "@/lib/unwrap"

export const Route = createFileRoute("/_layout/insights")({
  component: InsightsPage,
})

const addInsightSchema = z.object({
  raw_text: z.string().min(1, "内容不能为空"),
  tags: z.array(z.string()).optional(),
})

type AddInsightForm = z.infer<typeof addInsightSchema>

interface InsightItem {
  id: number
  raw_text: string
  status: string
  tags?: string[]
  created_at: string
  ai_interpretation?: {
    core_viewpoint?: string
    emotional_tone?: string
    actionable_suggestions?: string[]
  }
  follow_ups?: Array<{
    id: number
    raw_text: string
  }>
}

export default function InsightsPage() {
  const queryClient = useQueryClient()
  const [addOpen, setAddOpen] = useState(false)
  const [selectedTag, setSelectedTag] = useState<string | null>(null)

  const { data, isLoading, refetch } = useQuery<{ data?: { res?: InsightItem[] }; res?: InsightItem[] }>({
    queryKey: ["insights", selectedTag],
    queryFn: () =>
      unwrapApiData(
        fetch("/api/v1/Insight/list", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ tag: selectedTag, page_num: 1, page_size: 50 }),
        }).then(r => r.json())
      ),
  })

  const addMutation = useMutation({
    mutationFn: (data: AddInsightForm) => {
      return fetch("/api/v1/Insight/add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      }).then(r => r.json())
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["insights"] })
      setAddOpen(false)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) =>
      fetch("/api/v1/Insight/delete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id }),
      }).then(r => r.json()),
    onSuccess: () => refetch(),
  })

  const form = useForm<AddInsightForm>({
    resolver: zodResolver(addInsightSchema),
    defaultValues: { raw_text: "", tags: [] },
  })

  const insights = data?.data?.res ?? data?.res ?? []

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">我的洞见</h1>
        <Button onClick={() => setAddOpen(true)}>
          <Plus className="size-4" />
          录入洞见
        </Button>
      </div>

      <div className="flex gap-2 flex-wrap">
        <Badge
          variant={selectedTag === null ? "default" : "outline"}
          className="cursor-pointer"
          onClick={() => setSelectedTag(null)}
        >
          全部
        </Badge>
      </div>

      <div className="space-y-4">
        {isLoading ? (
          <div className="py-8 text-center text-muted-foreground">加载中...</div>
        ) : insights.length === 0 ? (
          <div className="py-8 text-center text-muted-foreground">暂无洞见</div>
        ) : (
          insights.map((insight: InsightItem) => (
            <InsightCard
              key={insight.id}
              insight={insight}
              onDelete={() => deleteMutation.mutate(insight.id)}
              onRefresh={refetch}
            />
          ))
        )}
      </div>

      <Dialog open={addOpen} onOpenChange={setAddOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>录入洞见</DialogTitle>
          </DialogHeader>
          <form onSubmit={form.handleSubmit((data) => addMutation.mutate(data))}>
            <div className="space-y-4 py-4">
              <div>
                <label className="text-sm font-medium">想法 / 灵感 / 反思</label>
                <Textarea
                  {...form.register("raw_text")}
                  placeholder="写下你的想法..."
                  className="min-h-[150px]"
                />
                {form.formState.errors.raw_text && (
                  <p className="text-red-500 text-sm">{String(form.formState.errors.raw_text.message)}</p>
                )}
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" type="button" onClick={() => setAddOpen(false)}>
                取消
              </Button>
              <LoadingButton type="submit" loading={addMutation.isPending}>
                提交
              </LoadingButton>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}

function InsightCard({ insight, onDelete, onRefresh }: {
  insight: InsightItem
  onDelete: () => void
  onRefresh: () => void
}) {
  const [expanded, setExpanded] = useState(false)
  const [followUpOpen, setFollowUpOpen] = useState(false)
  const [followUpText, setFollowUpText] = useState("")
  const [followUpLoading, setFollowUpLoading] = useState(false)

  const interpretation = insight.ai_interpretation || {}

  const handleFollowUp = async () => {
    setFollowUpLoading(true)
    try {
      await fetch("/api/v1/Insight/followUp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ parent_id: insight.id, raw_text: followUpText }),
      })
      setFollowUpOpen(false)
      setFollowUpText("")
      onRefresh()
    } finally {
      setFollowUpLoading(false)
    }
  }

  return (
    <Card>
      <CardContent className="pt-6">
        <div className="space-y-3">
          <div className="text-sm">
            {expanded ? insight.raw_text : insight.raw_text.slice(0, 200)}
            {insight.raw_text.length > 200 && (
              <button
                className="text-muted-foreground underline ml-1"
                onClick={() => setExpanded(!expanded)}
              >
                {expanded ? "收起" : "展开"}
              </button>
            )}
          </div>

          <div className="flex items-center gap-2">
            <Badge variant={insight.status === "done" ? "default" : "secondary"}>
              {insight.status === "done" ? "已解读" : insight.status === "pending" ? "解读中..." : "失败"}
            </Badge>
            {insight.tags?.map((tag: string) => (
              <Badge key={tag} variant="outline">{tag}</Badge>
            ))}
            <span className="text-muted-foreground text-xs ml-auto">
              {insight.created_at}
            </span>
          </div>

          {insight.status === "done" && interpretation && (
            <div className="bg-muted/50 rounded-lg p-3 space-y-2 text-sm">
              {interpretation.core_viewpoint && (
                <div>
                  <span className="font-medium">核心观点：</span>
                  {interpretation.core_viewpoint}
                </div>
              )}
              {interpretation.emotional_tone && (
                <div>
                  <span className="font-medium">情绪：</span>
                  {interpretation.emotional_tone}
                </div>
              )}
              {(interpretation.actionable_suggestions?.length ?? 0) > 0 && (
                <div>
                  <span className="font-medium">建议：</span>
                  <ul className="list-disc list-inside">
                    {interpretation.actionable_suggestions!.map((s: string, i: number) => (
                      <li key={i}>{s}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {(insight.follow_ups?.length ?? 0) > 0 && (
            <div className="ml-4 border-l-2 pl-4 space-y-2">
              {insight.follow_ups!.map((fu) => (
                <div key={fu.id} className="text-sm text-muted-foreground">
                  <span className="font-medium text-foreground">追问：</span>
                  {fu.raw_text}
                </div>
              ))}
            </div>
          )}

          <div className="flex gap-2">
            <Button size="sm" variant="outline" onClick={() => setFollowUpOpen(true)}>
              追问
            </Button>
            <Button size="sm" variant="destructive" onClick={onDelete}>
              删除
            </Button>
          </div>

          {followUpOpen && (
            <div className="border-t pt-3 mt-3">
              <Textarea
                value={followUpText}
                onChange={(e) => setFollowUpText(e.target.value)}
                placeholder="输入你的追问..."
                className="min-h-[80px] mb-2"
              />
              <div className="flex gap-2">
                <Button size="sm" onClick={handleFollowUp} disabled={followUpLoading}>
                  {followUpLoading ? "提交中..." : "提交追问"}
                </Button>
                <Button size="sm" variant="outline" onClick={() => setFollowUpOpen(false)}>
                  取消
                </Button>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
