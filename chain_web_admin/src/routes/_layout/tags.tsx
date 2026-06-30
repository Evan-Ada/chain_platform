import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { useState } from "react"
import { Plus } from "lucide-react"
import { unwrapApiData } from "@/lib/unwrap"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from "@/components/ui/dialog"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { LoadingButton } from "@/components/ui/loading-button"
import { tagTagStats } from "@chain/api-client"
import { apiFetch } from "@/lib/apiClient"

export const Route = createFileRoute("/_layout/tags")({
  component: TagsPage,
})

const addTagSchema = z.object({
  name: z.string().min(1, "名称必填"),
  display_name: z.string().min(1, "展示名必填"),
  category: z.string().optional(),
  parent_id: z.number().optional().nullable(),
})

type AddTagForm = z.infer<typeof addTagSchema>

interface TagItem {
  id: number
  name: string
  display_name: string
  category?: string
  parent_id?: number
  usage_count: number
}

export default function TagsPage() {
  const queryClient = useQueryClient()
  const [addOpen, setAddOpen] = useState(false)
  const [parentId, setParentId] = useState<number | null>(null)

  const { data: statsData, isLoading } = useQuery<TagItem[]>({
    queryKey: ["tag-stats"],
    queryFn: () => unwrapApiData<TagItem[]>(tagTagStats({})),
  })

  const addMutation = useMutation({
    mutationFn: async (data: AddTagForm) => {
      return apiFetch("/api/v1/Tag/add", {
        method: "POST",
        body: JSON.stringify({
          name: data.name,
          display_name: data.display_name,
          category: data.category || "topic",
          parent_id: parentId,
        }),
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tag-stats"] })
      setAddOpen(false)
    },
  })

  const form = useForm<AddTagForm>({
    resolver: zodResolver(addTagSchema),
    defaultValues: { name: "", display_name: "", category: "topic", parent_id: null },
  })

  const rootTags = statsData?.filter((t: TagItem) => !t.parent_id) ?? []
  const tagsByParent = (pid: number | null) =>
    statsData?.filter((t: TagItem) => t.parent_id === pid) ?? []

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">标签管理</h1>
        <Button onClick={() => setAddOpen(true)}>
          <Plus className="size-4" />
          新增标签
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>标签列表</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="py-8 text-center text-muted-foreground">加载中...</div>
          ) : rootTags.length === 0 ? (
            <div className="py-8 text-center text-muted-foreground">暂无标签</div>
          ) : (
            <div className="space-y-4">
              {rootTags.map((tag: TagItem) => (
                <div key={tag.id} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline">{tag.category || "topic"}</Badge>
                      <span className="font-medium">{tag.display_name}</span>
                      <span className="text-muted-foreground text-sm">({tag.name})</span>
                      <span className="text-muted-foreground text-sm">使用 {tag.usage_count} 次</span>
                    </div>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        setParentId(tag.id)
                        setAddOpen(true)
                      }}
                    >
                      添加子标签
                    </Button>
                  </div>
                  {tagsByParent(tag.id).length > 0 && (
                    <div className="mt-2 ml-6 flex flex-wrap gap-2">
                      {tagsByParent(tag.id).map((child: TagItem) => (
                        <Badge key={child.id} variant="secondary">
                          {child.display_name} ({child.usage_count})
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog open={addOpen} onOpenChange={(open) => { setAddOpen(open); if (!open) setParentId(null) }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{parentId ? "添加子标签" : "新增一级标签"}</DialogTitle>
          </DialogHeader>
          <form onSubmit={form.handleSubmit((data) => addMutation.mutate({ ...data, parent_id: parentId }))}>
            <div className="space-y-4 py-4">
              <div>
                <label className="text-sm font-medium">标签名（英文）</label>
                <Input {...form.register("name")} placeholder="如: llm" />
                {form.formState.errors.name && (
                  <p className="text-red-500 text-sm">{String(form.formState.errors.name.message)}</p>
                )}
              </div>
              <div>
                <label className="text-sm font-medium">展示名（中文）</label>
                <Input {...form.register("display_name")} placeholder="如: 大语言模型" />
                {form.formState.errors.display_name && (
                  <p className="text-red-500 text-sm">{String(form.formState.errors.display_name.message)}</p>
                )}
              </div>
              <div>
                <label className="text-sm font-medium">分类</label>
                <Input {...form.register("category")} placeholder="如: topic" />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" type="button" onClick={() => setAddOpen(false)}>
                取消
              </Button>
              <LoadingButton type="submit" loading={addMutation.isPending}>
                确认
              </LoadingButton>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
