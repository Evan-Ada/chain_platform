import { useMutation } from "@tanstack/react-query"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { LoadingButton } from "@/components/ui/loading-button"
import { Switch } from "@/components/ui/switch"
import { subscriptionAddSubscription } from "@chain/api-client"
import { unwrapResult } from "@/lib/unwrap"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

const schema = z.object({
  name: z.string().min(1, "名称必填"),
  keywords: z.string().optional(),
  sources: z.string().optional(),
  schedule_type: z.string().optional(),
  schedule_cron: z.string().min(1, "cron 必填"),
  enabled: z.boolean().optional(),
})

type FormData = z.infer<typeof schema>

interface Props {
  open: boolean
  onOpenChange: (b: boolean) => void
  onSuccess?: () => void
}

function AddSubscription({ open, onOpenChange, onSuccess }: Props) {
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const form = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: "",
      keywords: "",
      sources: "rss",
      schedule_type: "daily",
      schedule_cron: "0 8 * * *",
      enabled: true,
    },
  })

  const mutation = useMutation({
    mutationFn: (data: FormData) => {
      const keywords = (data.keywords ?? "")
        .split(/[,，\s]+/)
        .map((s) => s.trim())
        .filter(Boolean)
      const sources = (data.sources ?? "rss")
        .split(/[,，\s]+/)
        .map((s) => s.trim())
        .filter(Boolean)
      return unwrapResult(
        subscriptionAddSubscription({
          body: {
            name: data.name,
            keywords,
            sources,
            schedule_type: data.schedule_type ?? "daily",
            schedule_cron: data.schedule_cron,
            enabled: data.enabled ?? true,
          },
        }),
      )
    },
    onSuccess: () => {
      showSuccessToast("创建成功")
      onSuccess?.()
      onOpenChange(false)
      form.reset()
    },
    onError: handleError.bind(showErrorToast),
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>新增订阅</DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form
            onSubmit={form.handleSubmit((d) => mutation.mutate(d))}
            className="space-y-3"
          >
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>名称</FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="keywords"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>关键词 (逗号分隔)</FormLabel>
                  <FormControl>
                    <Input {...field} placeholder="例: AI, 财报, 监管" />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="sources"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>来源</FormLabel>
                  <FormControl>
                    <Input {...field} placeholder="rss" />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <div className="grid grid-cols-2 gap-3">
              <FormField
                control={form.control}
                name="schedule_type"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>类型</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="schedule_cron"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>cron</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
            <FormField
              control={form.control}
              name="enabled"
              render={({ field }) => (
                <FormItem className="flex items-center justify-between rounded-md border p-3">
                  <FormLabel>启用</FormLabel>
                  <FormControl>
                    <Switch
                      checked={!!field.value}
                      onCheckedChange={field.onChange}
                    />
                  </FormControl>
                </FormItem>
              )}
            />
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
              >
                取消
              </Button>
              <LoadingButton type="submit" loading={mutation.isPending}>
                创建
              </LoadingButton>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

export default AddSubscription