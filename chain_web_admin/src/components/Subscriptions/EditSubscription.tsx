import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useEffect } from "react"
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
import {
  subscriptionDeleteSubscription,
  subscriptionUpdateSubscription,
} from "@chain/api-client"
import { unwrapResult } from "@/lib/unwrap"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"
import type { SubscriptionItem } from "@/types/domain"

const schema = z.object({
  id: z.number(),
  name: z.string().min(1).optional(),
  keywords: z.string().optional(),
  sources: z.string().optional(),
  schedule_cron: z.string().optional(),
  enabled: z.boolean().optional(),
})

type FormData = z.infer<typeof schema>

interface Props {
  subscription: SubscriptionItem
  open: boolean
  onOpenChange: (b: boolean) => void
}

function EditSubscription({ subscription, open, onOpenChange }: Props) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const form = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      id: subscription.id,
      name: subscription.name,
      keywords: (subscription.keywords ?? []).join(", "),
      sources: (subscription.sources ?? []).join(", "),
      schedule_cron: subscription.schedule_cron,
      enabled: subscription.enabled,
    },
  })

  useEffect(() => {
    form.reset({
      id: subscription.id,
      name: subscription.name,
      keywords: (subscription.keywords ?? []).join(", "),
      sources: (subscription.sources ?? []).join(", "),
      schedule_cron: subscription.schedule_cron,
      enabled: subscription.enabled,
    })
  }, [subscription, form])

  const update = useMutation({
    mutationFn: (data: FormData) => {
      const payload: Record<string, unknown> = { id: subscription.id }
      if (data.name !== undefined) payload.name = data.name
      if (data.keywords !== undefined) {
        payload.keywords = data.keywords
          .split(/[,，\s]+/)
          .map((s) => s.trim())
          .filter(Boolean)
      }
      if (data.sources !== undefined) {
        payload.sources = data.sources
          .split(/[,，\s]+/)
          .map((s) => s.trim())
          .filter(Boolean)
      }
      if (data.schedule_cron !== undefined)
        payload.schedule_cron = data.schedule_cron
      if (data.enabled !== undefined) payload.enabled = data.enabled
      return unwrapResult(subscriptionUpdateSubscription({ body: payload as any }))
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["subscriptions"] })
      showSuccessToast("更新成功")
      onOpenChange(false)
    },
    onError: handleError.bind(showErrorToast),
  })

  const remove = useMutation({
    mutationFn: () =>
      unwrapResult(
        subscriptionDeleteSubscription({ body: { id: subscription.id } }),
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["subscriptions"] })
      showSuccessToast("已删除")
      onOpenChange(false)
    },
    onError: handleError.bind(showErrorToast),
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>编辑订阅：{subscription.name}</DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form
            onSubmit={form.handleSubmit((d) => update.mutate(d))}
            className="space-y-3"
          >
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>名称</FormLabel>
                  <FormControl>
                    <Input {...field} value={field.value ?? ""} />
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
                  <FormLabel>关键词</FormLabel>
                  <FormControl>
                    <Input {...field} value={field.value ?? ""} />
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
                    <Input {...field} value={field.value ?? ""} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
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
            <DialogFooter className="!justify-between">
              <Button
                type="button"
                variant="destructive"
                onClick={() => remove.mutate()}
                disabled={remove.isPending}
              >
                删除
              </Button>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => onOpenChange(false)}
                >
                  取消
                </Button>
                <LoadingButton type="submit" loading={update.isPending}>
                  保存
                </LoadingButton>
              </div>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

export default EditSubscription